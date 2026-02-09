import re

contacts = {}

def validate_email(email):
    pattern = r'^[\w\.\-]+@\w+\.\w+$'
    return bool(re.match(pattern, email))

def add_contact(name, phone, email):
    if name in contacts:
        print("Error: Nombre ya existe")
        return
    if not validate_email(email):
        print("Error: Formato de email inválido")
        return
    contacts[name] = {"phone": phone, "email": email}

def search_contact(name):
    if name in contacts:
        print(f"Contacto encontrado: {contacts[name]}")
    else:
        print("Contacto no encontrado")

def delete_contact(name):
    if name in contacts:
        del contacts[name]
        print("Contacto eliminado")
    else:
        print("Contacto no encontrado")

# Menú principal
while True:
    print(\n"Mini Agenda de Contactos")
    print("1. Agregar contacto")
    print("2. Buscar contacto")
    print("3. Eliminar contacto")
    print("4. Salir")
    choice = input("Seleccione una opción: ")
    if choice == '1':
        name = input("Nombre: ")
        phone = input("Teléfono: ")
        email = input("Email: ")
        add_contact(name, phone, email)
    elif choice == '2':
        name = input("Nombre a buscar: ")
        search_contact(name)
    elif choice == '3':
        name = input("Nombre a eliminar: ")
        delete_contact(name)
    elif choice == '4':
        break
    else:
        print("Opción no válida")