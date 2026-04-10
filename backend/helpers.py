import json
from typing import List

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
