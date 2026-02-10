import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
try:
    import ollama
except ImportError:
    ollama = None
import json
import subprocess
import time
import os
try:
    import torch
except ImportError:
    torch = None
try:
    import pyautogui
except ImportError:
    pyautogui = None
try:
    import pygetwindow as gw
except ImportError:
    gw = None
try:
    import pyperclip
except ImportError:
    pyperclip = None
import webbrowser
import re
import importlib.util
import sys
import pkgutil
import ast
from queue import Queue, Empty

# =========================
# CONFIG
# =========================
MODEL = "qwen3:4b"
MAX_ITERACIONES = 6
MEMORIA_ARCHIVO = "memoria_agente.txt"
LOG_ARCHIVO = "log_sesion.txt"
MODULOS_ESTANDAR = getattr(sys, "stdlib_module_names", None)
if MODULOS_ESTANDAR is None:
    MODULOS_ESTANDAR = set(sys.builtin_module_names)

if torch and torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

stop_event = threading.Event()
pause_event = threading.Event()
pause_event.set()

# =========================
# PERFILES DE SEGURIDAD
# =========================
PERFILES = {
    "Seguro": {"python": True, "apps": False, "reintentos": False},
    "Dev": {"python": True, "apps": True, "reintentos": True},
    "Libre": {"python": True, "apps": True, "reintentos": True},
}

# =========================
# MEMORIA PERSISTENTE
# =========================
TIPOS_VALIDOS = [
    "OBJETIVO",
    "ERROR",
    "RESULTADO",
    "PERMISOS",
    "CONVERSACION",
    "REGLA",
    "CONCLUSION"
]

def cargar_memoria():
    if os.path.exists(MEMORIA_ARCHIVO):
        with open(MEMORIA_ARCHIVO, "r", encoding="utf-8") as f:
            return f.read().splitlines()
    return []

def guardar_memoria(lineas):
    memoria_por_tipo = {tipo: [] for tipo in TIPOS_VALIDOS}
    for linea in lineas:
        if "=" in linea:
            tipo, contenido = linea.split("=", 1)
            if tipo in TIPOS_VALIDOS:
                memoria_por_tipo[tipo].append(contenido)
    final = []
    for tipo in TIPOS_VALIDOS:
        for contenido in memoria_por_tipo[tipo][-50:]:
            final.append(f"{tipo}={contenido}")
    with open(MEMORIA_ARCHIVO, "w", encoding="utf-8") as f:
        f.write("\n".join(final))

def memorizar(tipo, contenido):
    if tipo not in TIPOS_VALIDOS or not contenido:
        return
    contenido = contenido.strip()
    if len(contenido) < 5:
        return
    memoria = cargar_memoria()
    linea = f"{tipo}={contenido}"
    if linea not in memoria:
        memoria.append(linea)
        guardar_memoria(memoria)

# =========================
# LOG
# =========================
def guardar_log(texto):
    with open(LOG_ARCHIVO, "a", encoding="utf-8") as f:
        f.write(texto + "\n")

# =========================
# GUARDAR SCRIPT
# =========================
def guardar_script(nombre_archivo, codigo):
    carpeta = "scripts"
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    ruta = os.path.join(carpeta, nombre_archivo)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(codigo)
    return ruta

# =========================
# PROMPT BASE
# =========================
SYSTEM_PROMPT = """
Eres un agente autonomo ejecutandose en WINDOWS.
REGLAS:
- Si la accion requiere comandos de Windows (cmd, powershell, exe) -> action = "windows_shell"
- Si la accion requiere comandos Linux -> action = "wsl_shell"
- Nunca mezcles sintaxis Windows y Linux en la misma accion
- No asumas que Linux existe fuera de WSL
- Si action = "none", usa el campo "code" para responder al usuario en lenguaje natural, no para ejecutar codigo.
- Si action = "none" y es conversacion, el campo "code" DEBE contener la respuesta al usuario en lenguaje natural.
- si ERROR se repite -> cambiar estrategia
- Usa la MEMORIA si existe informacion previa util
- No inventes rutas ni metodos que no existan realmente
- No marques objetivo completado sin ejecutar codigo real
- Si solo es conversacion -> action = "none"
- Si requiere accion real -> action = "python"
- Guarda solo reglas, conclusiones o patrones reutilizables
- Usa formato: "RULE: cuando X ocurre -> hacer Y"
- No guardes flags genericos ni estados temporales
- 'requests' es una libreria de Python, no un programa ejecutable
- No se puede ejecutar escribiendo 'requests' en PowerShell
- Para usarla, primero se importa en Python: 'import requests'
- Se puede usar en scripts Python (.py) o en la consola interactiva de Python
- Esto aplica igual a otras librerias de Python como 'pandas', 'numpy', etc.

RAZONAMIENTO:
- Antes de ejecutar codigo, valida mentalmente que la API, comando o metodo que planeas usar EXISTE y es utilizable en este entorno.
- Distingue entre tres estados: EJECUTABLE, INDETERMINADO (faltan datos), o IMPOSIBLE (la capacidad no existe).
- Si el objetivo es IMPOSIBLE o INDETERMINADO, explica brevemente por que y usa action = "none".
- No confundas "avanzar" con "ejecutar"; pensar tambien es progreso.
- Si ocurre un error, identifica la causa raiz antes de intentar corregirlo.

Responde SOLO en JSON:
{
  "thought": "razonamiento corto y claro",
  "action": "python | windows_shell | wsl_shell | none",
  "code": "",
  "goal_done": false,
  "memory": ""
}
"""

