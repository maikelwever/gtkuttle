#!/usr/bin/env python2
#gtkuttle.py

from gi.repository import Gtk
import json
import os


SETTINGS_FILE_PATH = os.path.expanduser("~/.gtkuttle.json")
PID_FILE_PATH = "/tmp/gtkuttle-sshuttle.pid"


class MainApplication():

    settings = {
        "endpoints": []
    }

    def __init__(self):
        if not os.path.exists(SETTINGS_FILE_PATH):
            os.system('touch {0}'.format(SETTINGS_FILE_PATH))
            self.save_settings()

        self.tray = Gtk.StatusIcon()
        self.tray.set_from_stock(Gtk.STOCK_NETWORK)
        self.tray.connect('popup-menu', self.on_right_click)
        self.tray.set_tooltip_text(('gtkuttle - a sshuttle frontend'))

    def read_settings(self):
        with open(SETTINGS_FILE_PATH, "r") as f:
            self.settings = json.parse(f.read(-1))

    def save_settings(self):
        with open(SETTINGS_FILE_PATH, "w") as f:
            f.write(json.dumps(self.settings))

    def on_right_click(self, event_button, event_time, user_data):
        menu = Gtk.Menu()

        # render saved endpoints
        for endpoint in self.settings['endpoints']:
            pass

        # render app buttons
        add_new = Gtk.MenuItem("Add new endpoint")
        add_new.show()
        menu.append(add_new)
        add_new.connect('activate', self.show_add_new_dialog)

        if self.session_is_open():
            disconnect = Gtk.MenuItem("Disconnect current session")
            disconnect.show()
            menu.append(disconnect)
            disconnect.connect('activate', self.disconnect_current_session)

        menu.popup(None, None, Gtk.Menu.status_icon_position_menu, self.tray, event_button, event_time)

    def disconnect_current_session(self):
        os.system("kill $(cat {0})".format(PID_FILE_PATH))

    def session_is_open(self):
        return os.path.exists(PID_FILE_PATH)

    def show_add_new_dialog(self, widget):
        pass


if __name__ == "__main__":
    MainApplication()
    Gtk.main()
