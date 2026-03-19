from sqlalchemy import text
from app.database import SessionLocal

db = SessionLocal()
try:
    result = db.execute(text("""
        DELETE FROM draws
        WHERE game_id = (SELECT id FROM games WHERE slug = 'powerball' LIMIT 1)
          AND draw_date = '2026-03-21'
    """))
    db.commit()
    print("Rows deleted:", result.rowcount)
finally:
    db.close()