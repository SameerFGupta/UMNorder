from pydantic import BaseModel
from typing import List, Optional

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
