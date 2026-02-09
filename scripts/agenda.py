import re

# Diccionario principal de contactos
agenda = {}

# Función para validar email
def validar_email(email):
    # Patrón simple: texto@texto.texto
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(patron, email) is not None

# Agregar contacto
def agregar_contacto(nombre, telefono, email):
    if nombre in agenda:
        print(f"⚠️ El contacto '{nombre}' ya existe.")
        return
    
    if not validar_email(email):
        print("❌ Formato de email inválido.")
        return
    
    agenda[nombre] = {"telefono": telefono, "email": email}
    print(f"✅ Contacto '{nombre}' agregado.")

# Buscar contacto
def buscar_contacto(nombre):
    try:
        contacto = agenda[nombre]
        print(f"🔍 {nombre}: Tel: {contacto['telefono']}, Email: {contacto['email']}")
    except KeyError:
        print(f"❌ No se encontró el contacto '{nombre}'.")

# Eliminar contacto
def eliminar_contacto(nombre):
    try:
        del agenda[nombre]
        print(f"🗑️ Contacto '{nombre}' eliminado.")
    except KeyError:
        print(f"❌ No se encontró el contacto '{nombre}'.")

# Menú simple
def menu():
    while True:
        print("\n--- Mini Agenda ---")
        print("1. Agregar contacto")
        print("2. Buscar contacto")
        print("3. Eliminar contacto")
        print("4. Mostrar todos")
        print("5. Salir")
        opcion = input("Elige una opción: ")

        if opcion == "1":
            nombre = input("Nombre: ")
            telefono = input("Teléfono: ")
            email = input("Email: ")
            agregar_contacto(nombre, telefono, email)
        elif opcion == "2":
            nombre = input("Nombre a buscar: ")
            buscar_contacto(nombre)
        elif opcion == "3":
            nombre = input("Nombre a eliminar: ")
            eliminar_contacto(nombre)
        elif opcion == "4":
            if agenda:
                print("\n📋 Lista de contactos:")
                for nombre, datos in agenda.items():
                    print(f"{nombre}: Tel: {datos['telefono']}, Email: {datos['email']}")
            else:
                print("No hay contactos.")
        elif opcion == "5":
            print("👋 ¡Adiós!")
            break
        else:
            print("❌ Opción inválida. Intenta de nuevo.")

# Ejecutar el menú
if __name__ == "__main__":
    menu()
