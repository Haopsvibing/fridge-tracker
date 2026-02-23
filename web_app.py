import anthropic
import base64
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
client = anthropic.Anthropic()

DATA_FILE = "fridge_data.json"
SHELF_LIFE_FILE = "shelf_life_data.json"


def load_fridge_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"items": []}


def save_fridge_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_shelf_life_data():
    if os.path.exists(SHELF_LIFE_FILE):
        with open(SHELF_LIFE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_shelf_life_data(data):
    with open(SHELF_LIFE_FILE, "w") as f:
        json.dump(data, f, indent=4)


def sort_items_by_expiry(items):
    today = datetime.now().date()
    def sort_key(item):
        expiry = item.get("expiry_date")
        if expiry:
            return (0, datetime.strptime(expiry, "%Y-%m-%d").date())
        return (1, today)
    items.sort(key=sort_key)
    return items


def analyze_image(image_data, media_type, mode="fridge"):
    """Analyze fridge or receipt image."""
    if mode == "receipt":
        prompt = """Analyze this grocery receipt and list all FOOD items purchased.
Keep the EXACT names as they appear on the receipt (in their original language).
Include weight/size if shown (e.g., "Oltermanni 500g", "Maito 1L").
Ignore non-food items like bags, cleaning supplies, etc.

Return ONLY a JSON array: [{"name": "Oltermanni 500g", "quantity": 1}, {"name": "Kevytmaito 1L", "quantity": 2}]
Keep original names exactly as printed. Just the JSON array, nothing else."""
    else:
        prompt = """Analyze this fridge image and list all food items.
Return ONLY a JSON array: ["milk", "eggs", "butter"]"""
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                {"type": "text", "text": prompt}
            ],
        }],
    )
    
    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(response_text)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "Fridgic",
        "short_name": "Fridgic",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#051C2C",
        "theme_color": "#051C2C",
        "icons": [{"src": "/static/icon.png", "sizes": "192x192", "type": "image/png"}]
    })


@app.route('/api/items', methods=['GET'])
def get_items():
    data = load_fridge_data()
    today = datetime.now().date()
    
    for item in data["items"]:
        expiry = item.get("expiry_date")
        if expiry:
            expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
            days_left = (expiry_date - today).days
            item["days_left"] = days_left
            if days_left < 0:
                item["status"] = "expired"
            elif days_left == 0:
                item["status"] = "today"
            elif days_left <= 3:
                item["status"] = "soon"
            else:
                item["status"] = "ok"
        else:
            item["days_left"] = None
            item["status"] = "no_date"
    
    data["items"] = sort_items_by_expiry(data["items"])
    return jsonify(data["items"])


@app.route('/api/items', methods=['POST'])
def add_item():
    item_data = request.json
    data = load_fridge_data()
    
    data["items"].append({
        "name": item_data["name"],
        "quantity": item_data.get("quantity", 1),
        "expiry_date": item_data.get("expiry_date"),
        "added_date": datetime.now().strftime("%Y-%m-%d")
    })
    
    data["items"] = sort_items_by_expiry(data["items"])
    save_fridge_data(data)
    return jsonify({"success": True})


@app.route('/api/items/<item_name>', methods=['PUT'])
def update_item(item_name):
    item_data = request.json
    data = load_fridge_data()
    
    for item in data["items"]:
        if item["name"] == item_name:
            item["quantity"] = item_data.get("quantity", item["quantity"])
            item["expiry_date"] = item_data.get("expiry_date", item["expiry_date"])
            break
    
    data["items"] = sort_items_by_expiry(data["items"])
    save_fridge_data(data)
    return jsonify({"success": True})


@app.route('/api/items/<item_name>', methods=['DELETE'])
def delete_item(item_name):
    data = load_fridge_data()
    data["items"] = [i for i in data["items"] if i["name"] != item_name]
    save_fridge_data(data)
    return jsonify({"success": True})


@app.route('/api/scan', methods=['POST'])
def scan_image():
    image_file = request.files.get('image')
    mode = request.form.get('mode', 'fridge')
    
    if not image_file:
        return jsonify({"error": "No image provided"}), 400
    
    image_data = base64.standard_b64encode(image_file.read()).decode("utf-8")
    ext = image_file.filename.lower().split(".")[-1]
    media_types = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}
    media_type = media_types.get(ext, "image/jpeg")
    
    try:
        items = analyze_image(image_data, media_type, mode)
        return jsonify({"items": items, "mode": mode})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/shelf-life', methods=['GET'])
def get_shelf_life():
    return jsonify(load_shelf_life_data())


@app.route('/api/shelf-life', methods=['POST'])
def save_shelf_life():
    data = request.json
    shelf_life = load_shelf_life_data()
    shelf_life[data["name"].lower().strip()] = data["days"]
    save_shelf_life_data(shelf_life)
    return jsonify({"success": True})


@app.route('/api/shelf-life/<item_name>', methods=['PUT'])
def update_shelf_life(item_name):
    """Update shelf life days for an item."""
    data = request.json
    shelf_life = load_shelf_life_data()
    key = item_name.lower().strip()
    if key in shelf_life:
        shelf_life[key] = data["days"]
        save_shelf_life_data(shelf_life)
        return jsonify({"success": True})
    return jsonify({"error": "Item not found"}), 404


@app.route('/api/shelf-life/<item_name>', methods=['DELETE'])
def delete_shelf_life(item_name):
    """Delete shelf life entry for an item."""
    shelf_life = load_shelf_life_data()
    key = item_name.lower().strip()
    if key in shelf_life:
        del shelf_life[key]
        save_shelf_life_data(shelf_life)
        return jsonify({"success": True})
    return jsonify({"error": "Item not found"}), 404


@app.route('/api/process-receipt', methods=['POST'])
def process_receipt():
    """Process receipt items with shelf life data."""
    items = request.json.get("items", [])
    shelf_life = load_shelf_life_data()
    data = load_fridge_data()
    today = datetime.now()
    
    results = []
    for item in items:
        item_name = item["name"]
        quantity = item.get("quantity", 1)
        key = item_name.lower().strip()
        
        if key in shelf_life:
            days = shelf_life[key]
            expiry_date = (today + timedelta(days=days)).strftime("%Y-%m-%d")
            
            existing = next((i for i in data["items"] if i["name"].lower() == key), None)
            if existing:
                existing["quantity"] = existing.get("quantity", 1) + quantity
                if existing.get("expiry_date"):
                    existing_exp = datetime.strptime(existing["expiry_date"], "%Y-%m-%d")
                    new_exp = datetime.strptime(expiry_date, "%Y-%m-%d")
                    if new_exp > existing_exp:
                        existing["expiry_date"] = expiry_date
                else:
                    existing["expiry_date"] = expiry_date
            else:
                data["items"].append({
                    "name": item_name,
                    "quantity": quantity,
                    "expiry_date": expiry_date,
                    "added_date": today.strftime("%Y-%m-%d")
                })
            
            results.append({"name": item_name, "status": "added", "expiry": expiry_date})
        else:
            results.append({"name": item_name, "quantity": quantity, "status": "needs_shelf_life"})
    
    data["items"] = sort_items_by_expiry(data["items"])
    save_fridge_data(data)
    return jsonify({"results": results})


if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    print("\n🧊 Fridgic Web Server")
    print("=" * 40)
    print("Open on your phone: http://YOUR_IP:5000")
    print("=" * 40 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)