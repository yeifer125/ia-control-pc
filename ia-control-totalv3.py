import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
import ollama
import json
import subprocess
import time
import os
import torch
import pyautogui
import pygetwindow as gw
import pyperclip
import webbrowser

# =========================
# CONFIG
# =========================
MODEL = "qwen3:4b"
MAX_ITERACIONES = 6
MEMORIA_ARCHIVO = "memoria_agente.txt"
LOG_ARCHIVO = "log_sesion.txt"

device = "cuda" if torch.cuda.is_available() else "cpu"

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
TIPOS_VALIDOS = ["OBJETIVO", "ERROR", "RESULTADO", "PERMISOS", "CONVERSACION", "REGLA"]

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
Eres un agente autónomo ejecutándose en WINDOWS.

REGLAS:
- Usa la MEMORIA si existe información previa útil
- No inventes rutas
- No marques objetivo completado sin ejecutar código real
- Si solo es conversación → action = "none"
- Si requiere acción real → action = "python"

Responde SOLO en JSON:

{
  "thought": "razonamiento corto",
  "action": "python | none",
  "code": "",
  "goal_done": false,
  "memory": ""
}
"""

# =========================
# UI
# =========================
def log_chat(t):
    chat.config(state="normal")
    chat.insert(tk.END, t + "\n")
    chat.see(tk.END)
    chat.config(state="disabled")
    guardar_log(t)

def log_estado(t):
    linea = f"[IA@local] > {t}"
    estado.config(state="normal")
    estado.insert(tk.END, linea + "\n")
    estado.see(tk.END)
    estado.config(state="disabled")
    guardar_log(linea)

def set_estado(t):
    estado_actual.set(t)

# =========================
# BURBUJA FLOTANTE
# =========================
log_flotante = None
def log_flotante_insert(msg):
    if log_flotante:
        log_flotante.config(state="normal")
        log_flotante.insert(tk.END, msg + "\n")
        log_flotante.see(tk.END)
        log_flotante.config(state="disabled")
    log_chat(msg)

# =========================
# IA
# =========================
def llamar_ia(historial, memoria, permisos):
    log_estado("🧠 Pensando...")
    memoria_texto = "\n".join(memoria)
    contexto = SYSTEM_PROMPT + "\nMEMORIA:\n" + memoria_texto + f"\nPERMISOS: {permisos}\n" + "\n".join(historial)
    return ollama.generate(model=MODEL, prompt=contexto)["response"]

# =========================
# EJECUTAR CÓDIGO
# =========================
def ejecutar_codigo(codigo, permisos):
    if not permisos['python'] and not permisos['apps']:
        return "⛔ Permiso para ejecutar código denegado"

    if permisos['python']:
        try:
            codigo_real = codigo.replace("\\", "\\\\")
            entorno = {
                "subprocess": subprocess if permisos['apps'] else None,
                "os": os,
                "time": time,
                "pyautogui": pyautogui,
                "pygetwindow": gw,
                "webbrowser": webbrowser,
                "pyperclip": pyperclip,
                "log_flotante": log_flotante_insert,
                "print": log_flotante_insert,
                "__name__": "__main__"
            }
            for num, linea in enumerate(codigo_real.splitlines(), start=1):
                if linea.strip():
                    log_estado(f"▶ Ejecutando línea Python {num}: {linea}")
                    time.sleep(0.05)
            exec(codigo_real, entorno)
            memorizar("RESULTADO", "Código Python ejecutado correctamente")
            return "✅ Código Python ejecutado correctamente"
        except Exception as e:
            memorizar("ERROR", str(e))
            log_estado(f"🧠 Memoria de error guardada: {e}")
            log_flotante_insert(f"❌ ERROR Python: {e}")
            if permisos['apps']:
                return ejecutar_como_app(codigo_real)

    if permisos['apps']:
        return ejecutar_como_app(codigo)

    return "⛔ No se pudo ejecutar el código"

def ejecutar_como_app(codigo):
    try:
        if "\n" in codigo:
            archivo_temp = f"temp_script_{int(time.time())}.py"
            with open(archivo_temp, "w", encoding="utf-8") as f:
                f.write(codigo)
            comando = ["python", archivo_temp]
        else:
            comando = codigo.split()
        log_estado(f"⚙ Ejecutando comando externo: {' '.join(comando)}")
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

        # Manejo seguro de keys
        thought = data.get('thought', "—")
        action = data.get('action', 'none')
        code = data.get('code', '')
        goal_done = data.get('goal_done', False)
        memory = data.get('memory', '')

        log_estado(f"💭 {thought}")
        historial.append(respuesta)

        if memory:
            memorizar("OBJETIVO", memory)
            memorizar("CONVERSACION", memory)
            log_estado(f"🧠 Memoria guardada: {memory}")

        if action == 'none':
            log_estado("ℹ️ Sin acción requerida")
            set_estado("IDLE")
            return

        if action == 'python' and code.strip():
            nombre_archivo = f"script_agente_{int(time.time())}.py"
            ruta = guardar_script(nombre_archivo, code)
            log_estado(f"💾 Script guardado: {ruta}")
            memorizar("RESULTADO", ruta)

            log_estado("⚙ Ejecutando código sin confirmación...")
            resultado = ejecutar_codigo(code, permisos)
            log_chat("--- RESULTADO ---\n" + resultado)

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
    log_chat("\nTÚ: " + texto)
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
ventana.title("IA Local – Control Total")
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

tk.Button(botones, text="⏸ PAUSA", width=15, command=pausa).pack(side=tk.LEFT, padx=10)
tk.Button(botones, text="⛔ STOP", width=15, command=stop).pack(side=tk.RIGHT, padx=10)

# =========================
# BURBUJA FLOTANTE
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
            log_flotante_insert(f"TÚ: {texto}")
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

    def actualizar_log():
        contenido = chat.get("1.0", tk.END)
        log_area.config(state="normal")
        log_area.delete("1.0", tk.END)
        log_area.insert(tk.END, contenido)
        log_area.see(tk.END)
        log_area.config(state="disabled")
        burbuja.after(500, actualizar_log)

    actualizar_log()

ventana.after(1000, crear_burbuja_completa)
ventana.mainloop()
