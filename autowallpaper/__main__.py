#!/usr/bin/env python3
import sys
import os
import json
import subprocess
import time
from datetime import datetime
import argparse
import threading
from PyQt5 import QtWidgets, QtGui

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
    parser.add_argument("--daemon", action="store_true", help="Executa o script como um daemon em segundo plano")
    return parser.parse_args()

def gui_config():
    config = {"manhã": None, "tarde": None, "noite": None, "intervalo": 10}

    class ConfigWindow(QtWidgets.QWidget):
        def __init__(self):
            super().__init__()
            self.initUI()

        def initUI(self):
            self.setWindowTitle("Configuração do Wallpaper")
            self.setGeometry(100, 100, 400, 300)
            self.setStyleSheet("background-color: #f0f0f0;")

            layout = QtWidgets.QVBoxLayout()

            self.labels = {}
            for periodo in ["manhã", "tarde", "noite"]:
                hbox = QtWidgets.QHBoxLayout()
                btn = QtWidgets.QPushButton(f"Selecionar wallpaper para {periodo}")
                btn.setStyleSheet("background-color: #4CAF50; color: white;")
                btn.clicked.connect(lambda _, p=periodo: self.selecionar_wallpaper(p))
                lbl = QtWidgets.QLabel("Nenhum arquivo selecionado")
                lbl.setStyleSheet("background-color: #f0f0f0;")
                hbox.addWidget(btn)
                hbox.addWidget(lbl)
                layout.addLayout(hbox)
                self.labels[periodo] = lbl

            hbox_intervalo = QtWidgets.QHBoxLayout()
            lbl_intervalo = QtWidgets.QLabel("Intervalo (minutos):")
            lbl_intervalo.setStyleSheet("background-color: #f0f0f0;")
            self.entry_intervalo = QtWidgets.QLineEdit("10")
            hbox_intervalo.addWidget(lbl_intervalo)
            hbox_intervalo.addWidget(self.entry_intervalo)
            layout.addLayout(hbox_intervalo)

            btn_iniciar = QtWidgets.QPushButton("Iniciar")
            btn_iniciar.setStyleSheet("background-color: #4CAF50; color: white;")
            btn_iniciar.clicked.connect(self.iniciar)
            layout.addWidget(btn_iniciar)

            self.setLayout(layout)

        def selecionar_wallpaper(self, periodo):
            caminho, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, f"Selecione o wallpaper para {periodo}", "", 
                "Todos os Arquivos de Imagem (*.png *.jpg *.jpeg *.bmp *.gif);;PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;GIF (*.gif)")
            if caminho:
                config[periodo] = caminho
                self.labels[periodo].setText(caminho)

        def iniciar(self):
            try:
                config["intervalo"] = int(self.entry_intervalo.text())
            except ValueError:
                QtWidgets.QMessageBox.critical(self, "Erro", "Intervalo deve ser um número inteiro")
                return

            if not (config["manhã"] and config["tarde"] and config["noite"]):
                QtWidgets.QMessageBox.critical(self, "Erro", "Selecione todos os wallpapers (manhã, tarde e noite)")
                return
            self.close()

    app = QtWidgets.QApplication(sys.argv)
    window = ConfigWindow()
    window.show()
    app.exec_()
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

    if args.daemon:
        print("Executando em segundo plano...")
        while True:
            time.sleep(1)
    else:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Encerrando o script.")

if __name__ == '__main__':
    if '--daemon' in sys.argv:
        pid = os.fork()
        if pid > 0:
            sys.exit()
    main()
