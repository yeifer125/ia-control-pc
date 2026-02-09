import re

contacts = {}
def validate_email(email):
    regex = r'^[\w\.\-]+@[\w\.\-]+\.\w+$'
    return bool(re.match(regex, email))

def add_contact():
    name = input("Nombre: ")
    phone = input("Teléfono: ")
    email = input("Email: ")
    if name in contacts:
        print("Error: Nombre ya existe.")
        return
    if not validate_email(email):
        print("Error: Email inválido.")
        return
    contacts[name] = {"phone": phone, "email": email}
def search_contact():
    name = input("Nombre a buscar: ")
    if name in contacts:
        print(f"Contacto encontrado: {name}, Teléfono: {contacts[name]['phone']}, Email: {contacts[name]['email']}")
    else:
        print(f"El contacto {name} no existe en la agenda.")
def delete_contact():
    name = input("Nombre a eliminar: ")
    if name in contacts:
        del contacts[name]
        print(f"Contacto {name} eliminado exitosamente.")
    else:
        print(f"El contacto {name} no existe en la agenda.")

while True:
    print("\n--- Agenda de Contactos ---")
    print("1. Agregar contacto")
    print("2. Buscar contacto")
    print("3. Eliminar contacto")
    print("4. Salir")

    opcion = input("Seleccione una opción: ")

    if opcion == '1':
        add_contact()
    elif opcion == '2':
        search_contact()
    elif opcion == '3':
        delete_contact()
    elif opcion == '4':
        print("Saliendo del programa...")
        break
    else:
        print("Opción no válida. Por favor, seleccione una opción válida.")