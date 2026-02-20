import anthropic
import base64
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Load your API key from .env file
load_dotenv()

# Initialize the Anthropic client
client = anthropic.Anthropic()

# File to store fridge data
DATA_FILE = "fridge_data.json"


def load_fridge_data():
    """Load existing fridge data from JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"items": []}


def save_fridge_data(data):
    """Save fridge data to JSON file."""
    with open(DATA_FILE, "w") as f:
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
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": image_data},
                    },
                    {
                        "type": "text",
                        "text": """Analyze this fridge image and list all food items you can see.
Return ONLY a JSON array of items, like this:
["milk", "eggs", "butter", "leftover pizza"]
Be specific but concise. Just the JSON array, nothing else."""
                    }
                ],
            }
        ],
    )
    
    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1].rsplit("```", 1)[0]
    
    items = json.loads(response_text)
    return items


class FridgeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧊 Fridge Tracker")
        self.root.geometry("650x550")
        
        self.data = load_fridge_data()
        
        self.setup_ui()
        self.refresh_list()
        
        # Check for expiring items on startup
        self.root.after(500, self.check_expiring_on_startup)
    
    def setup_ui(self):
        # Title
        title = tk.Label(self.root, text="🧊 Fridge Tracker", font=("Arial", 20, "bold"))
        title.pack(pady=10)
        
        # Top buttons frame
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        scan_btn = tk.Button(btn_frame, text="📷 Scan Photo", command=self.scan_photo, font=("Arial", 11), bg="#4CAF50", fg="white", padx=15, pady=8)
        scan_btn.pack(side=tk.LEFT, padx=5)
        
        add_btn = tk.Button(btn_frame, text="➕ Add Item", command=self.add_item_dialog, font=("Arial", 11), bg="#2196F3", fg="white", padx=15, pady=8)
        add_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = tk.Button(btn_frame, text="🗑️ Delete Selected", command=self.delete_selected, font=("Arial", 11), bg="#f44336", fg="white", padx=15, pady=8)
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(btn_frame, text="🗑️ Clear All", command=self.clear_all, font=("Arial", 11), padx=15, pady=8)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Items list with scrollbar
        list_frame = tk.Frame(self.root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        columns = ("Item", "Expiry Date", "Status")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("Item", text="Item")
        self.tree.heading("Expiry Date", text="Expiry Date")
        self.tree.heading("Status", text="Status")
        
        self.tree.column("Item", width=220)
        self.tree.column("Expiry Date", width=150)
        self.tree.column("Status", width=180)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double-click to edit expiry
        self.tree.bind("<Double-1>", self.edit_expiry)
        
        # Instructions
        instructions = tk.Label(self.root, text="💡 Double-click an item to edit its expiry date", font=("Arial", 10), fg="gray")
        instructions.pack(pady=5)
    
    def check_expiring_on_startup(self):
        """Show warning popup if items are expiring today or tomorrow."""
        today = datetime.now().date()
        expiring_today = []
        expiring_tomorrow = []
        expired = []
        
        for item in self.data["items"]:
            expiry = item.get("expiry_date")
            if expiry:
                expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
                days_left = (expiry_date - today).days
                
                if days_left < 0:
                    expired.append(item["name"])
                elif days_left == 0:
                    expiring_today.append(item["name"])
                elif days_left == 1:
                    expiring_tomorrow.append(item["name"])
        
        # Build warning message
        warnings = []
        if expired:
            warnings.append(f"⚠️ EXPIRED:\n  • " + "\n  • ".join(expired))
        if expiring_today:
            warnings.append(f"🔴 Expiring TODAY:\n  • " + "\n  • ".join(expiring_today))
        if expiring_tomorrow:
            warnings.append(f"🟡 Expiring TOMORROW:\n  • " + "\n  • ".join(expiring_tomorrow))
        
        if warnings:
            message = "\n\n".join(warnings)
            messagebox.showwarning("⚠️ Food Expiry Alert!", message)
    
    def sort_items_by_expiry(self):
        """Sort items by expiry date (soonest first, no date at end)."""
        today = datetime.now().date()
        
        def sort_key(item):
            expiry = item.get("expiry_date")
            if expiry:
                expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
                return (0, expiry_date)  # Has date: sort by date
            return (1, today)  # No date: put at end
        
        self.data["items"].sort(key=sort_key)
        save_fridge_data(self.data)
    
    def add_item_dialog(self):
        """Open dialog to manually add an item."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Item")
        dialog.geometry("350x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.lift()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))
        
        # Item name
        tk.Label(dialog, text="Item name:", font=("Arial", 11)).pack(pady=(15, 5))
        name_entry = tk.Entry(dialog, font=("Arial", 12), width=25)
        name_entry.pack()
        name_entry.focus()
        
        # Expiry date
        tk.Label(dialog, text="Expiry date (YYYY-MM-DD):", font=("Arial", 11)).pack(pady=(15, 5))
        date_entry = tk.Entry(dialog, font=("Arial", 12), width=25)
        date_entry.pack()
        
        tk.Label(dialog, text="(Leave empty if unknown)", font=("Arial", 9), fg="gray").pack()
        
        def save_item():
            name = name_entry.get().strip()
            date_str = date_entry.get().strip()
            
            if not name:
                messagebox.showerror("Error", "Please enter an item name")
                return
            
            expiry = None
            if date_str:
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                    expiry = date_str
                except ValueError:
                    messagebox.showerror("Invalid Date", "Please use YYYY-MM-DD format")
                    return
            
            # Add item
            self.data["items"].append({
                "name": name,
                "expiry_date": expiry,
                "added_date": datetime.now().strftime("%Y-%m-%d")
            })
            
            self.sort_items_by_expiry()
            self.refresh_list()
            dialog.destroy()
        
        tk.Button(dialog, text="Add Item", command=save_item, font=("Arial", 11), bg="#4CAF50", fg="white", padx=20, pady=5).pack(pady=15)
    
    def delete_selected(self):
        """Delete the selected item from the list."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select an item to delete")
            return
        
        item_values = self.tree.item(selection[0])["values"]
        item_name = item_values[0]
        
        if messagebox.askyesno("Confirm Delete", f"Delete '{item_name}' from your fridge?"):
            # Remove item from data
            self.data["items"] = [i for i in self.data["items"] if i["name"] != item_name]
            save_fridge_data(self.data)
            self.refresh_list()
    
    def scan_photo(self):
        """Open file dialog and analyze selected photo."""
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
        """Update the displayed list."""
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        today = datetime.now().date()
        
        for item in self.data["items"]:
            expiry = item.get("expiry_date")
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
            
            self.tree.insert("", tk.END, values=(item["name"], expiry or "Not set", status), tags=(tag,))
        
        self.tree.tag_configure("expired", background="#ffcccc")
        self.tree.tag_configure("today", background="#ffdddd")
        self.tree.tag_configure("soon", background="#fff3cd")
        self.tree.tag_configure("ok", background="#d4edda")
    
    def edit_expiry(self, event):
        """Edit expiry date for selected item."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item_values = self.tree.item(selection[0])["values"]
        item_name = item_values[0]
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Set Expiry: {item_name}")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.lift()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))
        
        tk.Label(dialog, text=f"Enter expiry date for {item_name}:", font=("Arial", 11)).pack(pady=10)
        tk.Label(dialog, text="Format: YYYY-MM-DD (e.g., 2026-02-25)", font=("Arial", 9), fg="gray").pack()
        
        entry = tk.Entry(dialog, font=("Arial", 12), width=15)
        entry.pack(pady=10)
        entry.focus()
        
        def save_date():
            date_str = entry.get().strip()
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                for item in self.data["items"]:
                    if item["name"] == item_name:
                        item["expiry_date"] = date_str
                        break
                self.sort_items_by_expiry()
                self.refresh_list()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Invalid Date", "Please use YYYY-MM-DD format")
        
        tk.Button(dialog, text="Save", command=save_date, font=("Arial", 11), bg="#4CAF50", fg="white").pack(pady=10)
    
    def clear_all(self):
        """Clear all items."""
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