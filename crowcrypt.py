import os
import tkinter as tk
from tkinter import messagebox, simpledialog
from cryptography.fernet import Fernet
import threading
import pystray
from PIL import Image, ImageTk
import logging
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from PIL import Image

# Estado do app
encrypted = False
animation_id = None
target_directory = "."
IGNORED_FILES = ["app.py", "key.key"]

# Log
logging.basicConfig(
    filename="log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logging.info("App started.")

# Janela principal
app = tb.Window(themename="darkly")
app.title("CrowCrypt")
app.geometry("650x450")
app.resizable(False, False)

# Bloquear fechamento
def on_close():
    if encrypted:
        Messagebox.show_warning("You must decrypt files before exiting.", title="Warning")
    else:
        app.destroy()

app.protocol("WM_DELETE_WINDOW", on_close)

# Status
status_var = tk.StringVar()
status_label = tb.Label(app, textvariable=status_var, foreground="lightblue", font=("Arial", 10))
status_label.pack(pady=5)

def animate_status(text_base, count=0):
    global animation_id
    dots = "." * (count % 4)
    status_var.set(text_base + dots)
    animation_id = app.after(500, lambda: animate_status(text_base, count + 1))

# Gerar chave
def generate_key():
    key = Fernet.generate_key()
    with open("key.key", "wb") as f:
        f.write(key)
    return key

def load_key():
    with open("key.key", "rb") as f:
        return f.read()

# Listar arquivos
def list_files(directory):
    files = []
    for root, _, filenames in os.walk(directory):
        for file in filenames:
            full_path = os.path.join(root, file)
            if any(ignored in full_path for ignored in IGNORED_FILES):
                continue
            files.append(full_path)
    return files

# Selecionar pasta
def select_folder():
    global target_directory
    from tkinter import filedialog
    folder = filedialog.askdirectory()
    if folder:
        target_directory = folder
        folder_label.configure(text=f"Selected Folder:\n{folder}")

# Criptografar
def encrypt_files():
    global encrypted
    try:
        animate_status("Encrypting")
        key = generate_key()
        fernet = Fernet(key)
        files = list_files(target_directory)
        log_output.delete(1.0, tk.END)

        progress["maximum"] = len(files)
        progress["value"] = 0

        for i, file in enumerate(files, 1):
            with open(file, "rb") as f:
                data = f.read()
            with open(file, "wb") as f:
                f.write(fernet.encrypt(data))
            log_output.insert(tk.END, f"[✔] Encrypted: {file}\n")
            progress["value"] = i
            app.update_idletasks()

        encrypted = True
        logging.info("Files encrypted successfully.")
        Messagebox.show_info(f"{len(files)} files encrypted.", title="Success")
    except Exception as e:
        logging.error(f"Encryption error: {e}")
        Messagebox.show_error(str(e), title="Error")
    finally:
        if animation_id:
            app.after_cancel(animation_id)
        status_var.set("Encryption complete.")

# Descriptografar
def decrypt_files():
    global encrypted
    try:
        password = simpledialog.askstring("Password", "Enter the password to decrypt:", show="*")
        if password != "12345678":
            Messagebox.show_warning("Wrong password!", title="Access Denied")
            return

        animate_status("Decrypting")
        key = load_key()
        fernet = Fernet(key)
        files = list_files(target_directory)
        log_output.delete(1.0, tk.END)

        progress["maximum"] = len(files)
        progress["value"] = 0

        for i, file in enumerate(files, 1):
            with open(file, "rb") as f:
                data = f.read()
            with open(file, "wb") as f:
                f.write(fernet.decrypt(data))
            log_output.insert(tk.END, f"[✔] Decrypted: {file}\n")
            progress["value"] = i
            app.update_idletasks()

        encrypted = False
        logging.info("Files decrypted successfully.")
        Messagebox.show_info(f"{len(files)} files decrypted.", title="Success")
    except Exception as e:
        logging.error(f"Decryption error: {e}")
        Messagebox.show_error(str(e), title="Error")
    finally:
        if animation_id:
            app.after_cancel(animation_id)
        status_var.set("Decryption complete.")

# UI Layout
folder_icon = ImageTk.PhotoImage(Image.open("folder.png").resize((18, 18)))
lock_icon = ImageTk.PhotoImage(Image.open("lock.png").resize((18, 18)))
unlock_icon = ImageTk.PhotoImage(Image.open("unlock.png").resize((18, 18)))

frame_top = tb.Frame(app)
frame_top.pack(pady=10)

folder_label = tb.Label(frame_top, text="No folder selected")
folder_label.pack(pady=5)

tb.Button(frame_top, text=" Select Folder", image=folder_icon, compound=LEFT, command=select_folder, bootstyle=PRIMARY).pack()

frame_buttons = tb.Frame(app)
frame_buttons.pack(pady=10)

tb.Button(frame_buttons, text=" Encrypt", image=lock_icon, compound=LEFT, command=encrypt_files, width=20, bootstyle=SUCCESS).pack(side=LEFT, padx=10)
tb.Button(frame_buttons, text=" Decrypt", image=unlock_icon, compound=LEFT, command=decrypt_files, width=20, bootstyle=WARNING).pack(side=LEFT, padx=10)

tb.Label(app, text="Process Log:").pack(pady=5)
log_output = tk.Text(app, height=10, width=72, font=("Courier", 9))
log_output.pack(padx=10)

progress = tb.Progressbar(app, orient="horizontal", length=500, mode="determinate", bootstyle=INFO)
progress.pack(pady=5)

# Minimizar para bandeja
def hide_app():
    app.withdraw()

def restore_app(icon, item):
    app.deiconify()

def exit_app(icon, item):
    icon.stop()
    app.destroy()

def tray_icon():
    try:
        tray_img = Image.open("icone.png").resize((64, 64))
        menu = pystray.Menu(
            pystray.MenuItem(" Restore", restore_app),
            pystray.MenuItem(" Exit", exit_app)
        )
        icon = pystray.Icon("CrowCrypt", tray_img, "CrowCrypt", menu)
        icon.run()
    except Exception as e:
        print(f"Tray icon error: {e}")

def on_minimize(event=None):
    if app.state() == "iconic":
        hide_app()
        threading.Thread(target=tray_icon, daemon=True).start()

app.bind("<Unmap>", on_minimize)

# Iniciar app
app.mainloop()
