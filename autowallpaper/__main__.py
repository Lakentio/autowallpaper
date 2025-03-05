#!/usr/bin/env python3
import os
import json
import subprocess
import time
from datetime import datetime
import argparse
import threading

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
        description="Automatically change wallpapers based on time of day (morning, afternoon, evening).")
    parser.add_argument("--morning", help="Path to the morning wallpaper", type=str)
    parser.add_argument("--afternoon", help="Path to the afternoon wallpaper", type=str)
    parser.add_argument("--evening", help="Path to the evening wallpaper", type=str)
    parser.add_argument("--interval", help="Interval in minutes for wallpaper change", type=int, default=10)
    parser.add_argument("--reset", action="store_true", help="Force reconfiguration (ignore saved configuration)")
    return parser.parse_args()

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

    if args.morning and args.afternoon and args.evening and args.interval:
        config = {
            "morning": args.morning,
            "afternoon": args.afternoon,
            "evening": args.evening,
            "interval": args.interval
        }
    elif config is None:
        print("No configuration found. Please provide wallpaper paths and interval using arguments.")
        return
    
    save_config(config)

    wallpapers = {''
        "morning": config["morning"],
        "afternoon": config["afternoon"],
        "evening": config["evening"]
    }
    intervalo = config["interval"]

    print("Starting automatic wallpaper changer...")
    start_wallpaper_switcher(wallpapers, intervalo)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping the script.")

if __name__ == '__main__':
    main()
