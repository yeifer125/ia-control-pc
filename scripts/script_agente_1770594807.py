import tkinter as tk
import random

def jugar():
    usuario = var.get()
    computadora = random.choice(['piedra', 'papel', 'tijera'])
    if usuario == computadora:
        resultado = "Empate"
    elif (usuario == 'piedra' and computadora == 'tijera') or (usuario == 'papel' and computadora == 'piedra') or (usuario == 'tijera' and computadora == 'papel'):
        resultado = "Ganaste"
    else:
        resultado = "Perdiste"
    label_resultado.config(text=f"Resultado: {resultado}")

ventana = tk.Tk()
ventana.title("Piedra, Papel o Tijera")

var = tk.StringVar()
radios = tk.Radiobutton(ventana, text="Piedra", variable=var, value="piedra", command=jugar)
radios.pack()
radios = tk.Radiobutton(ventana, text="Papel", variable=var, value="papel", command=jugar)
radios.pack()
radios = tk.Radiobutton(ventana, text="Tijera", variable=var, value="tijera", command=jugar)
radios.pack()

label_resultado = tk.Label(ventana, text="")
label_resultado.pack()

ventana.mainloop()