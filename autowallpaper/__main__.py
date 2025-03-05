#!/usr/bin/env python3
import os
import json
import subprocess
import time
from datetime import datetime
import argparse
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

CONFIG_FILE = "wallpaper_config.json"

def set_wallpaper(path):
    current_desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

    if "xfce" in current_desktop:
        try:
            output = subprocess.check_output(['xfconf-query', '-c', 'xfce4-desktop', '-l'], text=True)
            properties = [line.strip() for line in output.splitlines() if "last-image" in line]
            if not properties:
                print("Nenhuma propriedade 'last-image' encontrada no xfce4-desktop.")
            for prop in properties:
                subprocess.run(['xfconf-query', '-c', 'xfce4-desktop', '-p', prop, '-s', path])
        except subprocess.CalledProcessError as e:
            print("Erro ao atualizar as propriedades do wallpaper no XFCE:", e)
    elif "gnome" in current_desktop or "budgie" in current_desktop:
        cmd = ['gsettings', 'set', 'org.gnome.desktop.background', 'picture-uri', f"file://{path}"]
        subprocess.run(cmd)
    elif "mate" in current_desktop:
        cmd = ['gsettings', 'set', 'org.mate.background', 'picture-filename', path]
        subprocess.run(cmd)
    elif "kde" in current_desktop:
        script = f"""
var Desktops = desktops();
for (i=0;i<Desktops.length;i++) {{
    d = Desktops[i];
    d.wallpaperPlugin = "org.kde.image";
    d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
    d.writeConfig("Image", "file://{path}")
}}
"""
        cmd = ['qdbus-qt5', 'org.kde.plasmashell', '/PlasmaShell', 'org.kde.PlasmaShell.evaluateScript', script]
        subprocess.run(cmd)
    else:
        cmd = ['feh', '--bg-scale', path]
        subprocess.run(cmd)

def get_wallpaper_for_time(wallpapers):
    agora = datetime.now().time()
    hora_manha = datetime.strptime("06:00", "%H:%M").time()
    hora_tarde = datetime.strptime("12:00", "%H:%M").time()
    hora_noite = datetime.strptime("18:00", "%H:%M").time()

    if hora_manha <= agora < hora_tarde:
        return wallpapers.get("manhã")
    elif hora_tarde <= agora < hora_noite:
        return wallpapers.get("tarde")
    else:
        return wallpapers.get("noite")

def wallpaper_loop(wallpapers, intervalo):
    while True:
        path = get_wallpaper_for_time(wallpapers)
        if path:
            set_wallpaper(path)
        time.sleep(intervalo * 60)

def start_wallpaper_switcher(wallpapers, intervalo):
    thread = threading.Thread(target=wallpaper_loop, args=(wallpapers, intervalo), daemon=True)
    thread.start()

def parse_args():
    parser = argparse.ArgumentParser(
        description="Troca wallpapers automaticamente com base no horário (manhã, tarde, noite).")
    parser.add_argument("--manha", help="Caminho do wallpaper para a manhã", type=str)
    parser.add_argument("--tarde", help="Caminho do wallpaper para a tarde", type=str)
    parser.add_argument("--noite", help="Caminho do wallpaper para a noite", type=str)
    parser.add_argument("--intervalo", help="Intervalo em minutos para troca de wallpaper", type=int)
    parser.add_argument("--reset", action="store_true", help="Força reconfiguração (ignora configuração salva)")
    return parser.parse_args()

def gui_config():
    config = {"manhã": None, "tarde": None, "noite": None, "intervalo": 10}

    def selecionar_wallpaper(periodo):
        caminho = filedialog.askopenfilename(
            title=f"Selecione o wallpaper para {periodo}",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")])
        if caminho:
            config[periodo] = caminho
            labels[periodo]["text"] = caminho

    def iniciar():
        try:
            config["intervalo"] = int(entry_intervalo.get())
        except ValueError:
            messagebox.showerror("Erro", "Intervalo deve ser um número inteiro")
            return

        if not (config["manhã"] and config["tarde"] and config["noite"]):
            messagebox.showerror("Erro", "Selecione todos os wallpapers (manhã, tarde e noite)")
            return
        root.destroy()

    root = tk.Tk()
    root.title("Configuração do Wallpaper")

    labels = {}
    for idx, periodo in enumerate(["manhã", "tarde", "noite"]):
        frame = tk.Frame(root)
        frame.pack(padx=10, pady=5, fill="x")
        btn = tk.Button(frame, text=f"Selecionar wallpaper para {periodo}",
                        command=lambda p=periodo: selecionar_wallpaper(p))
        btn.pack(side="left")
        lbl = tk.Label(frame, text="Nenhum arquivo selecionado", wraplength=300)
        lbl.pack(side="left", padx=5)
        labels[periodo] = lbl

    frame_intervalo = tk.Frame(root)
    frame_intervalo.pack(padx=10, pady=5, fill="x")
    tk.Label(frame_intervalo, text="Intervalo (minutos):").pack(side="left")
    entry_intervalo = tk.Entry(frame_intervalo, width=5)
    entry_intervalo.insert(0, "10")
    entry_intervalo.pack(side="left", padx=5)

    btn_iniciar = tk.Button(root, text="Iniciar", command=iniciar)
    btn_iniciar.pack(pady=10)

    root.mainloop()
    return config

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print("Erro ao carregar a configuração:", e)
    return None

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print("Erro ao salvar a configuração:", e)

def main():
    args = parse_args()
    config = None

    if not args.reset:
        config = load_config()

    if args.manha and args.tarde and args.noite and args.intervalo:
        config = {
            "manhã": args.manha,
            "tarde": args.tarde,
            "noite": args.noite,
            "intervalo": args.intervalo
        }
    elif config is None:
        config = gui_config()
    
    save_config(config)

    wallpapers = {
        "manhã": config["manhã"],
        "tarde": config["tarde"],
        "noite": config["noite"]
    }
    intervalo = config["intervalo"]

    print("Iniciando a troca automática de wallpapers...")
    start_wallpaper_switcher(wallpapers, intervalo)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Encerrando o script.")

if __name__ == '__main__':
    main()
