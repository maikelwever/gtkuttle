gtkuttle
========

A GTK sshuttle GUI with tray icon, written in Python.

Requirements
------------

* PyGTK2
* gksudo
* sshuttle in $PATH


Optional requirements
---------------------

* (x11-)ssh-askpass if you don't use keys for your ssh session (this was present by default on my Ubuntu installation)


Notes
-----

I've created this on Manjaro Linux with Cinnamon Desktop (an Arch Linux devirative), which copes well with launching sshuttle under gksu.
However, my Ubuntu 12.04 laptop with Gnome3 does not like this. Quickfix: launch gtkuttle as root (sounds nasty, not?).


Legal matter
------------

This software is licensed under the GNU GPL v3. See the LICENSE file for details. You can contribute back your changes to https://github.com/maikelwever/gtkuttle/.
