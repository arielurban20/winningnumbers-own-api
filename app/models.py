from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class State(Base):
    __tablename__ = "states"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(10), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)

    games = relationship("Game", back_populates="state")


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=True)
    name = Column(String(150), nullable=False)
    slug = Column(String(150), nullable=False, index=True)
    logo_url = Column(Text, nullable=True)

    game_type = Column(String(30), nullable=False, default="state-specific")
    is_multi_state = Column(Boolean, nullable=False, default=False)

    draw_timezone = Column(String(100), nullable=True)
    draw_time = Column(String(30), nullable=True)

    has_bonus_ball = Column(Boolean, nullable=False, default=False)
    has_multiplier = Column(Boolean, nullable=False, default=False)
    has_secondary_draws = Column(Boolean, nullable=False, default=False)
    has_multiple_daily_draws = Column(Boolean, nullable=False, default=False)

    main_ball_count = Column(Integer, nullable=True)
    main_ball_min = Column(Integer, nullable=True)
    main_ball_max = Column(Integer, nullable=True)
    bonus_ball_min = Column(Integer, nullable=True)
    bonus_ball_max = Column(Integer, nullable=True)

    source_result_url = Column(Text, nullable=True)
    source_stats_url = Column(Text, nullable=True)
    stats_period_default = Column(String(20), nullable=True)

    state = relationship("State", back_populates="games")
    draws = relationship("Draw", back_populates="game")
    frequency_stats = relationship("FrequencyStat", back_populates="game")


class Draw(Base):
    __tablename__ = "draws"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)

    draw_date = Column(Date, nullable=False, index=True)
    draw_type = Column(String(50), nullable=False, default="main")
    draw_time = Column(String(30), nullable=True)

    main_numbers = Column(JSON, nullable=False)
    bonus_number = Column(String(20), nullable=True)
    multiplier = Column(String(20), nullable=True)

    jackpot = Column(String(100), nullable=True)
    cash_payout = Column(String(100), nullable=True)

    secondary_draws = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    game = relationship("Game", back_populates="draws")


class FrequencyStat(Base):
    __tablename__ = "frequency_stats"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)

    stat_type = Column(String(20), nullable=False)
    number = Column(String(20), nullable=False)
    count = Column(Integer, nullable=False)
    last_seen_date = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    game = relationship("Game", back_populates="frequency_stats")