import json
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from sqlalchemy import select

from app.database import SessionLocal
from app.models import Game, Draw

GAME_SLUG = "pick-4-oh"


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


def find_latest_result_block(soup: BeautifulSoup):
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


def extract_pick4_draws(block):
    """
    Busca formatos tipo:
    MIDDAY 5 0 0 1
    EVENING 2 4 2 5
    """
    text = block.get_text("\n", strip=True)
    lines = [clean_text(x) for x in text.splitlines() if clean_text(x)]

    results = []

    i = 0
    while i < len(lines):
        line = lines[i].upper()

        if line in ("MIDDAY", "EVENING", "NIGHT", "MORNING"):
            draw_type = line.lower()

            # buscamos los siguientes 4 números válidos
            nums = []
            j = i + 1
            while j < len(lines) and len(nums) < 4:
                if re.fullmatch(r"\d{1,2}", lines[j]):
                    nums.append(int(lines[j]))
                j += 1

            if len(nums) == 4:
                results.append({
                    "draw_type": draw_type,
                    "main_numbers": nums,
                })

            i = j
            continue

        i += 1

    return results


def extract_jackpot(block_text: str):
    money = re.findall(r"\d[\d\.\,]*\$", block_text)
    return money[-1] if money else None


def parse_pick4_page(html: str):
    soup = BeautifulSoup(html, "lxml")

    latest_block = find_latest_result_block(soup)
    if not latest_block:
        raise ValueError("No se encontró el bloque de 'Último resultado'")

    block_text = latest_block.get_text("\n", strip=True)
    block_text_clean = clean_text(block_text)

    draw_date = extract_date(block_text)
    extracted_draws = extract_pick4_draws(latest_block)
    jackpot = extract_jackpot(block_text_clean)

    if not draw_date:
        raise ValueError("No se pudo extraer la fecha de Pick 4 OH")

    if not extracted_draws:
        raise ValueError("No se pudieron extraer draws de Pick 4 OH")

    parsed = []
    for d in extracted_draws:
        parsed.append({
            "draw_date": draw_date,
            "draw_type": d["draw_type"],
            "draw_time": None,
            "main_numbers": d["main_numbers"],
            "bonus_number": None,
            "multiplier": None,
            "jackpot": jackpot,
            "cash_payout": None,
            "secondary_draws": None,
            "notes": "Scraped from loteria.guru",
        })

    return parsed


def save_draws(game_id: int, source_url: str, draws_data: list[dict]):
    db = SessionLocal()
    try:
        inserted = 0

        for data in draws_data:
            existing = db.execute(
                select(Draw).where(
                    Draw.game_id == game_id,
                    Draw.draw_date == data["draw_date"],
                    Draw.draw_type == data["draw_type"],
                )
            ).scalar_one_or_none()

            if existing:
                print(f"Ya existe: {data['draw_type']} {data['draw_date']}")
                continue

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
            inserted += 1

        db.commit()
        print(f"Insertados {inserted} draws nuevos.")
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

    draws_data = parse_pick4_page(resp.text)

    print("DRAWS EXTRAÍDOS:")
    print(json.dumps(
        [
            {**d, "draw_date": d["draw_date"].isoformat()}
            for d in draws_data
        ],
        ensure_ascii=False,
        indent=2,
        default=str
    ))

    save_draws(game_id, url, draws_data)


if __name__ == "__main__":
    main()