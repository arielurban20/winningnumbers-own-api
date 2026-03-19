from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session

from app import models


def get_states(db: Session):
    stmt = select(models.State).order_by(models.State.name.asc())
    return db.execute(stmt).scalars().all()


def get_games(db: Session, state_code: str | None = None):
    stmt = select(models.Game)

    if state_code:
        stmt = stmt.join(models.State).where(models.State.code == state_code.upper())

    stmt = stmt.order_by(models.Game.name.asc())
    return db.execute(stmt).scalars().all()


def get_latest_result(db: Session, state_code: str, game_slug: str):
    stmt = (
        select(models.Draw)
        .join(models.Game)
        .join(models.State, isouter=True)
        .where(models.Game.slug == game_slug)
    )

    if state_code.upper() != "MULTI":
        stmt = stmt.where(models.State.code == state_code.upper())

    stmt = stmt.order_by(desc(models.Draw.draw_date), desc(models.Draw.id))
    return db.execute(stmt).scalars().first()


def get_past_draws(db: Session, state_code: str, game_slug: str, limit: int = 20):
    stmt = (
        select(models.Draw)
        .join(models.Game)
        .join(models.State, isouter=True)
        .where(models.Game.slug == game_slug)
    )

    if state_code.upper() != "MULTI":
        stmt = stmt.where(models.State.code == state_code.upper())

    stmt = stmt.order_by(desc(models.Draw.draw_date), desc(models.Draw.id)).limit(limit)
    return db.execute(stmt).scalars().all()


def get_frequency_stats(db: Session, state_code: str, game_slug: str, stat_type: str, limit: int = 5):
    stmt = (
        select(models.FrequencyStat)
        .join(models.Game)
        .join(models.State, isouter=True)
        .where(
            models.Game.slug == game_slug,
            models.FrequencyStat.stat_type == stat_type,
        )
    )

    if state_code.upper() != "MULTI":
        stmt = stmt.where(models.State.code == state_code.upper())

    if stat_type == "most":
        stmt = stmt.order_by(desc(models.FrequencyStat.count), models.FrequencyStat.number.asc())
    else:
        stmt = stmt.order_by(models.FrequencyStat.count.asc(), models.FrequencyStat.number.asc())

    stmt = stmt.limit(limit)
    return db.execute(stmt).scalars().all()


def get_latest_results_grouped(db: Session, state_code: str, game_slug: str):
    stmt = (
        select(models.Draw)
        .join(models.Game)
        .join(models.State, isouter=True)
        .where(models.Game.slug == game_slug)
    )

    if state_code.upper() != "MULTI":
        stmt = stmt.where(models.State.code == state_code.upper())

    stmt = stmt.order_by(desc(models.Draw.draw_date), desc(models.Draw.id))
    draws = db.execute(stmt).scalars().all()

    if not draws:
        return None

    latest_date = draws[0].draw_date
    same_day_draws = [d for d in draws if d.draw_date == latest_date]
    same_day_draws.sort(key=lambda x: (x.draw_type or ""))

    return {
        "draw_date": latest_date,
        "draws": same_day_draws,
    }


def get_game_config(db: Session, state_code: str, game_slug: str):
    stmt = (
        select(models.Game, models.State)
        .join(models.State, isouter=True)
        .where(models.Game.slug == game_slug)
    )

    if state_code.upper() != "MULTI":
        stmt = stmt.where(models.State.code == state_code.upper())

    row = db.execute(stmt).first()

    if not row:
        return None

    game, state = row

    supports_frequency_stats = bool(game.source_stats_url)
    supports_grouped_latest = bool(game.has_multiple_daily_draws)

    return {
        "id": game.id,
        "name": game.name,
        "slug": game.slug,
        "state_code": state.code if state else None,
        "game_type": game.game_type,
        "is_multi_state": game.is_multi_state,
        "has_multiple_daily_draws": game.has_multiple_daily_draws,
        "supports_grouped_latest": supports_grouped_latest,
        "supports_frequency_stats": supports_frequency_stats,
        "has_bonus_ball": game.has_bonus_ball,
        "has_multiplier": game.has_multiplier,
        "draw_timezone": game.draw_timezone,
        "draw_time": game.draw_time,
    }


def get_system_summary(db: Session):
    states_count = db.execute(
        select(func.count()).select_from(models.State)
    ).scalar_one()

    games_count = db.execute(
        select(func.count()).select_from(models.Game)
    ).scalar_one()

    draws_count = db.execute(
        select(func.count()).select_from(models.Draw)
    ).scalar_one()

    frequency_stats_count = db.execute(
        select(func.count()).select_from(models.FrequencyStat)
    ).scalar_one()

    grouped_games_count = db.execute(
        select(func.count()).select_from(models.Game).where(models.Game.has_multiple_daily_draws == True)
    ).scalar_one()

    stats_supported_games_count = db.execute(
        select(func.count()).select_from(models.Game).where(models.Game.source_stats_url.is_not(None))
    ).scalar_one()

    return {
        "ok": True,
        "states_count": states_count,
        "games_count": games_count,
        "draws_count": draws_count,
        "frequency_stats_count": frequency_stats_count,
        "grouped_games_count": grouped_games_count,
        "stats_supported_games_count": stats_supported_games_count,
    }