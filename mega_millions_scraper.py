import json
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Game, Draw

GAME_SLUG = "mega-millions"


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def parse_spanish_date(raw_date: str):
    month_map = {
        "ene": "Jan", "feb": "Feb", "mar": "Mar", "abr": "Apr", "may": "May", "jun": "Jun",
        "jul": "Jul", "ago": "Aug", "sep": "Sep", "oct": "Oct", "nov": "Nov", "dic": "Dec"
    }
    parts = raw_date.split()
    if len(parts) != 3:
        return None
    day, mon, year = parts
    mon_en = month_map.get(mon.lower()[:3], mon)
    return datetime.strptime(f"{day} {mon_en} {year}", "%d %b %Y").date()


def parse_mega_millions_page(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    full_text = soup.get_text("\n", strip=True)
    full_text_clean = clean_text(full_text)

    date_match = re.search(
        r"(Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo)\s+(\d{1,2}\s+\w+\s+\d{4})",
        full_text
    )
    draw_date = None
    if date_match:
        draw_date = parse_spanish_date(date_match.group(2))

    money_matches = re.findall(r"\d[\d\.\,]*\$", full_text_clean)
    jackpot = money_matches[0] if money_matches else None

    raw_numbers = re.findall(r"\b\d{1,2}\b", full_text_clean)
    filtered = [n for n in raw_numbers if 0 <= int(n) <= 99]

    main_numbers = []
    bonus_number = None

    if len(filtered) >= 6:
        main_numbers = filtered[:5]
        bonus_number = filtered[5]

    megaplier = None
    mega_match = re.search(
        r"(Megaplier|Megaplifier|Mega Plier|Megaplay|Megaplier)[:\s]+(\d+)",
        full_text_clean,
        re.IGNORECASE
    )
    if mega_match:
        megaplier = mega_match.group(2)

    if not draw_date or len(main_numbers) < 5:
        raise ValueError("No se pudo extraer correctamente el resultado de Mega Millions")

    return {
        "draw_date": draw_date,
        "draw_type": "main",
        "draw_time": "23:00:00",
        "main_numbers": [int(x) for x in main_numbers],
        "bonus_number": str(bonus_number) if bonus_number else None,
        "multiplier": str(megaplier) if megaplier else None,
        "jackpot": jackpot,
        "cash_payout": None,
        "secondary_draws": None,
        "notes": "Scraped from loteria.guru",
    }


def get_game_and_url():
    db = SessionLocal()
    try:
        game = db.execute(
            select(Game).where(Game.slug == GAME_SLUG)
        ).scalar_one_or_none()

        if not game:
            raise ValueError(f"No existe el juego {GAME_SLUG} en la tabla games")

        if not game.source_result_url:
            raise ValueError(f"El juego {GAME_SLUG} no tiene source_result_url")

        return game.id, game.source_result_url
    finally:
        db.close()


def save_draw(game_id: int, source_url: str, data: dict):
    db = SessionLocal()
    try:
        existing = db.execute(
            select(Draw).where(
                Draw.game_id == game_id,
                Draw.draw_date == data["draw_date"],
                Draw.draw_type == data["draw_type"],
            )
        ).scalar_one_or_none()

        if existing:
            print("Ese draw ya existe. No se insertó duplicado.")
            return

        draw = Draw(
            game_id=game_id,
            draw_date=data["draw_date"],
            draw_type=data["draw_type"],
            draw_time=data["draw_time"],
            main_numbers=data["main_numbers"],
            bonus_number=data["bonus_number"],
            multiplier=data["multiplier"],
            jackpot=data["jackpot"],
            cash_payout=data["cash_payout"],
            secondary_draws=data["secondary_draws"],
            notes=data["notes"],
            source_url=source_url,
        )
        db.add(draw)
        db.commit()
        print("Draw guardado correctamente.")
    finally:
        db.close()


def main():
    game_id, url = get_game_and_url()

    resp = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    resp.raise_for_status()

    data = parse_mega_millions_page(resp.text)

    print("RESULTADO EXTRAÍDO:")
    print(json.dumps(
        {**data, "draw_date": data["draw_date"].isoformat()},
        ensure_ascii=False,
        indent=2,
        default=str
    ))

    save_draw(game_id, url, data)


if __name__ == "__main__":
    main()