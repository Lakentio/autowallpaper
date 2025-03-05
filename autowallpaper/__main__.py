#!/usr/bin/env python3
import sys
import os
import json
import subprocess
import time
from datetime import datetime
import argparse
import threading
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

CONFIG_FILE = os.path.expanduser("~/.config/autowallpaper/wallpaper_config.json")

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
    parser.add_argument("--foreground", action="store_true", help="Executa o script em primeiro plano")
    return parser.parse_args()

def gui_config():
    config = {"manhã": None, "tarde": None, "noite": None, "intervalo": 10}

    class ConfigWindow(Gtk.Window):
        def __init__(self):
            Gtk.Window.__init__(self, title="Configuração do Wallpaper")
            self.set_border_width(10)
            self.set_default_size(400, 300)

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            self.add(vbox)

            self.labels = {}
            for periodo in ["manhã", "tarde", "noite"]:
                hbox = Gtk.Box(spacing=10)
                btn = Gtk.Button(label=f"Selecionar wallpaper para {periodo}")
                btn.connect("clicked", self.selecionar_wallpaper, periodo)
                lbl = Gtk.Label(label="Nenhum arquivo selecionado")
                hbox.pack_start(btn, True, True, 0)
                hbox.pack_start(lbl, True, True, 0)
                vbox.pack_start(hbox, True, True, 0)
                self.labels[periodo] = lbl

            hbox_intervalo = Gtk.Box(spacing=10)
            lbl_intervalo = Gtk.Label(label="Intervalo (minutos):")
            self.entry_intervalo = Gtk.Entry()
            self.entry_intervalo.set_text("10")
            hbox_intervalo.pack_start(lbl_intervalo, True, True, 0)
            hbox_intervalo.pack_start(self.entry_intervalo, True, True, 0)
            vbox.pack_start(hbox_intervalo, True, True, 0)

            btn_iniciar = Gtk.Button(label="Iniciar")
            btn_iniciar.connect("clicked", self.iniciar)
            vbox.pack_start(btn_iniciar, True, True, 0)

        def selecionar_wallpaper(self, widget, periodo):
            dialog = Gtk.FileChooserDialog(
                title=f"Selecione o wallpaper para {periodo}", parent=self,
                action=Gtk.FileChooserAction.OPEN)
            dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                               Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

            filter_image = Gtk.FileFilter()
            filter_image.set_name("Todos os Arquivos de Imagem")
            filter_image.add_mime_type("image/png")
            filter_image.add_mime_type("image/jpeg")
            filter_image.add_mime_type("image/bmp")
            filter_image.add_mime_type("image/gif")
            dialog.add_filter(filter_image)

            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                caminho = dialog.get_filename()
                config[periodo] = caminho
                self.labels[periodo].set_text(caminho)
            dialog.destroy()

        def iniciar(self, widget):
            try:
                config["intervalo"] = int(self.entry_intervalo.get_text())
            except ValueError:
                dialog = Gtk.MessageDialog(
                    transient_for=self, flags=0, message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK, text="Erro")
                dialog.format_secondary_text("Intervalo deve ser um número inteiro")
                dialog.run()
                dialog.destroy()
                return

            if not (config["manhã"] and config["tarde"] and config["noite"]):
                dialog = Gtk.MessageDialog(
                    transient_for=self, flags=0, message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK, text="Erro")
                dialog.format_secondary_text("Selecione todos os wallpapers (manhã, tarde e noite)")
                dialog.run()
                dialog.destroy()
                return
            self.close()

    win = ConfigWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
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
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
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

    if args.foreground:
        print("Executando em primeiro plano...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Encerrando o script.")
    else:
        print("Executando em segundo plano...")
        subprocess.Popen([sys.executable] + sys.argv + ["--foreground"])
        sys.exit()

if __name__ == '__main__':
    main()
