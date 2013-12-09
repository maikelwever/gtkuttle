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

        self.data.setdefault('name', '')
        self.data.setdefault('address', 'user@host:22')
        self.data.setdefault('subnet', '0.0.0.0/0')
        self.data.setdefault('use_dns', False)
        self.data.setdefault('use_askpass', True)

    def run(self):
        # Initialize dialog
        self.wTree = gtk.glade.XML(self.gladefile, "addEndpointDlg")
        self.dlg = self.wTree.get_widget("addEndpointDlg")

        # Get all widgets
        self.in_name = self.wTree.get_widget('in_name')
        self.in_address = self.wTree.get_widget('in_address')
        self.in_subnet = self.wTree.get_widget('in_subnet')
        self.cb_dns = self.wTree.get_widget('cb_dns')
        self.cb_askpass = self.wTree.get_widget('cb_askpass')

        # Set default widget text
        self.in_name.set_text(self.data['name'])
        self.in_address.set_text(self.data['address'])
        self.in_subnet.set_text(self.data['subnet'])
        self.cb_dns.set_active(self.data['use_dns'])
        self.cb_askpass.set_active(self.data['use_askpass'])

        # Show dialog
        self.result = self.dlg.run()

        # Fetch data from dialog
        self.data['name'] = self.in_name.get_text()
        self.data['address'] = self.in_address.get_text()
        self.data['subnet'] = self.in_subnet.get_text()
        self.data['use_dns'] = self.cb_dns.get_active()
        self.data['use_askpass'] = self.cb_askpass.get_active()

        # Kill dialog and return data
        self.dlg.destroy()
        return self.result, self.data


class MainApplication():

    settings = {
        "endpoints": {},
    }

    def __init__(self):
        if not os.path.exists(SETTINGS_FILE_PATH):
            os.system('touch {0}'.format(SETTINGS_FILE_PATH))
            self.save_settings()

        self.read_settings()

        self.ind = appindicator.Indicator("gtkuttle", "gtkuttle",
                      appindicator.CATEGORY_APPLICATION_STATUS)
        self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.ind.set_label("gtkuttle")

        self.menu = None
        self.build_menu()

    def build_menu(self):
        self.menu = gtk.Menu()

        # render saved endpoints
        for name, endpoint in self.settings['endpoints'].iteritems():
            endpoint_item = gtk.MenuItem(name)
            endpoint_item.show()
            self.menu.append(endpoint_item)
            endpoint_item.connect('activate', self.endpoint_clicked)

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
            self.settings = json.loads(f.read())

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
        result, data = dialog.run()
        print result
        print data

        self.settings['endpoints'][data['name']] = data
        self.save_settings()
        self.build_menu()

        print self.settings

    def endpoint_clicked(self, widget):
        ep_name = widget.get_label()
        try:
            endpoint = self.settings['endpoints'][ep_name]
        except (IndexError, KeyError):
            return

        print endpoint

        self.show_error("ERRUH!")
        #import pdb; pdb.set_trace();

    def run(self):
        gtk.main()
        return 0

    def show_error(self, message):
        error_dialog = gtk.MessageDialog(
            message_format=message,
            type=gtk.MESSAGE_ERROR,
            buttons=gtk.BUTTONS_CLOSE
        )
        response = error_dialog.run()
        error_dialog.destroy()


if __name__ == "__main__":
    app = MainApplication()
    app.run()
