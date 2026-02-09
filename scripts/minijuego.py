import random

choices = ["rock", "paper", "scissors"]
user_score = 0
computer_score = 0

while True:
    user_choice = input("Ingresa tu elección (rock, paper, scissors): ").lower()
    if user_choice not in choices:
        print("Opción inválida. Intenta de nuevo.")
        continue

    computer_choice = random.choice(choices)
    print(f"Computadora eligió: {computer_choice}")

    if user_choice == computer_choice:
        print("Empate!")
    elif ((user_choice == "rock" and computer_choice == "scissors") or 
         (user_choice == "scissors" and computer_choice == "paper") or 
         (user_choice == "paper" and computer_choice == "rock")):
        print("¡Ganaste!")
        user_score += 1
    else:
        print("Perdiste")
        computer_score += 1

    print(f"Puntaje: Tú {user_score} - Computadora {computer_score}")
    play_again = input("¿Jugar otra ronda? (s/n): ").lower()
    if play_again != "s":
        break

print(f"Juego terminado. Puntaje final: Tú {user_score} - Computadora {computer_score}")