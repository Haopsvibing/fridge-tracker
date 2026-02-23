import anthropic
import base64
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Load your API key from .env file
load_dotenv()

# Initialize the Anthropic client
client = anthropic.Anthropic()

# Files to store data
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
    """Load historical shelf life data."""
    if os.path.exists(SHELF_LIFE_FILE):
        with open(SHELF_LIFE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_shelf_life_data(data):
    """Save shelf life data."""
    with open(SHELF_LIFE_FILE, "w") as f:
        json.dump(data, f, indent=4)


def analyze_fridge_image(image_path):
    """Send image to Claude and get list of food items."""
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")
    
    ext = image_path.lower().split(".")[-1]
    media_types = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}
    media_type = media_types.get(ext, "image/jpeg")
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                    {"type": "text", "text": """Analyze this fridge image and list all food items you can see.
Return ONLY a JSON array of items, like this:
["milk", "eggs", "butter", "leftover pizza"]
Be specific but concise. Just the JSON array, nothing else."""}
                ],
            }
        ],
    )
    
    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(response_text)


def analyze_receipt_image(image_path):
    """Send receipt image to Claude and get list of purchased items."""
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")
    
    ext = image_path.lower().split(".")[-1]
    media_types = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}
    media_type = media_types.get(ext, "image/jpeg")
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
                    {"type": "text", "text": """Analyze this grocery receipt and list all FOOD items purchased.
Ignore non-food items like bags, cleaning supplies, etc.
Simplify names to basic food items (e.g., "VALIO MILK 1L" → "milk").

Return ONLY a JSON array with item name and quantity, like this:
[{"name": "milk", "quantity": 2}, {"name": "eggs", "quantity": 1}, {"name": "bread", "quantity": 1}]

Just the JSON array, nothing else."""}
                ],
            }
        ],
    )
    
    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(response_text)


class FridgeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧊 Fridge Tracker")
        self.root.geometry("700x600")
        
        self.data = load_fridge_data()
        self.shelf_life_data = load_shelf_life_data()
        
        self.setup_ui()
        self.refresh_list()
        self.root.after(500, self.check_expiring_on_startup)
    
    def setup_ui(self):
        title = tk.Label(self.root, text="🧊 Fridge Tracker", font=("Arial", 20, "bold"))
        title.pack(pady=10)
        
        # Top buttons frame - row 1
        btn_frame1 = tk.Frame(self.root)
        btn_frame1.pack(pady=5)
        
        scan_btn = tk.Button(btn_frame1, text="📷 Scan Fridge", command=self.scan_photo, font=("Arial", 11), bg="#4CAF50", fg="white", padx=12, pady=8)
        scan_btn.pack(side=tk.LEFT, padx=5)
        
        receipt_btn = tk.Button(btn_frame1, text="🧾 Scan Receipt", command=self.scan_receipt, font=("Arial", 11), bg="#FF9800", fg="white", padx=12, pady=8)
        receipt_btn.pack(side=tk.LEFT, padx=5)
        
        add_btn = tk.Button(btn_frame1, text="➕ Add Item", command=self.add_item_dialog, font=("Arial", 11), bg="#2196F3", fg="white", padx=12, pady=8)
        add_btn.pack(side=tk.LEFT, padx=5)
        
        # Top buttons frame - row 2
        btn_frame2 = tk.Frame(self.root)
        btn_frame2.pack(pady=5)
        
        delete_btn = tk.Button(btn_frame2, text="🗑️ Delete Selected", command=self.delete_selected, font=("Arial", 11), bg="#f44336", fg="white", padx=12, pady=8)
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(btn_frame2, text="🗑️ Clear All", command=self.clear_all, font=("Arial", 11), padx=12, pady=8)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Items list
        list_frame = tk.Frame(self.root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        columns = ("Item", "Quantity", "Expiry Date", "Status")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("Item", text="Item")
        self.tree.heading("Quantity", text="Qty")
        self.tree.heading("Expiry Date", text="Expiry Date")
        self.tree.heading("Status", text="Status")
        
        self.tree.column("Item", width=200)
        self.tree.column("Quantity", width=50)
        self.tree.column("Expiry Date", width=120)
        self.tree.column("Status", width=180)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<Double-1>", self.edit_item)
        
        instructions = tk.Label(self.root, text="💡 Double-click an item to edit expiry date or quantity", font=("Arial", 10), fg="gray")
        instructions.pack(pady=5)
    
    def check_expiring_on_startup(self):
        today = datetime.now().date()
        expiring_today, expiring_tomorrow, expired = [], [], []
        
        for item in self.data["items"]:
            expiry = item.get("expiry_date")
            if expiry:
                expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
                days_left = (expiry_date - today).days
                name = f"{item['name']} (x{item.get('quantity', 1)})"
                
                if days_left < 0:
                    expired.append(name)
                elif days_left == 0:
                    expiring_today.append(name)
                elif days_left == 1:
                    expiring_tomorrow.append(name)
        
        warnings = []
        if expired:
            warnings.append(f"⚠️ EXPIRED:\n  • " + "\n  • ".join(expired))
        if expiring_today:
            warnings.append(f"🔴 Expiring TODAY:\n  • " + "\n  • ".join(expiring_today))
        if expiring_tomorrow:
            warnings.append(f"🟡 Expiring TOMORROW:\n  • " + "\n  • ".join(expiring_tomorrow))
        
        if warnings:
            messagebox.showwarning("⚠️ Food Expiry Alert!", "\n\n".join(warnings))
    
    def sort_items_by_expiry(self):
        today = datetime.now().date()
        def sort_key(item):
            expiry = item.get("expiry_date")
            if expiry:
                return (0, datetime.strptime(expiry, "%Y-%m-%d").date())
            return (1, today)
        self.data["items"].sort(key=sort_key)
        save_fridge_data(self.data)
    
    def get_shelf_life_days(self, item_name):
        """Get stored shelf life for an item (returns None if unknown)."""
        key = item_name.lower().strip()
        return self.shelf_life_data.get(key)
    
    def save_shelf_life(self, item_name, days):
        """Save shelf life for an item."""
        key = item_name.lower().strip()
        self.shelf_life_data[key] = days
        save_shelf_life_data(self.shelf_life_data)
    
    def ask_shelf_life(self, item_name, callback):
        """Dialog to ask user for shelf life of a new item."""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"New Item: {item_name}")
        dialog.geometry("350x180")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.lift()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))
        
        tk.Label(dialog, text=f"How many days does '{item_name}' typically last?", font=("Arial", 11), wraplength=300).pack(pady=(20, 10))
        
        tk.Label(dialog, text="Days until expiry:", font=("Arial", 10)).pack()
        
        days_entry = tk.Entry(dialog, font=("Arial", 12), width=10)
        days_entry.pack(pady=10)
        days_entry.focus()
        
        def save():
            try:
                days = int(days_entry.get().strip())
                if days < 1:
                    raise ValueError()
                self.save_shelf_life(item_name, days)
                dialog.destroy()
                callback(days)
            except ValueError:
                messagebox.showerror("Invalid", "Please enter a positive number")
        
        tk.Button(dialog, text="Save", command=save, font=("Arial", 11), bg="#4CAF50", fg="white", padx=20).pack(pady=10)
        
        dialog.wait_window()
    
    def scan_receipt(self):
        """Scan a receipt and add items with smart expiry dates."""
        file_path = filedialog.askopenfilename(
            title="Select Receipt Photo",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.webp")]
        )
        
        if not file_path:
            return
        
        self.root.config(cursor="wait")
        self.root.update()
        
        try:
            items = analyze_receipt_image(file_path)
            self.root.config(cursor="")
            self.process_receipt_items(items)
        except Exception as e:
            self.root.config(cursor="")
            messagebox.showerror("Error", f"Failed to analyze receipt: {str(e)}")
    
    def process_receipt_items(self, items, index=0):
        """Process receipt items one by one, asking for shelf life if needed."""
        if index >= len(items):
            self.sort_items_by_expiry()
            self.refresh_list()
            messagebox.showinfo("Done!", f"Added/updated {len(items)} items from receipt!")
            return
        
        item = items[index]
        item_name = item["name"]
        quantity = item.get("quantity", 1)
        today = datetime.now()
        
        # Check if we know the shelf life
        shelf_life = self.get_shelf_life_days(item_name)
        
        def add_item_with_days(days):
            expiry_date = (today + timedelta(days=days)).strftime("%Y-%m-%d")
            
            # Check if item already exists in fridge
            existing = None
            for i in self.data["items"]:
                if i["name"].lower() == item_name.lower():
                    existing = i
                    break
            
            if existing:
                # Update quantity and expiry
                existing["quantity"] = existing.get("quantity", 1) + quantity
                # Use the later expiry date
                if existing.get("expiry_date"):
                    existing_expiry = datetime.strptime(existing["expiry_date"], "%Y-%m-%d")
                    new_expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
                    if new_expiry > existing_expiry:
                        existing["expiry_date"] = expiry_date
                else:
                    existing["expiry_date"] = expiry_date
            else:
                # Add new item
                self.data["items"].append({
                    "name": item_name,
                    "quantity": quantity,
                    "expiry_date": expiry_date,
                    "added_date": today.strftime("%Y-%m-%d")
                })
            
            save_fridge_data(self.data)
            # Process next item
            self.process_receipt_items(items, index + 1)
        
        if shelf_life:
            # Known item - auto-add
            add_item_with_days(shelf_life)
        else:
            # Unknown item - ask user
            self.ask_shelf_life(item_name, add_item_with_days)
    
    def add_item_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Item")
        dialog.geometry("350x280")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.lift()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))
        
        tk.Label(dialog, text="Item name:", font=("Arial", 11)).pack(pady=(15, 5))
        name_entry = tk.Entry(dialog, font=("Arial", 12), width=25)
        name_entry.pack()
        name_entry.focus()
        
        tk.Label(dialog, text="Quantity:", font=("Arial", 11)).pack(pady=(10, 5))
        qty_entry = tk.Entry(dialog, font=("Arial", 12), width=25)
        qty_entry.insert(0, "1")
        qty_entry.pack()
        
        tk.Label(dialog, text="Expiry date (YYYY-MM-DD):", font=("Arial", 11)).pack(pady=(10, 5))
        date_entry = tk.Entry(dialog, font=("Arial", 12), width=25)
        date_entry.pack()
        tk.Label(dialog, text="(Leave empty if unknown)", font=("Arial", 9), fg="gray").pack()
        
        def save_item():
            name = name_entry.get().strip()
            qty_str = qty_entry.get().strip()
            date_str = date_entry.get().strip()
            
            if not name:
                messagebox.showerror("Error", "Please enter an item name")
                return
            
            try:
                quantity = int(qty_str) if qty_str else 1
            except ValueError:
                messagebox.showerror("Error", "Quantity must be a number")
                return
            
            expiry = None
            if date_str:
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                    expiry = date_str
                except ValueError:
                    messagebox.showerror("Invalid Date", "Please use YYYY-MM-DD format")
                    return
            
            self.data["items"].append({
                "name": name,
                "quantity": quantity,
                "expiry_date": expiry,
                "added_date": datetime.now().strftime("%Y-%m-%d")
            })
            
            self.sort_items_by_expiry()
            self.refresh_list()
            dialog.destroy()
        
        tk.Button(dialog, text="Add Item", command=save_item, font=("Arial", 11), bg="#4CAF50", fg="white", padx=20, pady=5).pack(pady=15)
    
    def delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select an item to delete")
            return
        
        item_values = self.tree.item(selection[0])["values"]
        item_name = item_values[0]
        
        if messagebox.askyesno("Confirm Delete", f"Delete '{item_name}' from your fridge?"):
            self.data["items"] = [i for i in self.data["items"] if i["name"] != item_name]
            save_fridge_data(self.data)
            self.refresh_list()
    
    def scan_photo(self):
        file_path = filedialog.askopenfilename(
            title="Select Fridge Photo",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.webp")]
        )
        
        if not file_path:
            return
        
        self.root.config(cursor="wait")
        self.root.update()
        
        try:
            items = analyze_fridge_image(file_path)
            today = datetime.now().strftime("%Y-%m-%d")
            new_count = 0
            for item in items:
                exists = any(i["name"].lower() == item.lower() for i in self.data["items"])
                if not exists:
                    self.data["items"].append({
                        "name": item,
                        "quantity": 1,
                        "expiry_date": None,
                        "added_date": today
                    })
                    new_count += 1
            
            self.sort_items_by_expiry()
            self.refresh_list()
            messagebox.showinfo("Success", f"Found {len(items)} items, added {new_count} new items!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze image: {str(e)}")
        finally:
            self.root.config(cursor="")
    
    def refresh_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        today = datetime.now().date()
        
        for item in self.data["items"]:
            expiry = item.get("expiry_date")
            quantity = item.get("quantity", 1)
            status = "No date set"
            tag = ""
            
            if expiry:
                expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
                days_left = (expiry_date - today).days
                
                if days_left < 0:
                    status = "⚠️ EXPIRED!"
                    tag = "expired"
                elif days_left == 0:
                    status = "⚠️ Expires TODAY!"
                    tag = "today"
                elif days_left <= 3:
                    status = f"⚡ {days_left} days left"
                    tag = "soon"
                else:
                    status = f"✓ {days_left} days left"
                    tag = "ok"
            
            self.tree.insert("", tk.END, values=(item["name"], quantity, expiry or "Not set", status), tags=(tag,))
        
        self.tree.tag_configure("expired", background="#ffcccc")
        self.tree.tag_configure("today", background="#ffdddd")
        self.tree.tag_configure("soon", background="#fff3cd")
        self.tree.tag_configure("ok", background="#d4edda")
    
    def edit_item(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        
        item_values = self.tree.item(selection[0])["values"]
        item_name = item_values[0]
        current_qty = item_values[1]
        current_expiry = item_values[2] if item_values[2] != "Not set" else ""
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit: {item_name}")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.lift()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))
        
        tk.Label(dialog, text="Quantity:", font=("Arial", 11)).pack(pady=(15, 5))
        qty_entry = tk.Entry(dialog, font=("Arial", 12), width=15)
        qty_entry.insert(0, str(current_qty))
        qty_entry.pack()
        
        tk.Label(dialog, text="Expiry date (YYYY-MM-DD):", font=("Arial", 11)).pack(pady=(15, 5))
        date_entry = tk.Entry(dialog, font=("Arial", 12), width=15)
        date_entry.insert(0, current_expiry)
        date_entry.pack()
        date_entry.focus()
        
        def save():
            qty_str = qty_entry.get().strip()
            date_str = date_entry.get().strip()
            
            try:
                quantity = int(qty_str) if qty_str else 1
            except ValueError:
                messagebox.showerror("Error", "Quantity must be a number")
                return
            
            expiry = None
            if date_str:
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                    expiry = date_str
                except ValueError:
                    messagebox.showerror("Invalid Date", "Please use YYYY-MM-DD format")
                    return
            
            for item in self.data["items"]:
                if item["name"] == item_name:
                    item["quantity"] = quantity
                    item["expiry_date"] = expiry
                    break
            
            self.sort_items_by_expiry()
            self.refresh_list()
            dialog.destroy()
        
        tk.Button(dialog, text="Save", command=save, font=("Arial", 11), bg="#4CAF50", fg="white").pack(pady=15)
    
    def clear_all(self):
        if messagebox.askyesno("Confirm", "Delete all items from your fridge list?"):
            self.data = {"items": []}
            save_fridge_data(self.data)
            self.refresh_list()


if __name__ == "__main__":
    root = tk.Tk()
    root.lift()
    root.attributes('-topmost', True)
    root.after(100, lambda: root.attributes('-topmost', False))
    root.focus_force()
    app = FridgeApp(root)
    root.mainloop()