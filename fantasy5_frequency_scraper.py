import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from sqlalchemy import select, delete

from app.database import SessionLocal
from app.models import Game, FrequencyStat

URL = "https://loteria.guru/resultados-loteria-estados-unidos/us-fantasy-5-1"


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


def parse_frequency_blocks(html: str):
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text("\n", strip=True)
    lines = [clean_text(x) for x in text.splitlines() if clean_text(x)]

    most = []
    least = []

    mode = None
    i = 0
    while i < len(lines):
        line = lines[i]

        if "NÚMEROS MÁS HABITUALES DE FANTASY 5" in line.upper():
            mode = "most"
            i += 1
            continue

        if "NÚMEROS MENOS HABITUALES DE FANTASY 5" in line.upper():
            mode = "least"
            i += 1
            continue

        # Paramos si llega al texto final
        if "Estas estadísticas tienen en cuenta" in line:
            break

        if mode in ("most", "least"):
            # Esperamos grupos del estilo:
            # 33
            # Extraído 260 veces
            # Hace 6 días
            # 13 mar 2026
            if re.fullmatch(r"\d{1,2}", line):
                number = line

                count = None
                last_seen_date = None

                if i + 1 < len(lines):
                    m_count = re.search(r"Extraído\s+(\d+)\s+veces", lines[i + 1], re.IGNORECASE)
                    if m_count:
                        count = int(m_count.group(1))

                if i + 3 < len(lines):
                    raw_date = lines[i + 3]
                    if re.fullmatch(r"\d{1,2}\s+\w+\s+\d{4}", raw_date):
                        last_seen_date = parse_spanish_date(raw_date)

                if count is not None:
                    item = {
                        "number": number,
                        "count": count,
                        "last_seen_date": last_seen_date,
                    }
                    if mode == "most":
                        most.append(item)
                    else:
                        least.append(item)

        i += 1

    return most, least


def save_frequency_stats(most, least):
    db = SessionLocal()
    try:
        game = db.execute(
            select(Game).where(Game.slug == "fantasy-5")
        ).scalar_one_or_none()

        if not game:
            raise ValueError("No existe el juego fantasy-5 en la tabla games")

        # Borramos stats viejos de fantasy-5
        db.execute(
            delete(FrequencyStat).where(FrequencyStat.game_id == game.id)
        )
        db.commit()

        for item in most:
            db.add(FrequencyStat(
                game_id=game.id,
                stat_type="most",
                number=str(item["number"]),
                count=item["count"],
                last_seen_date=item["last_seen_date"],
            ))

        for item in least:
            db.add(FrequencyStat(
                game_id=game.id,
                stat_type="least",
                number=str(item["number"]),
                count=item["count"],
                last_seen_date=item["last_seen_date"],
            ))

        db.commit()
        print(f"Guardados {len(most)} hot numbers y {len(least)} cold numbers.")
    finally:
        db.close()


def main():
    resp = requests.get(
        URL,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    resp.raise_for_status()

    most, least = parse_frequency_blocks(resp.text)

    print("MOST:", most)
    print("LEAST:", least)

    save_frequency_stats(most, least)


if __name__ == "__main__":
    main()