# =========================
# UI
# =========================
ui_queue = Queue()

def _log_chat_ui(t):
    chat.config(state="normal")
    chat.insert(tk.END, t + "\n")
    chat.see(tk.END)
    chat.config(state="disabled")

def _log_estado_ui(linea):
    estado.config(state="normal")
    estado.insert(tk.END, linea + "\n")
    estado.see(tk.END)
    estado.config(state="disabled")

def log_chat(t):
    ui_queue.put(("chat", t))
    guardar_log(t)

def log_estado(t):
    linea = f"[IA@local] > {t}"
    ui_queue.put(("estado", linea))
    guardar_log(linea)

def set_estado(t):
    estado_actual.set(t)

# =========================
# BURBUJA FLOTANTE
# =========================
log_flotante = None
def log_flotante_insert(msg):
    if log_flotante:
        ui_queue.put(("flotante", msg))
    log_chat(msg)

# =========================
# IA
# =========================
def llamar_ia(historial, memoria, permisos):
    log_estado("Pensando...")
    if not ollama:
        return json.dumps({
            "thought": "ollama no esta disponible",
            "action": "none",
            "code": "ollama no esta instalado. Instala el modulo para continuar.",
            "goal_done": True,
            "memory": ""
        })
    memoria_texto = "\n".join(
        m for m in memoria if m.startswith("CONCLUSION=")
    )
    contexto = SYSTEM_PROMPT + "\nMEMORIA:\n" + memoria_texto + f"\nPERMISOS: {permisos}\n" + "\n".join(historial)
    return ollama.generate(model=MODEL, prompt=contexto)["response"]

# =========================
# EJECUCIÓN INTELIGENTE
# =========================
def modulo_existe(modulo):
    """Verifica si un módulo de Python está instalado y accesible"""
    return importlib.util.find_spec(modulo) is not None

def asegurar_pip():
    try:
        import pip
        return True
    except ImportError:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "ensurepip", "--upgrade"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception:
            return False


def instalar_modulo(modulo):
    """Intenta instalar automáticamente un módulo externo con pip"""
    if not asegurar_pip():
        log_estado("❌ pip no disponible y no se pudo inicializar")
        return False

    try:
        log_estado(f"💡 Instalando módulo externo: {modulo}")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", modulo],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except Exception as e:
        log_estado(f"❌ Error instalando módulo {modulo}: {e}")
        return False


def analizar_imports(codigo):
    """Extrae modulos importados y verifica si existen"""
    fallos = []
    sugerencias = []
    try:
        tree = ast.parse(codigo)
    except SyntaxError:
        return fallos, sugerencias
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split(".")[0]
                if not modulo_existe(mod):
                    fallos.append(mod)
                    if mod not in MODULOS_ESTANDAR:
                        sugerencias.append(mod)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mod = node.module.split(".")[0]
                if not modulo_existe(mod):
                    fallos.append(mod)
                    if mod not in MODULOS_ESTANDAR:
                        sugerencias.append(mod)
    return fallos, sugerencias

def ejecutar_accion(action, code, permisos):
    if action == "python":
        return ejecutar_codigo(code, permisos)

    if action == "windows_shell":
        resultado = ejecutar_windows_shell(code)

        cmd_base = code.strip().split()[0] if code.strip() else ""

        if resultado and "not recognized" not in resultado.lower():
            memorizar(
                "CONCLUSION",
                f"El comando '{cmd_base}' está instalado y accesible en Windows shell"
            )

        return resultado

    if action == "wsl_shell":
        resultado = ejecutar_wsl_shell(code)

        cmd_base = code.strip().split()[0] if code.strip() else ""
        if resultado and "command not found" not in resultado.lower():
            memorizar(
                "CONCLUSION",
                f"El comando '{cmd_base}' está disponible en WSL"
            )

        return resultado

    return "ℹ️ Acción no ejecutable"

