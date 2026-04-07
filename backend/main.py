from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from typing import List, Optional
import os
import traceback
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

from backend.automation import run_order_automation
from backend.config import SQLALCHEMY_DATABASE_URL
import logging

# Database setup
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# SQLAlchemy models
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

# Setup logging
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Migrate existing database: Add location_name column if it doesn't exist
def migrate_database():
    """Add location_name column to presets table if it doesn't exist"""
    try:
        with engine.begin() as conn:  # Use begin() for automatic transaction handling
            # Check if column exists by querying table info
            result = conn.execute(text("PRAGMA table_info(presets)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'location_name' not in columns:
                logger.info("Migrating database: Adding location_name column to presets table")
                conn.execute(text("ALTER TABLE presets ADD COLUMN location_name VARCHAR"))
                logger.info("Database migration completed successfully")
            else:
                logger.info("Database already has location_name column")
    except Exception as e:
        # It's OK if the table doesn't exist yet - create_all() will create it with the new column
        logger.info(f"Migration check: {str(e)} (this is OK if table doesn't exist yet)")

# Run migration
migrate_database()

app = FastAPI(title="UMN Order Automation")

# Exception handlers for proper JSON error responses
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors and return JSON response"""
    logger.error(f"Database error: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": f"Database error: {str(exc)}"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general errors and return JSON response"""
    logger.error(f"Unhandled error: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

# Get frontend path
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

# Mount static files (CSS, JS)
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your actual domain
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic models for request/response
class UserCreate(BaseModel):
    name: str
    phone_number: str


class ItemWithModifiers(BaseModel):
    name: str
    modifiers: List[str] = []  # List of modifier names (e.g., ["Bun", "American Cheese"])


class PresetCreate(BaseModel):
    user_id: int
    preset_name: str
    items: List[ItemWithModifiers]  # List of items with their modifiers
    location_name: Optional[str] = None  # Dining hall location name


class PresetResponse(BaseModel):
    id: int
    user_id: int
    preset_name: str
    items: List[ItemWithModifiers]
    location_name: Optional[str] = None

    class Config:
        from_attributes = True


class OrderRequest(BaseModel):
    preset_id: int


class OrderResponse(BaseModel):
    success: bool
    message: str
    cooldown_remaining: Optional[int] = None  # seconds remaining


# Helper functions

def parse_items_json(items_json: str) -> List[ItemWithModifiers]:
    """
    Parse the items_json string from the database into a list of ItemWithModifiers objects.
    Handles both old format (list of strings) and new format (list of dicts).
    """
    if not items_json:
        return []

    items_list = json.loads(items_json)
    if not items_list:
        return []

    # Handle both old format (list of strings) and new format (list of dicts)
    if isinstance(items_list[0], str):
        # Old format: convert to new format
        return [ItemWithModifiers(name=item, modifiers=[]) for item in items_list]
    else:
        # New format
        return [ItemWithModifiers(name=item["name"], modifiers=item.get("modifiers", [])) for item in items_list]


def check_user_cooldown(db: Session, phone_number: str) -> Optional[OrderResponse]:
    """Check if the user is on cooldown, return OrderResponse if so, else None."""
    last_order = db.query(OrderHistory).filter(
        OrderHistory.phone_number == phone_number
    ).order_by(OrderHistory.ordered_at.desc()).first()

    if last_order:
        time_since_last_order = datetime.utcnow() - last_order.ordered_at
        if time_since_last_order < timedelta(minutes=30):
            remaining_seconds = int((timedelta(minutes=30) - time_since_last_order).total_seconds())
            return OrderResponse(
                success=False,
                message=f"Cooldown active. Please wait {remaining_seconds // 60} minutes and {remaining_seconds % 60} seconds.",
                cooldown_remaining=remaining_seconds
            )
    return None

def format_items_for_automation(items_objects: List[ItemWithModifiers]) -> List[dict]:
    """Convert a list of ItemWithModifiers to a list of dicts for the automation script."""
    return [{"name": item.name, "modifiers": item.modifiers} for item in items_objects]


# API Endpoints

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend"""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Frontend not found</h1><p>Please ensure frontend/index.html exists.</p>", status_code=404)


@app.post("/api/users", response_model=dict)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    db_user = User(name=user.name, phone_number=user.phone_number)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"id": db_user.id, "name": db_user.name, "phone_number": db_user.phone_number}


@app.get("/api/users", response_model=List[dict])
def get_users(db: Session = Depends(get_db)):
    """Get all users"""
    users = db.query(User).all()
    return [{"id": u.id, "name": u.name, "phone_number": u.phone_number} for u in users]


@app.post("/api/presets", response_model=PresetResponse)
def create_preset(preset: PresetCreate, db: Session = Depends(get_db)):
    """Create a new order preset"""
    # Convert items to JSON (list of dicts with name and modifiers)
    items_data = [{"name": item.name, "modifiers": item.modifiers} for item in preset.items]
    db_preset = Preset(
        user_id=preset.user_id,
        preset_name=preset.preset_name,
        items_json=json.dumps(items_data),
        location_name=preset.location_name
    )
    db.add(db_preset)
    db.commit()
    db.refresh(db_preset)
    # Parse back to ItemWithModifiers objects
    items_objects = parse_items_json(db_preset.items_json)
    return PresetResponse(
        id=db_preset.id,
        user_id=db_preset.user_id,
        preset_name=db_preset.preset_name,
        items=items_objects,
        location_name=db_preset.location_name
    )


@app.get("/api/presets", response_model=List[PresetResponse])
def get_presets(db: Session = Depends(get_db)):
    """Get all presets"""
    presets = db.query(Preset).all()
    result = []
    for p in presets:
        items_objects = parse_items_json(p.items_json)
        result.append(PresetResponse(
            id=p.id,
            user_id=p.user_id,
            preset_name=p.preset_name,
            items=items_objects,
            location_name=p.location_name
        ))
    return result


@app.get("/api/presets/{preset_id}", response_model=PresetResponse)
def get_preset(preset_id: int, db: Session = Depends(get_db)):
    """Get a specific preset"""
    preset = db.query(Preset).filter(Preset.id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    items_objects = parse_items_json(preset.items_json)
    return PresetResponse(
        id=preset.id,
        user_id=preset.user_id,
        preset_name=preset.preset_name,
        items=items_objects,
        location_name=preset.location_name
    )


@app.delete("/api/presets/{preset_id}")
def delete_preset(preset_id: int, db: Session = Depends(get_db)):
    """Delete a preset"""
    preset = db.query(Preset).filter(Preset.id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    db.delete(preset)
    db.commit()
    return {"message": "Preset deleted successfully"}


@app.post("/api/order", response_model=OrderResponse)
def place_order(order_request: OrderRequest, db: Session = Depends(get_db)):
    """Place an order using a preset"""
    
    # Get preset
    preset = db.query(Preset).filter(Preset.id == order_request.preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    # Get user
    user = db.query(User).filter(User.id == preset.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check cooldown
    cooldown_response = check_user_cooldown(db, user.phone_number)
    if cooldown_response:
        return cooldown_response
    
    # Run automation
    items_objects = parse_items_json(preset.items_json)
    items = format_items_for_automation(items_objects)

    result = run_order_automation(user.name, user.phone_number, items, location_name=preset.location_name)
    
    # Record order attempt
    order_history = OrderHistory(
        preset_id=preset.id,
        phone_number=user.phone_number,
        success=result["success"],
        message=result["message"]
    )
    db.add(order_history)
    db.commit()
    
    return OrderResponse(
        success=result["success"],
        message=result["message"],
        cooldown_remaining=None
    )


@app.get("/api/order-history")
def get_order_history(phone_number: Optional[str] = None, db: Session = Depends(get_db)):
    """Get order history"""
    query = db.query(OrderHistory)
    if phone_number:
        query = query.filter(OrderHistory.phone_number == phone_number)
    orders = query.order_by(OrderHistory.ordered_at.desc()).limit(20).all()
    return [
        {
            "id": o.id,
            "preset_id": o.preset_id,
            "phone_number": o.phone_number,
            "success": o.success,
            "message": o.message,
            "ordered_at": o.ordered_at.isoformat()
        }
        for o in orders
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
