import json
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.models import OrderHistory
from backend.schemas import OrderResponse

def parse_items_json(items_json: str) -> List[dict]:
    """We maintain backwards compatibility for the items_json parsing to ensure existing database records aren't broken when deploying the new modifier features."""
    if not items_json:
        return []

    items_list = json.loads(items_json)
    if not items_list:
        return []

    if isinstance(items_list[0], str):
        return [{"name": item, "modifiers": []} for item in items_list]
    else:
        return [{"name": item["name"], "modifiers": item.get("modifiers", [])} for item in items_list]


def check_user_cooldown(db: Session, phone_number: str) -> Optional[OrderResponse]:
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