def ejecutar_windows_shell(comando):
    try:
        proceso = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True
        )
        salida = proceso.stdout + proceso.stderr
        memorizar("RESULTADO", salida.strip())
        log_flotante_insert(salida.strip())
        return salida.strip() or "✅ Comando ejecutado (sin salida)"
    except Exception as e:
        memorizar("ERROR", str(e))
        return f"❌ ERROR Windows shell: {e}"


def ejecutar_wsl_shell(comando):
    try:
        cmd = ["wsl", "bash", "-c", comando]
        proceso = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        salida = proceso.stdout + proceso.stderr
        memorizar("RESULTADO", salida.strip())
        log_flotante_insert(salida.strip())
        return salida.strip() or "✅ Comando WSL ejecutado"
    except Exception as e:
        memorizar("ERROR", str(e))
        return f"❌ ERROR WSL: {e}"


def ejecutar_codigo(codigo, permisos):
    if not permisos['python'] and not permisos['apps']:
        return "Permiso para ejecutar codigo denegado"

    # Ejecutar codigo Python si permisos permiten
    if permisos['python']:
        try:
            # Verificar modulos antes de ejecutar
            fallos, externos = analizar_imports(codigo)
            if fallos:
                # Intentar instalar automaticamente modulos externos faltantes
                for mod in externos:
                    instalado = instalar_modulo(mod)
                    if instalado:
                        log_estado(f"Modulo instalado automaticamente: {mod}")
                    else:
                        mensaje = f"No se pudo instalar el modulo: {mod}"
                        memorizar("ERROR", mensaje)
                        log_estado(mensaje)
                        log_flotante_insert(mensaje)
                        return mensaje

                # Re-verificar despues de instalacion automatica
                fallos_post, _ = analizar_imports(codigo)
                if fallos_post:
                    mensaje = f"Modulos aun faltantes: {', '.join(fallos_post)}"
                    memorizar("ERROR", mensaje)
                    log_estado(mensaje)
                    log_flotante_insert(mensaje)
                    return mensaje

            codigo_real = codigo
            for num, linea in enumerate(codigo_real.splitlines(), start=1):
                if linea.strip():
                    log_estado(f"Ejecutando linea Python {num}: {linea}")
                    time.sleep(0.05)
            exec(codigo_real, {})
            memorizar("RESULTADO", "Codigo Python ejecutado correctamente")
            return "Codigo Python ejecutado correctamente"
        except Exception as e:
            memorizar("ERROR", str(e))
            log_estado(f"Memoria de error guardada: {e}")
            log_flotante_insert(f"ERROR Python: {e}")
            return f"ERROR Python: {e}"

    if permisos['apps']:
        return ejecutar_como_app(codigo)

    return "No se pudo ejecutar el codigo"


def ejecutar_como_app(codigo):
    try:
        if "\n" in codigo:
            archivo_temp = f"temp_script_{int(time.time())}.py"
            with open(archivo_temp, "w", encoding="utf-8") as f:
                f.write(codigo)
            comando = ["python", archivo_temp]
            proceso = subprocess.run(comando, capture_output=True, text=True)
            os.remove(archivo_temp)
        else:
            comando = codigo.split()
            proceso = subprocess.run(comando, capture_output=True, text=True)

        salida = proceso.stdout + proceso.stderr
        memorizar("RESULTADO", salida.strip())
        log_flotante_insert(salida.strip())
        return f"✅ Comando ejecutado:\n{salida.strip()}"

    except Exception as e:
        memorizar("ERROR", str(e))
        log_estado(f"🧠 Error al ejecutar app: {e}")
        log_flotante_insert(f"❌ ERROR App: {e}")
        return f"❌ ERROR App: {e}"

# =========================
# AGENTE
# =========================
permisos_dinamicos = {"python": True, "apps": True}

