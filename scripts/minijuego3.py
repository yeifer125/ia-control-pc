import tkinter as tk
import random

root = tk.Tk()
root.title("Piedra, Papel, Tijera")

def play_game(choice):
    computer_choice = random.choice(['rock', 'paper', 'scissors'])
    result = f"Usuario: {choice}, Computadora: {computer_choice}"
    label.config(text=result)

label = tk.Label(root, text="")
label.pack()

button_rock = tk.Button(root, text="Piedra", command=lambda: play_game("rock"))
button_paper = tk.Button(root, text="Papel", command=lambda: play_game("paper"))
button_scissors = tk.Button(root, text="Tijera", command=lambda: play_game("scissors"))

button_rock.pack()
button_paper.pack()
button_scissors.pack()

root.mainloop()