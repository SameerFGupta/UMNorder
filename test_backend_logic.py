import json

def parse_items_json(items_json: str):
    if not items_json:
        return []

    items_list = json.loads(items_json)
    if not items_list:
        return []

    if isinstance(items_list[0], str):
        return [{"name": item, "modifiers": []} for item in items_list]
    else:
        return [{"name": item["name"], "modifiers": item.get("modifiers", [])} for item in items_list]

def test_parse_items_json_new_format():
    items = [
        {"name": "Hamburger", "modifiers": ["Bun", "Cheese"]},
        {"name": "Fries", "modifiers": []}
    ]
    items_json = json.dumps(items)
    result = parse_items_json(items_json)

    assert len(result) == 2
    assert result[0]["name"] == "Hamburger"
    assert result[0]["modifiers"] == ["Bun", "Cheese"]
    assert result[1]["name"] == "Fries"
    assert result[1]["modifiers"] == []

def test_parse_items_json_old_format():
    items = ["Hamburger", "Fries"]
    items_json = json.dumps(items)
    result = parse_items_json(items_json)

    assert len(result) == 2
    assert result[0]["name"] == "Hamburger"
    assert result[0]["modifiers"] == []
    assert result[1]["name"] == "Fries"
    assert result[1]["modifiers"] == []

def test_parse_items_json_empty():
    assert parse_items_json("") == []
    assert parse_items_json("[]") == []
    assert parse_items_json(None) == []

if __name__ == "__main__":
    test_parse_items_json_new_format()
    test_parse_items_json_old_format()
    test_parse_items_json_empty()
    print("All backend logic tests passed!")