def agente(objetivo):

    # =========================
    # 🔍 INTERCEPTOR pip install
    # =========================
    if objetivo.strip().lower().startswith("pip install "):
        modulo = objetivo.strip().split()[-1]
        log_estado(f"📦 Instalación solicitada: {modulo}")

        exito = instalar_modulo(modulo)
        if exito:
            log_chat(f"IA: ✅ El módulo '{modulo}' fue instalado correctamente.")
            memorizar("CONCLUSION", f"Módulo instalado manualmente: {modulo}")
        else:
            log_chat(f"IA: ❌ No se pudo instalar el módulo '{modulo}'.")
            memorizar("ERROR", f"Fallo instalando módulo: {modulo}")

        set_estado("IDLE")
        return
    # =========================
    # FIN INTERCEPTOR
    # =========================

    historial = [f"USUARIO: {objetivo}"]
    memoria = cargar_memoria()
    permisos = PERFILES[perfil_var.get()].copy()
    permisos.update(permisos_dinamicos)

    memorizar("OBJETIVO", objetivo)
    memorizar("CONVERSACION", objetivo)

    set_estado("EJECUTANDO")
    log_estado(f"🎯 Objetivo: {objetivo}")

    progreso['maximum'] = MAX_ITERACIONES
    progreso['value'] = 0

    for i in range(1, MAX_ITERACIONES + 1):
        if stop_event.is_set():
            log_estado("⛔ STOP DE EMERGENCIA")
            set_estado("STOP")
            return

        pause_event.wait()
        progreso['value'] = i
        log_estado(f"--- Iteración {i} ---")

        memoria = cargar_memoria()
        respuesta = llamar_ia(historial, memoria, permisos)
        log_chat("IA:\n" + respuesta)

        try:
            data = json.loads(respuesta)
        except:
            log_estado("❌ JSON inválido recibido de IA")
            log_estado(f"🔹 Respuesta cruda: {respuesta}")
            set_estado("IDLE")
            return

        thought = data.get('thought', "—")
        action = data.get('action', 'none')
        code = data.get('code', '')
        goal_done = data.get('goal_done', False)
        memory = data.get('memory', '')

        log_estado(f"💭 {thought}")
        historial.append(respuesta)

        if memory:
            memorizar("CONCLUSION", memory)
            log_estado(f"🧠 Conclusión guardada: {memory}")

        if action == 'none':
           respuesta_texto = code.strip() or thought.strip()
           if respuesta_texto:
            log_chat(f"IA: {respuesta_texto}")
           else:
               log_chat("IA: 👋 Hola, dime qué necesitas.")
           log_estado("ℹ️ Conversación sin ejecución")
           set_estado("IDLE")
           return


        if action in ("python", "windows_shell", "wsl_shell") and code.strip():
         log_estado(f"⚙ Ejecutando acción: {action}")
         resultado = ejecutar_accion(action, code, permisos)
         log_chat("--- RESULTADO ---\n" + resultado)


        if action == "python" and "\n" in code:
         nombre_archivo = f"script_agente_{int(time.time())}.py"
         ruta = guardar_script(nombre_archivo, code)
         log_estado(f"💾 Script guardado: {ruta}")
         memorizar("RESULTADO", ruta)



        if goal_done:
            log_estado("🏁 Objetivo completado")
            set_estado("IDLE")
            return

        if not permisos['reintentos']:
            log_estado("⚠ Reintentos desactivados")
            set_estado("IDLE")
            return

        time.sleep(1)

    log_estado("⌛ Límite alcanzado")
    set_estado("IDLE")


# =========================
# CONTROLES
# =========================
def enviar():
    texto = entrada.get().strip()
    if not texto:
        return
    log_chat("\nTU: " + texto)
    entrada.delete(0, tk.END)
    stop_event.clear()
    pause_event.set()
    progreso['value'] = 0
    threading.Thread(target=agente, args=(texto,), daemon=True).start()

def pausa():
    if pause_event.is_set():
        pause_event.clear()
        set_estado("PAUSADO")
    else:
        pause_event.set()
        set_estado("EJECUTANDO")

def stop():
    stop_event.set()
    set_estado("STOP")

# =========================
# UI PRINCIPAL
# =========================
ventana = tk.Tk()
ventana.title("IA Local - Control Total")
ventana.geometry("1000x850")
ventana.configure(bg="#000")

estado_actual = tk.StringVar(value="IDLE")

dispositivo_var = tk.StringVar(value=f"Dispositivo: {device}")
tk.Label(ventana, textvariable=dispositivo_var, bg="#000", fg="#00ff00", font=("Consolas", 12)).pack(pady=5)

chat = scrolledtext.ScrolledText(ventana, height=12, bg="#000", fg="#ff00dd", font=("Consolas", 10), state="disabled")
chat.pack(fill=tk.BOTH, padx=10, pady=5)

entrada = tk.Entry(ventana, bg="#111", fg="#fbff00", insertbackground="#d9ff00", font=("Consolas", 11))
entrada.pack(fill=tk.X, padx=10)
entrada.bind("<Return>", lambda e: enviar())

