import json
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.schemas import ItemWithModifiers, OrderResponse
from backend.models import OrderHistory

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

    if isinstance(items_list[0], str):
        return [ItemWithModifiers(name=item, modifiers=[]) for item in items_list]
    else:
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
