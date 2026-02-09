import tkinter as tk

class PacmanGame:
    def __init__(self):
        self.root = tk.Tk()
        self.canvas = tk.Canvas(self.root, width=400, height=400)
        self.canvas.pack()
        self.pacman = self.canvas.create_oval(150, 150, 250, 250, fill='yellow')
        self.root.bind('<Key>', self.move)
        self.root.mainloop()

    def move(self, event):
        if event.keysym == 'Up':
            self.canvas.move(self.pacman, 0, -10)
        elif event.keysym == 'Down':
            self.canvas.move(self.pacman, 0, 10)

pacman_game = PacmanGame()