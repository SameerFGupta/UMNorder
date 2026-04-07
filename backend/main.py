from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
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
import logging

"""Setting check_same_thread to False is required for SQLite since FastAPI may dispatch requests across multiple threads."""
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./umnorder.db")
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


"""Declarative base definitions allow us to use ORM features rather than raw SQL, providing type safety and easier migrations."""
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

"""Standardized logger setup is used to ensure all backend components log consistently."""
logger = logging.getLogger(__name__)

"""Creating all tables explicitly at startup ensures the database schema is immediately ready for incoming requests."""
Base.metadata.create_all(bind=engine)

"""We execute raw PRAGMA SQL to check if the column exists, since SQLite does not support robust ALTER TABLE statements easily through SQLAlchemy."""
def migrate_database():
    try:
        """Using engine.begin() provides a context manager that automatically commits or rolls back transactions based on execution success."""
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
        """Gracefully handle initial startup when the table may not exist yet; create_all() will handle the actual creation in that case."""
        logger.info(f"Migration check: {str(e)} (this is OK if table doesn't exist yet)")

migrate_database()

app = FastAPI(title="UMN Order Automation")

"""Exception handlers mapped globally to ensure we never leak sensitive stack traces and always return well-formed JSON."""
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

"""Dynamically determine frontend path relative to this script to support arbitrary working directories during execution."""
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

"""CORS configuration allows the separate frontend implementation to hit these API endpoints during development and deployment."""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""Using dependency injection (Yield) for the DB session ensures we automatically close the transaction pool after the request lifecycle completes, preventing connection leaks."""
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


"""Pydantic validation layers guarantee request schemas match expected structures, preventing downstream type or missing key errors."""
class UserCreate(BaseModel):
    name: str
    phone_number: str


class ItemWithModifiers(BaseModel):
    name: str
    modifiers: List[str] = []


class PresetCreate(BaseModel):
    user_id: int
    preset_name: str
    items: List[ItemWithModifiers]
    location_name: Optional[str] = None


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
    cooldown_remaining: Optional[int] = None


"""Parsing utility checks data structure format and upgrades legacy format objects dynamically, allowing safe backwards compatibility with older database records."""
def parse_items_json(items_json: str) -> List[ItemWithModifiers]:
    if not items_json:
        return []

    items_list = json.loads(items_json)
    if not items_list:
        return []

    if isinstance(items_list[0], str):
        return [ItemWithModifiers(name=item, modifiers=[]) for item in items_list]
    else:
        return [ItemWithModifiers(name=item["name"], modifiers=item.get("modifiers", [])) for item in items_list]


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
    """Explicitly remapping the Pydantic models to dicts before JSON serialization due to legacy format persistence constraints."""
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
    """We parse back from JSON locally after commit so the response accurately reflects what is persisted."""
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
    
    preset = db.query(Preset).filter(Preset.id == order_request.preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    user = db.query(User).filter(User.id == preset.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    """Validating cooldown period explicitly on the backend ensures rate limits are enforced universally, even if frontend checks are bypassed."""
    last_order = db.query(OrderHistory).filter(
        OrderHistory.phone_number == user.phone_number
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
    
    """Converting strongly typed Pydantic objects back to dicts, as the automation library explicitly operates on dictionaries."""
    items_objects = parse_items_json(preset.items_json)
    items = [{"name": item.name, "modifiers": item.modifiers} for item in items_objects]

    result = run_order_automation(user.name, user.phone_number, items, location_name=preset.location_name)
    
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
