from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app import crud, schemas

Base.metadata.create_all(bind=engine)

app = FastAPI(title="WinningNumbers Own API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "ok": True,
        "service": "winningnumbers-own-api",
        "version": "v1"
    }


@app.get("/api/system-summary", response_model=schemas.SystemSummaryOut)
def api_system_summary(db: Session = Depends(get_db)):
    return crud.get_system_summary(db)


@app.get("/api/states", response_model=list[schemas.StateOut])
def api_states(db: Session = Depends(get_db)):
    return crud.get_states(db)


@app.get("/api/games", response_model=list[schemas.GameOut])
def api_games(
    state: str | None = Query(None, description="State code, e.g. OH"),
    db: Session = Depends(get_db),
):
    return crud.get_games(db, state)


@app.get("/api/game-config", response_model=schemas.GameConfigOut)
def api_game_config(
    state: str = Query(..., description="State code, e.g. OH or MULTI"),
    slug: str = Query(..., description="Game slug, e.g. pick-4-oh"),
    db: Session = Depends(get_db),
):
    result = crud.get_game_config(db, state, slug)
    if not result:
        raise HTTPException(status_code=404, detail="Game config not found")
    return result


@app.get("/api/latest-results", response_model=schemas.DrawOut)
def api_latest_results(
    state: str = Query(..., description="State code, e.g. OH or MULTI"),
    slug: str = Query(..., description="Game slug, e.g. powerball"),
    db: Session = Depends(get_db),
):
    result = crud.get_latest_result(db, state, slug)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


@app.get("/api/latest-results-grouped", response_model=schemas.LatestResultsGroupedOut)
def api_latest_results_grouped(
    state: str = Query(..., description="State code, e.g. OH or MULTI"),
    slug: str = Query(..., description="Game slug, e.g. pick-4-oh"),
    db: Session = Depends(get_db),
):
    result = crud.get_latest_results_grouped(db, state, slug)
    if not result:
        raise HTTPException(status_code=404, detail="Grouped results not found")
    return result


@app.get("/api/past-draws", response_model=list[schemas.DrawOut])
def api_past_draws(
    state: str = Query(..., description="State code, e.g. OH or MULTI"),
    slug: str = Query(..., description="Game slug, e.g. powerball"),
    limit: int = Query(20, description="How many past draws to return"),
    db: Session = Depends(get_db),
):
    return crud.get_past_draws(db, state, slug, limit)


@app.get("/api/most-frequent", response_model=list[schemas.FrequencyStatOut])
def api_most_frequent(
    state: str = Query(..., description="State code, e.g. CA or MULTI"),
    slug: str = Query(..., description="Game slug, e.g. fantasy-5"),
    limit: int = Query(5, description="How many numbers to return"),
    db: Session = Depends(get_db),
):
    return crud.get_frequency_stats(db, state, slug, "most", limit)


@app.get("/api/least-frequent", response_model=list[schemas.FrequencyStatOut])
def api_least_frequent(
    state: str = Query(..., description="State code, e.g. CA or MULTI"),
    slug: str = Query(..., description="Game slug, e.g. fantasy-5"),
    limit: int = Query(5, description="How many numbers to return"),
    db: Session = Depends(get_db),
):
    return crud.get_frequency_stats(db, state, slug, "least", limit)