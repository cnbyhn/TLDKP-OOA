import json

ITEMS_JSON_FILE = "items.json"

def load_items_from_json():
    try:
        with open(ITEMS_JSON_FILE, "r") as f:
            items = json.load(f)
        print("✅ Items loaded from JSON.")
        return items
    except FileNotFoundError:
        print(f"❌ {ITEMS_JSON_FILE} not found.")
        return []
    except json.JSONDecodeError:
        print(f"❌ Error decoding {ITEMS_JSON_FILE}.")
        return []
