import tkinter as tk

class Calculator:
    def __init__(self, master):
        self.master = master
        self.master.title("Pro Calculator")
        self.entry = tk.Entry(master, width=20, font=('Arial', 14))
        self.entry.grid(row=0, column=0, columnspan=4)
        
        self.buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            '0', '.', '=', '+'
        ]
        
        row = 1
        col = 0
        for button in self.buttons:
            btn = tk.Button(master, text=button, width=5, height=2, command=lambda x=button: self.button_click(x))
            btn.grid(row=row, column=col)
            col += 1
            if col == 4:
                col = 0
                row += 1

    def button_click(self, char):
        if char == '=':
            try:
                result = eval(self.entry.get())
                self.entry.delete(0, tk.END)
                self.entry.insert(0, str(result))
            except:
                pass
        else:
            self.entry.insert(tk.END, char)

if __name__ == "__main__":
    root = tk.Tk()
    app = Calculator(root)
    root.mainloop()