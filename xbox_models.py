# models.py
from sqlalchemy import (
    Column,
    Date,
    String,
    Boolean,
    DateTime,
    Integer,
    BigInteger,
    SmallInteger,
    ForeignKey,
    func,
    UniqueConstraint,
    event,
    Float,
    PrimaryKeyConstraint,
    text,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.dialects.postgresql import REAL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from os import getenv
from dotenv import load_dotenv

DATABASE_URL = "postgresql+asyncpg://postgres:admin@localhost:5432/xboxtracker"

async_engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session_maker = sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession
)

Base = declarative_base()

load_dotenv()
XBOX_CHARTS = getenv("XBOX_CHARTS")
XBOX_TRACKER = getenv("XBOX_TRACKER")


def get_xbox_tracker_session():
    engine = create_engine(XBOX_TRACKER)
    Session = sessionmaker(bind=engine)
    return Session()


def get_xbox_charts_session():
    engine = create_engine(XBOX_CHARTS)
    Session = sessionmaker(bind=engine)
    return Session()


# --- Lookup Tables ---


class DeviceType(Base):
    __tablename__ = "device_types"

    # Smallint is sufficient for device types
    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)


class Title(Base):
    __tablename__ = "titles"

    # Xbox Title IDs are unsigned 32-bit, so they fit in BigInteger (int8)
    title_id = Column(BigInteger, primary_key=True, autoincrement=False)
    title_name = Column(String, nullable=False)


# --- Main Tables ---


class User(Base):
    __tablename__ = "users"

    xuid = Column(BigInteger, primary_key=True)

    # Optimization: Boolean flags
    friends_crawled = Column(Boolean, default=False)
    is_gold = Column(Boolean, nullable=True)

    # Optimization: Changed from String to FK ID
    device_type_id = Column(SmallInteger, ForeignKey("device_types.id"), nullable=True)

    # Timestamps
    last_seen = Column(DateTime(timezone=True), nullable=True)
    last_played = Column(DateTime(timezone=True), nullable=True)
    time_presence_checked = Column(DateTime(timezone=True), nullable=True)
    time_titles_checked = Column(DateTime(timezone=True), nullable=True)
    next_scheduled_check = Column(DateTime(timezone=True), nullable=True)
    # Stats
    friends_count = Column(SmallInteger, nullable=True)
    year_joined = Column(SmallInteger, nullable=True)
    total_checks = Column(SmallInteger, nullable=True)
    activity_score = Column(REAL, nullable=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    gamerscore = Column(Integer, nullable=True)
    # Relationship (Optional, helpful for queries like entry.device_type.name)
    device_type = relationship("DeviceType")
    time_profile_checked = Column(DateTime(timezone=True), nullable=True)


class GameSession(Base):
    __tablename__ = "sessions"

    xuid = Column(BigInteger, primary_key=True)
    title_id = Column(BigInteger, ForeignKey("titles.title_id"), primary_key=True)
    last_played = Column(DateTime, primary_key=True)

    time_requested = Column(DateTime)
    activity_score = Column(REAL, nullable=True)
    device_type_id = Column(SmallInteger, nullable=True)


class TitleCheckRotation(Base):
    __tablename__ = "title_check_rotation"

    xuid = Column(String, primary_key=True)
    processed = Column(Boolean, default=False)
    profile_checked = Column(Boolean, default=False, nullable=False)
    date = Column(DateTime, nullable=True)
    activity_score = Column(REAL, nullable=True)
    device_type_id = Column(SmallInteger, nullable=True)


class RevivalLog(Base):
    __tablename__ = "revival_logs"
    id = Column(Integer, primary_key=True)
    xuid = Column(BigInteger, nullable=False)
    previous_score = Column(Float)
    revival_time = Column(DateTime(timezone=True), server_default=func.now())


class AnalysisTable(Base):
    __tablename__ = "analytics_daily_snapshot"
    snapshot_date = Column(Date, primary_key=True, nullable=False)
    total_db_size = Column(Integer)
    scans_performed = Column(Integer)
    system_overdue_backlog = Column(Integer)
    confirmed_dau = Column(Integer)
    confirmed_dau = Column(Integer)
    users_regular = Column(Integer)
    users_casual = Column(Integer)
    users_ghost = Column(Integer)
    ghosts_checked_24h = Column(Integer)
    ghosts_detected_24h = Column(Integer)


class UserDevice(Base):
    __tablename__ = "user_devices"
    xuid = Column(
        BigInteger, ForeignKey("users.xuid", ondelete="CASCADE"), primary_key=True
    )
    device_type_id = Column(SmallInteger, primary_key=True)
    times_seen = Column(Integer, default=1, server_default=text("1"))
    last_seen = Column(
        DateTime(timezone=True), default=func.now(), server_default=func.now()
    )
