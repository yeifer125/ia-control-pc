import tkinter as tk
import random

class RockPaperScissors:
    def __init__(self, root):
        self.root = root
        self.root.title("Piedra, Papel o Tijera")
        self.user_score = 0
        self.computer_score = 0

        self.result_label = tk.Label(root, text="")
        self.result_label.pack()

        self.button_rock = tk.Button(root, text="Piedra", command=lambda: self.play("piedra")
        self.button_paper = tk.Button(root, text="Papel", command=lambda: self.play("papel")
        self.button_scissors = tk.Button(root, text="Tijera", command=lambda: self.play("tijera")

        self.button_rock.pack()
        self.button_paper.pack()
        self.button_scissors.pack()

    def play(self, user_choice):
        computer_choice = random.choice(["piedra", "papel", "tijera"])
        self.result_label.config(text=f"Tu elección: {user_choice}\nOpción del ordenador: {computer_choice}")

        if user_choice == computer_choice:
            self.result_label.config(text="Empate!")
        elif (user_choice == "piedra" and computer_choice == "tijera") or (user_choice == "tijera" and computer_choice == "papel") or (user_choice == "papel" and computer_choice == "piedra"):
            self.user_score += 1
            self.result_label.config(text=f"¡Ganaste! Tu puntuación: {self.user_score}")
        else:
            self.computer_score += 1
            self.result_label.config(text=f"Perdiste. Puntuación del ordenador: {self.computer_score}")

if __name__ == "__main__":
    root = tk.Tk()
    game = RockPaperScissors(root)
    root.mainloop()