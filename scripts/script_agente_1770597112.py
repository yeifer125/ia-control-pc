import tkinter as tk
import re

contacts = {}
def validate_email(email):
    pattern = r'^[\w\.-]+@[^\s]+\.\w+$'
    return re.match(pattern, email) is not None

def add_contact():
    name = entry_name.get()
    email = entry_email.get()
    if not name or not email:
        tk.messagebox.showerror("Error", "Name and email are required")
        return
    if name in contacts:
        tk.messagebox.showerror("Error", "Name already exists")
        return
    if not validate_email(email):
        tk.messagebox.showerror("Error", "Invalid email format")
        return
    contacts[name] = email
    tk.messagebox.showinfo("Success", "Contact added")

def search_contact():
    name = entry_name.get()
    if name in contacts:
        tk.messagebox.showinfo("Result", f"Email: {contacts[name]}")
    else:
        tk.messagebox.showinfo("Result", "Contact not found")

def delete_contact():
    name = entry_name.get()
    if name in contacts:
        del contacts[name]
        tk.messagebox.showinfo("Success", "Contact deleted")
    else:
        tk.messagebox.showinfo("Result", "Contact not found")

root = tk.Tk()
root.title("Contact Manager")

label_name = tk.Label(root, text="Name:")
label_email = tk.Label(root, text="Email:")
entry_name = tk.Entry(root)
entry_email = tk.Entry(root)

button_add = tk.Button(root, text="Add", command=add_contact)
button_search = tk.Button(root, text="Search", command=search_contact)
button_delete = tk.Button(root, text="Delete", command=delete_contact)

label_name.grid(row=0)
label_email.grid(row=1)
entry_name.grid(row=0, column=1)
entry_email.grid(row=1, column=1)
button_add.grid(row=2, column=0)
button_search.grid(row=2, column=1)
button_delete.grid(row=2, column=2)

root.mainloop()