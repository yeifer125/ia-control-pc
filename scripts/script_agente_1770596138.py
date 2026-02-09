import re

def validar_email(email):
    patron = r'^[\w\.\-]+@[\w\.\-]+\.\w+$'
    return bool(re.match(patron, email))

contactos = {}

while True:
    print("\n--- Agenda de Contactos ---")
    print("1. Agregar contacto")
    print("2. Buscar contacto")
    print("3. Eliminar contacto")
    print("4. Salir")

    opcion = input("Seleccione una opción: ")

    if opcion == '1':
        nombre = input("Nombre: ")
        email = input("Email: ")
        if validar_email(email):
            contactos[nombre] = email
            print(f"Contacto {nombre} agregado exitosamente.")
        else:
            print("Email inválido. Por favor, ingrese un email válido.")

    elif opcion == '2':
        nombre = input("Nombre a buscar: ")
        if nombre in contactos:
            print(f"{nombre}: {contactos[nombre]}")
        else:
            print(f"El contacto {nombre} no existe en la agenda.")

    elif opcion == '3':
        nombre = input("Nombre a eliminar: ")
        if nombre in contactos:
            del contactos[nombre]
            print(f"Contacto {nombre} eliminado exitosamente.")
        else:
            print(f"El contacto {nombre} no existe en la agenda.")

    elif opcion == '4':
        print("Saliendo del programa...")
        break

    else:
        print("Opción no válida. Por favor, seleccione una opción válida.")