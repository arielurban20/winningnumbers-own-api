import json
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Game, Draw

GAME_SLUG = "fantasy-5"


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


def find_latest_result_container(soup: BeautifulSoup):
    for tag in soup.find_all(["div", "section", "article"]):
        txt = clean_text(tag.get_text(" ", strip=True))
        if "Último resultado" in txt:
            return tag
    return None


def extract_date(block_text: str):
    m = re.search(
        r"(Lunes|Martes|Miércoles|Jueves|Viernes|Sábado|Domingo)\s+(\d{1,2}\s+\w+\s+\d{4})",
        block_text
    )
    if not m:
        return None
    return parse_spanish_date(m.group(2))


def extract_numbers_from_latest_block(block):
    nums = []
    for el in block.find_all(["span", "div", "li", "p"]):
        txt = clean_text(el.get_text(" ", strip=True))
        if re.fullmatch(r"\d{1,2}", txt):
            n = int(txt)
            if 1 <= n <= 39:
                nums.append(n)

    return nums[:5]


def extract_jackpot_from_latest_block(block_text: str):
    money = re.findall(r"\d[\d\.\,]*\$", block_text)
    if not money:
        return None
    return money[-1]


def parse_fantasy5_page(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")

    latest_block = find_latest_result_container(soup)
    if not latest_block:
        raise ValueError("No se encontró el bloque de 'Último resultado'")

    block_text = latest_block.get_text("\n", strip=True)
    block_text_clean = clean_text(block_text)

    draw_date = extract_date(block_text)
    main_numbers = extract_numbers_from_latest_block(latest_block)
    jackpot = extract_jackpot_from_latest_block(block_text_clean)

    if not draw_date:
        raise ValueError("No se pudo extraer la fecha correcta de Fantasy 5")

    if len(main_numbers) != 5:
        raise ValueError(f"No se pudieron extraer correctamente los 5 números. Detectados: {main_numbers}")

    return {
        "draw_date": draw_date,
        "draw_type": "main",
        "draw_time": None,
        "main_numbers": main_numbers,
        "bonus_number": None,
        "multiplier": None,
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

    data = parse_fantasy5_page(resp.text)

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