estado = scrolledtext.ScrolledText(ventana, height=14, bg="#000", fg="#00f7ff", font=("Consolas", 10), state="disabled")
estado.pack(fill=tk.BOTH, padx=10, pady=5)

progreso = ttk.Progressbar(ventana)
progreso.pack(fill=tk.X, padx=10, pady=5)

perfil_var = tk.StringVar(value="Libre")
panel = tk.LabelFrame(ventana, text="Perfil de Seguridad", fg="#00ff00", bg="#000")
panel.pack(fill=tk.X, padx=10, pady=5)

for p in PERFILES:
    tk.Radiobutton(panel, text=p, value=p, variable=perfil_var, bg="#000", fg="#d20fe4", selectcolor="#000").pack(side=tk.LEFT, padx=10)

bool_var_python = tk.BooleanVar(value=True)
bool_var_apps = tk.BooleanVar(value=True)

tk.Checkbutton(panel, text="Permitir Python", variable=bool_var_python,
               bg="#000", fg="#0f0",
               command=lambda: permisos_dinamicos.update({"python": bool_var_python.get()})).pack(side=tk.LEFT, padx=10)

tk.Checkbutton(panel, text="Permitir Apps", variable=bool_var_apps,
               bg="#000", fg="#0f0",
               command=lambda: permisos_dinamicos.update({"apps": bool_var_apps.get()})).pack(side=tk.LEFT, padx=10)

tk.Label(ventana, textvariable=estado_actual, bg="#000", fg="#00ff00", font=("Consolas", 12)).pack(pady=5)

botones = tk.Frame(ventana, bg="#000")
botones.pack(pady=10)

tk.Button(botones, text="PAUSA", width=15, command=pausa).pack(side=tk.LEFT, padx=10)
tk.Button(botones, text="STOP", width=15, command=stop).pack(side=tk.RIGHT, padx=10)

# =========================
# BURBUJA FLOTANTE OPTIMIZADA
# =========================
def crear_burbuja_completa():
    global log_flotante
    burbuja = tk.Toplevel()
    burbuja.title("IA Flotante")
    burbuja.geometry("300x400+1200+50")
    burbuja.configure(bg="#111")
    burbuja.attributes("-topmost", True)
    burbuja.attributes("-alpha", 0.9)
    burbuja.resizable(False, False)

    log_area = scrolledtext.ScrolledText(burbuja, height=15, bg="#000", fg="#00ff00", font=("Consolas", 9), state="disabled")
    log_area.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)
    log_flotante = log_area

    entry = tk.Entry(burbuja, bg="#111", fg="#ff0", insertbackground="#ff0", font=("Consolas", 11))
    entry.pack(fill=tk.X, padx=5, pady=5)

    def enviar_burbuja():
        texto = entry.get().strip()
        if texto:
            entry.delete(0, tk.END)
            log_flotante_insert(f"TU: {texto}")
            stop_event.clear()
            pause_event.set()
            threading.Thread(target=agente, args=(texto,), daemon=True).start()

    tk.Button(burbuja, text="Enviar", command=enviar_burbuja, bg="#222", fg="#0f0").pack(pady=5)

    def start_move(event):
        burbuja.x = event.x
        burbuja.y = event.y

    def do_move(event):
        deltax = event.x - burbuja.x
        deltay = event.y - burbuja.y
        x = burbuja.winfo_x() + deltax
        y = burbuja.winfo_y() + deltay
        burbuja.geometry(f"+{x}+{y}")

    log_area.bind("<Button-1>", start_move)
    log_area.bind("<B1-Motion>", do_move)

    ultima_linea = 1
    def actualizar_log():
        nonlocal ultima_linea
        contenido = chat.get(f"{ultima_linea}.0", tk.END)
        if contenido.strip():
            log_area.config(state="normal")
            log_area.insert(tk.END, contenido)
            log_area.see(tk.END)
            log_area.config(state="disabled")
        ultima_linea = int(chat.index(tk.END).split('.')[0])
        burbuja.after(500, actualizar_log)

    actualizar_log()

def process_ui_queue():
    while True:
        try:
            kind, payload = ui_queue.get_nowait()
        except Empty:
            break
        if kind == "chat":
            _log_chat_ui(payload)
        elif kind == "estado":
            _log_estado_ui(payload)
        elif kind == "flotante" and log_flotante:
            log_flotante.config(state="normal")
            log_flotante.insert(tk.END, payload + "\n")
            log_flotante.see(tk.END)
            log_flotante.config(state="disabled")
    ventana.after(50, process_ui_queue)

ventana.after(50, process_ui_queue)
ventana.after(1000, crear_burbuja_completa)
ventana.mainloop()





