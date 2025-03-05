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
                print("No 'last-image' property found in xfce4-desktop.")
            for prop in properties:
                subprocess.run(['xfconf-query', '-c', 'xfce4-desktop', '-p', prop, '-s', path])
        except subprocess.CalledProcessError as e:
            print("Error updating wallpaper properties in XFCE:", e)
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
    now = datetime.now().time()
    morning_time = datetime.strptime("06:00", "%H:%M").time()
    afternoon_time = datetime.strptime("12:00", "%H:%M").time()
    evening_time = datetime.strptime("18:00", "%H:%M").time()

    if morning_time <= now < afternoon_time:
        return wallpapers.get("morning")
    elif afternoon_time <= now < evening_time:
        return wallpapers.get("afternoon")
    else:
        return wallpapers.get("evening")

def wallpaper_loop(wallpapers, interval):
    while True:
        path = get_wallpaper_for_time(wallpapers)
        if path:
            set_wallpaper(path)
        time.sleep(interval * 60)

def start_wallpaper_switcher(wallpapers, interval):
    thread = threading.Thread(target=wallpaper_loop, args=(wallpapers, interval), daemon=True)
    thread.start()

def parse_args():
    parser = argparse.ArgumentParser(
        description="Automatically change wallpapers based on time (morning, afternoon, evening).")
    parser.add_argument("--morning", help="Path to the morning wallpaper", type=str)
    parser.add_argument("--afternoon", help="Path to the afternoon wallpaper", type=str)
    parser.add_argument("--evening", help="Path to the evening wallpaper", type=str)
    parser.add_argument("--interval", help="Interval in minutes to change wallpaper", type=int)
    parser.add_argument("--reset", action="store_true", help="Force reconfiguration (ignore saved configuration)")
    parser.add_argument("--foreground", action="store_true", help="Run the script in the foreground")
    return parser.parse_args()

def gui_config():
    config = {"morning": None, "afternoon": None, "evening": None, "interval": 10}

    class ConfigWindow(Gtk.Window):
        def __init__(self):
            Gtk.Window.__init__(self, title="Wallpaper Configuration")
            self.set_border_width(10)
            self.set_default_size(400, 300)

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            self.add(vbox)

            self.labels = {}
            for period in ["morning", "afternoon", "evening"]:
                hbox = Gtk.Box(spacing=10)
                btn = Gtk.Button(label=f"Select wallpaper for {period}")
                btn.connect("clicked", self.select_wallpaper, period)
                lbl = Gtk.Label(label="No file selected")
                hbox.pack_start(btn, True, True, 0)
                hbox.pack_start(lbl, True, True, 0)
                vbox.pack_start(hbox, True, True, 0)
                self.labels[period] = lbl

            hbox_interval = Gtk.Box(spacing=10)
            lbl_interval = Gtk.Label(label="Interval (minutes):")
            self.entry_interval = Gtk.Entry()
            self.entry_interval.set_text("10")
            hbox_interval.pack_start(lbl_interval, True, True, 0)
            hbox_interval.pack_start(self.entry_interval, True, True, 0)
            vbox.pack_start(hbox_interval, True, True, 0)

            btn_start = Gtk.Button(label="Start")
            btn_start.connect("clicked", self.start)
            vbox.pack_start(btn_start, True, True, 0)

        def select_wallpaper(self, widget, period):
            dialog = Gtk.FileChooserDialog(
                title=f"Select wallpaper for {period}", parent=self,
                action=Gtk.FileChooserAction.OPEN)
            dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                               Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

            filter_image = Gtk.FileFilter()
            filter_image.set_name("All Image Files")
            filter_image.add_mime_type("image/png")
            filter_image.add_mime_type("image/jpeg")
            filter_image.add_mime_type("image/bmp")
            filter_image.add_mime_type("image/gif")
            dialog.add_filter(filter_image)

            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                path = dialog.get_filename()
                config[period] = path
                self.labels[period].set_text(path)
            dialog.destroy()

        def start(self, widget):
            try:
                config["interval"] = int(self.entry_interval.get_text())
            except ValueError:
                dialog = Gtk.MessageDialog(
                    transient_for=self, flags=0, message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK, text="Error")
                dialog.format_secondary_text("Interval must be an integer")
                dialog.run()
                dialog.destroy()
                return

            if not (config["morning"] and config["afternoon"] and config["evening"]):
                dialog = Gtk.MessageDialog(
                    transient_for=self, flags=0, message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK, text="Error")
                dialog.format_secondary_text("Select all wallpapers (morning, afternoon, and evening)")
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
            print("Error loading configuration:", e)
    return None

def save_config(config):
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print("Error saving configuration:", e)

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
        config = gui_config()
    
    save_config(config)

    wallpapers = {
        "morning": config.get("morning"),
        "afternoon": config.get("afternoon"),
        "evening": config.get("evening")
    }
    interval = config.get("interval")

    print("Starting automatic wallpaper change...")
    start_wallpaper_switcher(wallpapers, interval)

    if args.foreground:
        print("Running in foreground...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping script.")
    else:
        print("Running in background...")
        subprocess.Popen([sys.executable] + sys.argv + ["--foreground"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sys.exit()

if __name__ == '__main__':
    main()
