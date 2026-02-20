import tkinter as tk

print("Starting window...")

root = tk.Tk()
root.title("Test Window")
root.geometry("300x200")

# Force the window to appear on top
root.lift()
root.attributes('-topmost', True)
root.after(100, lambda: root.attributes('-topmost', False))
root.focus_force()

label = tk.Label(root, text="If you see this, tkinter works!", font=("Arial", 14))
label.pack(pady=50)

print("Window should be visible now!")
print("Close the window to end the program.")

root.mainloop()

print("Window closed.")