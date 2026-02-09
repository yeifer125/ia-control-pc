import random

while True:
    target = random.randint(1, 50)
    attempts = 0
    while attempts < 7:
        try:
            guess = int(input(f"Adivina el número (1-50): "))
            attempts += 1
            if guess == target:
                print(f"¡Ganaste en {attempts} intentos!")
                break
            elif guess > target:
                print("Muy alto")
            else:
                print("Muy bajo")
        except ValueError:
            print("Por favor, ingresa un número válido.")
    else:
        print(f"El número era {target}. Has perdido.")
    restart = input("¿Quieres jugar de nuevo? (s/n): ").lower()
    if restart != 's':
        break