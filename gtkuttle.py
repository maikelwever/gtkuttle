#!/usr/bin/env python2
#gtkuttle.py

"""
===============================================================
gtkuttle Copyright (C) 2013 Maikel Wever.

This program comes with ABSOLUTELY NO WARRANTY;
for details see the LICENSE file.
This is free software, and you are welcome to redistribute it
under certain conditions; see the LICENCSE file for details.
===============================================================
"""

__version__ = "0.9"
__status__ = "Development"

import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import glib

import json
import os
import subprocess

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
        self.data.setdefault('extra', '')
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
        self.in_extra = self.wTree.get_widget('in_extra')
        self.cb_dns = self.wTree.get_widget('cb_dns')
        self.cb_askpass = self.wTree.get_widget('cb_askpass')

        # Set default widget text
        self.in_name.set_text(self.data['name'])
        self.in_address.set_text(self.data['address'])
        self.in_subnet.set_text(self.data['subnet'])
        self.in_extra.set_text(self.data['extra'])
        self.cb_dns.set_active(self.data['use_dns'])
        self.cb_askpass.set_active(self.data['use_askpass'])

        # Show dialog
        self.result = self.dlg.run()

        # Fetch data from dialog
        self.data['name'] = self.in_name.get_text()
        self.data['address'] = self.in_address.get_text()
        self.data['subnet'] = self.in_subnet.get_text()
        self.data['extra'] = self.in_extra.get_text()
        self.data['use_dns'] = self.cb_dns.get_active()
        self.data['use_askpass'] = self.cb_askpass.get_active()

        # Kill dialog and return data
        self.dlg.destroy()
        return self.result, self.data


class MainApplication():

    settings = {
        "endpoints": {},
    }

    connecting = False
    disconnecting = False

    def __init__(self):
        if not os.path.exists(SETTINGS_FILE_PATH):
            os.system('touch {0}'.format(SETTINGS_FILE_PATH))
            self.save_settings()

        self.read_settings()

        self.ind = appindicator.Indicator("gtkuttle", "down",
                      appindicator.CATEGORY_APPLICATION_STATUS)
        self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.ind.set_label("gtkuttle")
        self.connected = self.session_is_open()

        self.menu = None
        self.build_menu()

        if self.connected:
            self.ind.set_icon('up')

        glib.timeout_add_seconds(3, self.timeout_operation)

    def timeout_operation(self):
        if self.connecting and self.session_is_open():
            self.connecting = False
            self.connected = True
            self.build_menu()
            self.ind.set_icon('up')

        elif self.disconnecting and not self.session_is_open():
            self.disconnecting = False
            self.build_menu()
            self.ind.set_icon('down')

        elif self.connected and not self.session_is_open():
            self.connected = False
            self.build_menu()
            self.ind.set_icon('crashed')

        glib.timeout_add_seconds(3, self.timeout_operation)

    def build_menu(self):
        self.menu = gtk.Menu()

        # render saved endpoints
        for name, endpoint in self.settings['endpoints'].iteritems():
            endpoint_item = gtk.MenuItem(name)
            endpoint_item.show()
            self.menu.append(endpoint_item)
            endpoint_item.connect('activate', self.endpoint_clicked)

        if len(self.settings['endpoints']):
            self.add_menu_seperator()

        for name, endpoint in self.settings['endpoints'].iteritems():
            edit_ep_item = gtk.MenuItem("Edit {0}".format(name))
            edit_ep_item.show()
            self.menu.append(edit_ep_item)
            edit_ep_item.connect('activate', self.edit_endpoint_clicked)

        if len(self.settings['endpoints']):
            self.add_menu_seperator()

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

        quitapp = gtk.MenuItem("Quit Gtkuttle")
        quitapp.show()
        self.menu.append(quitapp)
        quitapp.connect('activate', self.quit_app)

        self.menu.show()
        self.ind.set_menu(self.menu)

    def quit_app(self, widget=None):
        gtk.main_quit()

    def add_menu_seperator(self):
        seperator = gtk.SeparatorMenuItem()
        seperator.show()
        self.menu.append(seperator)

    def read_settings(self):
        with open(SETTINGS_FILE_PATH, "r") as f:
            self.settings = json.loads(f.read())

    def save_settings(self):
        with open(SETTINGS_FILE_PATH, "w") as f:
            f.write(json.dumps(self.settings))

    def disconnect_current_session(self, widget=None):
        self.connected = False

        with open(PID_FILE_PATH) as f:
            cmd = "gksu \"kill {0}\"".format(f.read().rstrip())
            subprocess.Popen(cmd, shell=True)

        self.ind.set_icon('landing')
        self.disconnecting = True

    def session_is_open(self):
        return os.path.exists(PID_FILE_PATH)

    def start_session(self, endpoint_data):
        if endpoint_data['use_askpass']:
            os.environ['SSH_ASKPASS'] = 'ssh-askpass'

        # Use setsid to force no terminal askpass
        cmdline = "setsid sshuttle -r {0} {1} {2} --daemon --pidfile {3}".format(
            endpoint_data['address'],
            endpoint_data['subnet'],
            "--dns" if endpoint_data['use_dns'] else "",
            PID_FILE_PATH
        )

        self.ind.set_icon('launching')
        subprocess.Popen('gksu "{0}"'.format(cmdline), shell=True)
        self.connecting = True

    def show_add_new_dialog(self, widget, initial_data={}):
        dialog = AddEndpointWindow(initial_data)
        result, data = dialog.run()

        if not data['name']:
            self.show_error("No name defined, try again")
            return

        self.settings['endpoints'][data['name']] = data
        self.save_settings()
        self.build_menu()


    def edit_endpoint_clicked(self, widget):
        ep_name = widget.get_label()
        try:
            # TODO: fix ugly [5:] hax
            endpoint = self.settings['endpoints'][ep_name[5:]]
            del self.settings['endpoints'][ep_name[5:]]
        except (IndexError, KeyError):
            self.show_error("Endpoint not found in saved endpoint data. Something went wrong...")
            return

        self.show_add_new_dialog(widget, initial_data=endpoint)

    def endpoint_clicked(self, widget):
        ep_name = widget.get_label()
        try:
            endpoint = self.settings['endpoints'][ep_name]
        except (IndexError, KeyError):
            self.show_error("Endpoint not found in saved endpoint data. Something went wrong...")
            return

        # Start sshuttle if no session is running.
        if self.session_is_open():
            resp = self.confirm_action("A session is already active. Cancel this session?")
            if resp:
                self.disconnect_current_session()
            else:
                return

        # Start session here
        self.start_session(endpoint)

    def run(self):
        gtk.main()
        return 0

    def show_error(self, message):
        error_dialog = gtk.MessageDialog(
            parent=None,
            flags=gtk.DIALOG_MODAL,
            message_format=message,
            type=gtk.MESSAGE_ERROR,
            buttons=gtk.BUTTONS_CLOSE
        )
        response = error_dialog.run()
        error_dialog.destroy()
        return response

    def confirm_action(self, message):
        confirm_dialog = gtk.MessageDialog(
            parent=None,
            flags=gtk.DIALOG_MODAL,
            message_format=message,
            type=gtk.MESSAGE_QUESTION,
            buttons=gtk.BUTTONS_YES_NO
        )

        response = confirm_dialog.run()
        confirm_dialog.hide()
        confirm_dialog.destroy()
        return response


if __name__ == "__main__":
    app = MainApplication()
    app.run()
