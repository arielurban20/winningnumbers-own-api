from datetime import date, datetime
from typing import Optional, Any

from pydantic import BaseModel, ConfigDict


class StateOut(BaseModel):
    id: int
    name: str
    code: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class GameOut(BaseModel):
    id: int
    state_id: Optional[int]
    name: str
    slug: str
    logo_url: Optional[str]
    game_type: str
    is_multi_state: bool
    draw_timezone: Optional[str]
    draw_time: Optional[str]
    has_bonus_ball: bool
    has_multiplier: bool
    has_secondary_draws: bool
    has_multiple_daily_draws: bool
    main_ball_count: Optional[int]
    main_ball_min: Optional[int]
    main_ball_max: Optional[int]
    bonus_ball_min: Optional[int]
    bonus_ball_max: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class DrawOut(BaseModel):
    id: int
    game_id: int
    draw_date: date
    draw_type: str
    draw_time: Optional[str]
    main_numbers: Any
    bonus_number: Optional[str]
    multiplier: Optional[str]
    jackpot: Optional[str]
    cash_payout: Optional[str]
    secondary_draws: Optional[Any]
    notes: Optional[str]
    source_url: Optional[str]
    created_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class FrequencyStatOut(BaseModel):
    id: int
    game_id: int
    stat_type: str
    number: str
    count: int
    last_seen_date: Optional[date]
    created_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class LatestResultsGroupedOut(BaseModel):
    draw_date: date
    draws: list[DrawOut]


class GameConfigOut(BaseModel):
    id: int
    name: str
    slug: str
    state_code: Optional[str]
    game_type: str
    is_multi_state: bool
    has_multiple_daily_draws: bool
    supports_grouped_latest: bool
    supports_frequency_stats: bool
    has_bonus_ball: bool
    has_multiplier: bool
    draw_timezone: Optional[str]
    draw_time: Optional[str]


class SystemSummaryOut(BaseModel):
    ok: bool
    states_count: int
    games_count: int
    draws_count: int
    frequency_stats_count: int
    grouped_games_count: int
    stats_supported_games_count: int