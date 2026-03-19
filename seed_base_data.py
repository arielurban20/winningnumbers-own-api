from sqlalchemy import select

from app.database import SessionLocal
from app.models import State, Game


def seed_states_and_games():
    db = SessionLocal()
    try:
        states_data = [
            {"name": "Ohio", "code": "OH", "slug": "ohio"},
            {"name": "California", "code": "CA", "slug": "california"},
            {"name": "Texas", "code": "TX", "slug": "texas"},
            {"name": "New York", "code": "NY", "slug": "new-york"},
        ]

        for item in states_data:
            existing = db.execute(
                select(State).where(State.code == item["code"])
            ).scalar_one_or_none()

            if not existing:
                db.add(State(**item))

        db.commit()

        state_map = {
            s.code: s.id for s in db.execute(select(State)).scalars().all()
        }

        games_data = [
            {
                "state_id": None,
                "name": "Powerball",
                "slug": "powerball",
                "logo_url": None,
                "game_type": "multi-state",
                "is_multi_state": True,
                "draw_timezone": "America/New_York",
                "draw_time": "22:59:00",
                "has_bonus_ball": True,
                "has_multiplier": True,
                "has_secondary_draws": True,
                "has_multiple_daily_draws": False,
                "main_ball_count": 5,
                "main_ball_min": 1,
                "main_ball_max": 69,
                "bonus_ball_min": 1,
                "bonus_ball_max": 26,
                "source_result_url": "https://loteria.guru/resultados-loteria-estados-unidos/us-powerball/ohio",
                "source_stats_url": None,
                "stats_period_default": None,
            },
            {
                "state_id": None,
                "name": "Mega Millions",
                "slug": "mega-millions",
                "logo_url": None,
                "game_type": "multi-state",
                "is_multi_state": True,
                "draw_timezone": "America/New_York",
                "draw_time": "23:00:00",
                "has_bonus_ball": True,
                "has_multiplier": True,
                "has_secondary_draws": False,
                "has_multiple_daily_draws": False,
                "main_ball_count": 5,
                "main_ball_min": 1,
                "main_ball_max": 70,
                "bonus_ball_min": 1,
                "bonus_ball_max": 25,
                "source_result_url": "https://loteria.guru/resultados-loteria-estados-unidos/us-mega-millions/california",
                "source_stats_url": None,
                "stats_period_default": None,
            },
            {
                "state_id": state_map["OH"],
                "name": "Pick 4 OH",
                "slug": "pick-4-oh",
                "logo_url": None,
                "game_type": "state-specific",
                "is_multi_state": False,
                "draw_timezone": "America/New_York",
                "draw_time": None,
                "has_bonus_ball": False,
                "has_multiplier": False,
                "has_secondary_draws": False,
                "has_multiple_daily_draws": True,
                "main_ball_count": 4,
                "main_ball_min": 0,
                "main_ball_max": 9,
                "bonus_ball_min": None,
                "bonus_ball_max": None,
                "source_result_url": "https://loteria.guru/resultados-loteria-estados-unidos/us-pick-4-oh",
                "source_stats_url": None,
                "stats_period_default": None,
            },
            {
                "state_id": state_map["CA"],
                "name": "Fantasy 5",
                "slug": "fantasy-5",
                "logo_url": None,
                "game_type": "state-specific",
                "is_multi_state": False,
                "draw_timezone": "America/Los_Angeles",
                "draw_time": None,
                "has_bonus_ball": False,
                "has_multiplier": False,
                "has_secondary_draws": False,
                "has_multiple_daily_draws": False,
                "main_ball_count": 5,
                "main_ball_min": 1,
                "main_ball_max": 39,
                "bonus_ball_min": None,
                "bonus_ball_max": None,
                "source_result_url": "https://loteria.guru/resultados-loteria-estados-unidos/us-fantasy-5-1",
                "source_stats_url": "https://loteria.guru/resultados-loteria-estados-unidos/us-fantasy-5-1/us-fantasy-5-estadisticas-2?periodType=YEAR",
                "stats_period_default": "YEAR",
            },
            {
                "state_id": state_map["NY"],
                "name": "NY Lotto",
                "slug": "ny-lotto",
                "logo_url": None,
                "game_type": "state-specific",
                "is_multi_state": False,
                "draw_timezone": "America/New_York",
                "draw_time": None,
                "has_bonus_ball": False,
                "has_multiplier": False,
                "has_secondary_draws": False,
                "has_multiple_daily_draws": False,
                "main_ball_count": 6,
                "main_ball_min": 1,
                "main_ball_max": 59,
                "bonus_ball_min": None,
                "bonus_ball_max": None,
                "source_result_url": "https://loteria.guru/resultados-loteria-estados-unidos/us-ny-lotto",
                "source_stats_url": "https://loteria.guru/resultados-loteria-estados-unidos/us-ny-lotto/us-ny-lotto-estadisticas?periodType=MONTH",
                "stats_period_default": "MONTH",
            },
        ]

        for item in games_data:
            existing = db.execute(
                select(Game).where(Game.slug == item["slug"])
            ).scalar_one_or_none()

            if not existing:
                db.add(Game(**item))

        db.commit()
        print("Seed completado correctamente.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_states_and_games()