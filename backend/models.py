import logging
from sqlalchemy import create_engine, text, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func
from backend.config import SQLALCHEMY_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Preset(Base):
    __tablename__ = "presets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    preset_name = Column(String, nullable=False)
    items_json = Column(Text, nullable=False)
    location_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class OrderHistory(Base):
    __tablename__ = "order_history"
    id = Column(Integer, primary_key=True, index=True)
    preset_id = Column(Integer, nullable=False)
    phone_number = Column(String, nullable=False)
    success = Column(Boolean, nullable=False)
    message = Column(Text, nullable=False)
    ordered_at = Column(DateTime(timezone=True), server_default=func.now())

logger = logging.getLogger(__name__)
Base.metadata.create_all(bind=engine)

"""We handle schema migration explicitly here to support seamless updates for existing deployments without requiring external migration tools like Alembic for this simple single-file app."""
def migrate_database():
    """Add location_name column to presets table if it doesn't exist"""
    try:
        with engine.begin() as conn:
            result = conn.execute(text("PRAGMA table_info(presets)"))
            columns = [row[1] for row in result.fetchall()]

            if 'location_name' not in columns:
                logger.info("Migrating database: Adding location_name column to presets table")
                conn.execute(text("ALTER TABLE presets ADD COLUMN location_name VARCHAR"))
                logger.info("Database migration completed successfully")
            else:
                logger.info("Database already has location_name column")
    except Exception as e:
        logger.info(f"Migration check: {str(e)} (this is OK if table doesn't exist yet)")
