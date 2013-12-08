#!/usr/bin/env python2
#gtkuttle.py

import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade


import json
import os

try:
    import appindicator
except ImportError:
    import appindicator_replacement as appindicator


SETTINGS_FILE_PATH = os.path.expanduser("~/.gtkuttle.json")
PID_FILE_PATH = "/tmp/gtkuttle-sshuttle.pid"


class AddEndpointWindow():
    def __init__(self, endpoint_data):
        self.gladefile = "uifiles/add_new_endpoint_dialog.glade"
        self.data = endpoint_data

    def run(self):
        self.wTree = gtk.glade.XML(self.gladefile, "addEndpointDlg")
        self.dlg = self.wTree.get_widget("addEndpointDlg")
        self.result = self.dlg.run()

        self.dlg.destroy()
        return self.data


class MainApplication():

    settings = {
        "endpoints": []
    }

    def __init__(self):
        if not os.path.exists(SETTINGS_FILE_PATH):
            os.system('touch {0}'.format(SETTINGS_FILE_PATH))
            self.save_settings()

        self.ind = appindicator.Indicator("gtkuttle", "gtkuttle",
                      appindicator.CATEGORY_APPLICATION_STATUS)
        self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.ind.set_label("gtkuttle")

        self.menu = None
        self.build_menu()

    def build_menu(self):
        self.menu = gtk.Menu()

        # render saved endpoints
        for endpoint in self.settings['endpoints']:
            pass

        # render app buttons
        add_new = gtk.MenuItem("Add new endpoint")
        add_new.show()
        self.menu.append(add_new)
        add_new.connect('activate', self.show_add_new_dialog)

        if self.session_is_open():
            disconnect = gtk.MenuItem("Disconnect current session")
            disconnect.show()
            self.menu.append(disconnect)
            disconnect.connect('activate',
                               self.disconnect_current_session)

        self.menu.show()
        self.ind.set_menu(self.menu)

    def read_settings(self):
        with open(SETTINGS_FILE_PATH, "r") as f:
            self.settings = json.parse(f.read())

    def save_settings(self):
        with open(SETTINGS_FILE_PATH, "w") as f:
            f.write(json.dumps(self.settings))

    def on_right_click(self, event_button, event_time):
        self.menu.popup(None, None, None, 0, 0)

    def disconnect_current_session(self):
        os.system("kill $(cat {0})".format(PID_FILE_PATH))

    def session_is_open(self):
        return os.path.exists(PID_FILE_PATH)

    def show_add_new_dialog(self, widget):
        dialog = AddEndpointWindow({})
        result = dialog.run()
        print result

    def run(self):
        gtk.main()
        return 0


if __name__ == "__main__":
    app = MainApplication()
    app.run()
