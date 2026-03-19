import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from sqlalchemy import select, delete

from app.database import SessionLocal
from app.models import Game, FrequencyStat

GAME_SLUG = "ny-lotto"


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

        if not game.source_stats_url:
            raise ValueError(f"El juego {GAME_SLUG} no tiene source_stats_url")

        return game.id, game.source_stats_url
    finally:
        db.close()


def get_lines(html: str):
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text("\n", strip=True)
    return [clean_text(x) for x in text.splitlines() if clean_text(x)]


def extract_block(lines, start_title, stop_title):
    collecting = False
    block = []

    for line in lines:
        if start_title.lower() in line.lower():
            collecting = True
            continue

        if collecting and stop_title.lower() in line.lower():
            break

        if collecting:
            block.append(line)

    return block


def parse_strict_table(block_lines):
    rows = []
    i = 0

    while i < len(block_lines):
        current = block_lines[i].lower()

        if current in [
            "números",
            "frecuencia",
            "último sorteo",
            "ultima aparición (días)",
            "última aparición (días)"
        ]:
            i += 1
            continue

        if (
            i + 3 < len(block_lines)
            and re.fullmatch(r"\d{1,2}", block_lines[i])
            and re.fullmatch(r"\d+", block_lines[i + 1])
            and re.fullmatch(r"\d{1,2}\s+\w+\s+\d{4}", block_lines[i + 2])
            and re.fullmatch(r"\d+", block_lines[i + 3])
        ):
            rows.append({
                "number": block_lines[i],
                "count": int(block_lines[i + 1]),
                "last_seen_date": parse_spanish_date(block_lines[i + 2]),
            })
            i += 4
            continue

        i += 1

    return rows


def parse_stats_page(html: str):
    lines = get_lines(html)

    most_block = extract_block(
        lines,
        "Números más habituales",
        "Números menos habituales"
    )

    least_block = extract_block(
        lines,
        "Números menos habituales",
        "Parejas más habituales"
    )

    most = parse_strict_table(most_block)[:5]
    least = parse_strict_table(least_block)[:5]

    return most, least


def save_frequency_stats(game_id, most, least):
    db = SessionLocal()
    try:
        db.execute(
            delete(FrequencyStat).where(
                FrequencyStat.game_id == game_id,
                FrequencyStat.stat_type.in_(["most", "least"])
            )
        )
        db.commit()

        for row in most:
            db.add(FrequencyStat(
                game_id=game_id,
                stat_type="most",
                number=str(row["number"]),
                count=row["count"],
                last_seen_date=row["last_seen_date"],
            ))

        for row in least:
            db.add(FrequencyStat(
                game_id=game_id,
                stat_type="least",
                number=str(row["number"]),
                count=row["count"],
                last_seen_date=row["last_seen_date"],
            ))

        db.commit()
        print(f"Guardados {len(most)} most y {len(least)} least.")
        print("MOST:", most)
        print("LEAST:", least)
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

    most, least = parse_stats_page(resp.text)
    save_frequency_stats(game_id, most, least)


if __name__ == "__main__":
    main()