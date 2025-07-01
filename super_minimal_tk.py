import tkinter as tk

root = tk.Tk()
root.configure(bg="white")
tk.Label(root, text="Test Label", bg="white", fg="black").pack(pady=10)
entry = tk.Entry(root, bg="white", fg="black")
entry.pack(pady=10)
tk.Button(root, text="Test Button", bg="white", fg="black").pack(pady=10)
root.mainloop()