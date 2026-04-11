from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
import os
import traceback
import json
import logging

from backend.automation import run_order_automation
from backend.helpers import parse_items_json, check_user_cooldown
from backend.models import engine, SessionLocal, Base, User, Preset, OrderHistory, migrate_database
from backend.schemas import UserCreate, ItemWithModifiers, PresetCreate, PresetResponse, OrderRequest, OrderResponse
migrate_database()

app = FastAPI(title="UMN Order Automation")

"""We catch all exceptions globally to ensure the frontend always receives a well-formed JSON response, preventing opaque 500 HTML errors."""
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": f"Database error: {str(exc)}"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

"""Mounting static files under a distinct path ensures clear separation between API routes and static assets, avoiding routing conflicts."""
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""Using a dependency yield pattern for the database session ensures connections are automatically closed and returned to the pool after the request lifecycle, preventing connection leaks."""
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Frontend not found</h1><p>Please ensure frontend/index.html exists.</p>", status_code=404)

@app.post("/api/users", response_model=dict)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(name=user.name, phone_number=user.phone_number)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"id": db_user.id, "name": db_user.name, "phone_number": db_user.phone_number}

@app.get("/api/users", response_model=List[dict])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "name": u.name, "phone_number": u.phone_number} for u in users]

@app.post("/api/presets", response_model=PresetResponse)
def create_preset(preset: PresetCreate, db: Session = Depends(get_db)):
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
    """We immediately parse the committed JSON string back to objects to ensure the API response matches the structured format expected by the frontend."""
    items_objects = parse_items_json(db_preset.items_json)
    items_models = [ItemWithModifiers(**item) for item in items_objects]
    return PresetResponse(
        id=db_preset.id,
        user_id=db_preset.user_id,
        preset_name=db_preset.preset_name,
        items=items_models,
        location_name=db_preset.location_name
    )

@app.get("/api/presets", response_model=List[PresetResponse])
def get_presets(db: Session = Depends(get_db)):
    presets = db.query(Preset).all()
    result = []
    for p in presets:
        items_objects = parse_items_json(p.items_json)
        items_models = [ItemWithModifiers(**item) for item in items_objects]
        result.append({
            "id": p.id,
            "user_id": p.user_id,
            "preset_name": p.preset_name,
            "items": items_models,
            "location_name": p.location_name
        })
    return result

@app.get("/api/presets/{preset_id}", response_model=PresetResponse)
def get_preset(preset_id: int, db: Session = Depends(get_db)):
    preset = db.query(Preset).filter(Preset.id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    items_objects = parse_items_json(preset.items_json)
    items_models = [ItemWithModifiers(**item) for item in items_objects]
    return PresetResponse(
        id=preset.id,
        user_id=preset.user_id,
        preset_name=preset.preset_name,
        items=items_models,
        location_name=preset.location_name
    )

@app.delete("/api/presets/{preset_id}")
def delete_preset(preset_id: int, db: Session = Depends(get_db)):
    preset = db.query(Preset).filter(Preset.id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    db.delete(preset)
    db.commit()
    return {"message": "Preset deleted successfully"}

@app.post("/api/order", response_model=OrderResponse)
def place_order(order_request: OrderRequest, db: Session = Depends(get_db)):
    preset = db.query(Preset).filter(Preset.id == order_request.preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    user = db.query(User).filter(User.id == preset.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    cooldown_response = check_user_cooldown(db, user.phone_number)
    if cooldown_response:
        return cooldown_response
    items = parse_items_json(preset.items_json)

    result = run_order_automation(user.name, user.phone_number, items, location_name=preset.location_name)
    
    """We record every order attempt regardless of success to provide auditability and accurately enforce the cooldown system."""
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
