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
        print(f"Contacto encontrado: {name}, Teléfono: {contacts[name]["phone"]}, Email: {contacts[name]["email"]}")
    else:
        print("Contacto no encontrado.")

def delete_contact():
    name = input("Nombre a eliminar: ")
    if name in contacts:
        del contacts[name]
        print(f"Contacto {name} eliminado.")
    else:
        print("Contacto no encontrado.")

while True:
    print(\nMenú:\n1. Agregar contacto\n2. Buscar contacto\n3. Eliminar contacto\n4. Salir\n)
    choice = input("Seleccione una opción: ")
    if choice == "1":
        add_contact()
    elif choice == "2":
        search_contact()
    elif choice == "3":
        delete_contact()
    elif choice == "4":
        break
    else:
        print("Opción inválida.")