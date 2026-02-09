print("Calculadora")
num1 = float(input("Ingrese el primer número: "))
num2 = float(input("Ingrese el segundo número: "))
operacion = input("Ingrese la operación (+, -, *, /): ")
if operacion == '+':
    print(f"Resultado: {num1 + num2}")
elif operacion == '-':
    print(f"Resultado: {num1 - num2}")
elif operacion == '*':
    print(f"Resultado: {num1 * num2}")
elif operacion == '/':
    print(f"Resultado: {num1 / num2}")
else:
    print("Operación no válida")