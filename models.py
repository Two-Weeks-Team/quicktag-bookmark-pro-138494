import os
import re
from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Boolean,
    LargeBinary,
    DateTime,
    ForeignKey,
    Table,
    PrimaryKeyConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# Database URL handling (env var with auto‑fix for async schemes)
# ---------------------------------------------------------------------------
raw_url = os.getenv(
    "DATABASE_URL",
    os.getenv("POSTGRES_URL", "sqlite:///./app.db")
)
# Fix async scheme to psycopg if needed
if raw_url.startswith("postgresql+asyncpg://"):
    raw_url = raw_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
elif raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql+psycopg://")
# Determine if we need SSL (non‑localhost and not SQLite)
if raw_url.startswith("sqlite"):
    engine = create_engine(raw_url, echo=False)
else:
    # Extract host to decide on SSL – simple heuristic: if 'localhost' not in URL
    ssl_mode = "require" if not re.search(r"localhost|127\.0\.0\.1", raw_url) else "disable"
    engine = create_engine(
        raw_url,
        echo=False,
        connect_args={"sslmode": ssl_mode} if ssl_mode != "disable" else {},
    )

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

# ---------------------------------------------------------------------------
# Table name prefix – prevents collisions in shared DB
# ---------------------------------------------------------------------------
PREFIX = "qt_"

class Bookmark(Base):
    __tablename__ = f"{PREFIX}bookmarks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey(f"{PREFIX}users.id"), nullable=True)
    url = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    favicon_url = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    ai_summary_confidence = Column(Float, nullable=True)
    encrypted_data = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    tags = relationship(
        "Tag",
        secondary=f"{PREFIX}bookmark_tags",
        backref="bookmarks",
    )
    relations = relationship(
        "BookmarkRelation",
        primaryjoin="Bookmark.id==BookmarkRelation.source_id",
        backref="source_bookmark",
    )

class Tag(Base):
    __tablename__ = f"{PREFIX}tags"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(Text, nullable=False, unique=True)
    is_ai_suggested = Column(Boolean, nullable=False, default=True)

class BookmarkTag(Base):
    __tablename__ = f"{PREFIX}bookmark_tags"
    bookmark_id = Column(UUID(as_uuid=True), ForeignKey(f"{PREFIX}bookmarks.id"), nullable=False)
    tag_id = Column(UUID(as_uuid=True), ForeignKey(f"{PREFIX}tags.id"), nullable=False)
    confidence_score = Column(Float, nullable=True)
    __table_args__ = (
        PrimaryKeyConstraint('bookmark_id', 'tag_id', name=f"{PREFIX}pk_bookmark_tag"),
    )

class BookmarkRelation(Base):
    __tablename__ = f"{PREFIX}bookmark_relations"
    source_id = Column(UUID(as_uuid=True), ForeignKey(f"{PREFIX}bookmarks.id"), nullable=False)
    target_id = Column(UUID(as_uuid=True), ForeignKey(f"{PREFIX}bookmarks.id"), nullable=False)
    relation_type = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (
        PrimaryKeyConstraint('source_id', 'target_id', 'relation_type', name=f"{PREFIX}pk_bookmark_relation"),
    )

class User(Base):
    __tablename__ = f"{PREFIX}users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(Text, nullable=False, unique=True)
    sync_token_id = Column(UUID(as_uuid=True), ForeignKey(f"{PREFIX}sync_tokens.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class SyncToken(Base):
    __tablename__ = f"{PREFIX}sync_tokens"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    token = Column(Text, nullable=False, unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey(f"{PREFIX}users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

# Create tables if they do not exist (for simple deployments)
Base.metadata.create_all(bind=engine)
