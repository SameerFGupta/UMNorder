import json
from typing import List

def parse_items_json(items_json: str) -> List[dict]:
    """
    Parse the items_json string from the database into a list of dicts.
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
        return [{"name": item, "modifiers": []} for item in items_list]
    else:
        # New format
        return [{"name": item["name"], "modifiers": item.get("modifiers", [])} for item in items_list]
