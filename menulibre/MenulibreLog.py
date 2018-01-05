#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2015 Sean Davis <smd.seandavis@gmail.com>
#   Copyright (C) 2017 OmegaPhil <OmegaPhil@startmail.com>
#
#   This program is free software: you can redistribute it and/or modify it
#   under the terms of the GNU General Public License version 3, as published
#   by the Free Software Foundation.
#
#   This program is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranties of
#   MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import subprocess

from gi.repository import Gdk, Gio, Gtk

import menulibre_lib


class LogDialog:
    """The MenuLibre LogWindow."""

    def __init__(self, parent):
        """Initialize all values."""
        self._parent = parent

        builder = menulibre_lib.get_builder('MenulibreWindow')

        self._log_dialog = builder.get_object('log_dialog')
        self._log_ok = builder.get_object('log_ok')
        self._log_treeview = builder.get_object('log_treeview')

        # Connect the signals for the treeview
        self._log_treeview.connect("button-press-event",
                                   self.button_press_event_cb)
        self._log_treeview.connect("row-activated", self.row_activated_cb)

        # Connect the signal to destroy the LogDialog when OK is clicked
        self._log_ok.connect("clicked", self.log_close_cb)

        self._log_dialog.set_transient_for(parent)

    def add_item(self, filename, error):
        model = self._log_treeview.get_model()
        model.append(["<b>%s</b>\n%s" % (filename, error),
                      filename])

    def get_editor_executable(self):
        info = Gio.AppInfo.get_default_for_type("text/plain", False)
        if info is not None:
            return info.get_executable()
        return None

    def button_press_event_cb(self, widget, event):
        pos = self._log_treeview.get_path_at_pos(event.x, event.y)
        if pos is not None:
            treepath, treecol, cell_x, cell_y = pos
            treeiter = self._log_treeview.get_model().get_iter(treepath)
            treecol_name = treecol.get_name()
            filename = self._log_treeview.get_model()[treeiter][1]

            if treecol_name == "log_action_file":
                self.row_activated_cb(self._log_treeview, treepath, treecol)
            if treecol_name == "log_action_directory":
                dirname = os.path.dirname(filename)
                uri = "file://%s" % dirname
                if "show_uri_on_window" in dir(Gtk):
                    Gtk.show_uri_on_window(None, uri, 0)
                else:
                    Gtk.show_uri(None, uri, 0)
            if treecol_name == "log_action_copy":
                clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
                clipboard.set_text(filename, -1)

    def row_activated_cb(self, treeview, path, column):
        treeiter = self._log_treeview.get_model().get_iter(path)
        filename = self._log_treeview.get_model()[treeiter][1]
        binary = self.get_editor_executable()
        subprocess.Popen([binary, filename])

    def log_close_cb(self, widget):
        """Destroy the LogDialog when it is OK'd."""
        self._log_dialog.destroy()

    def set_text(self, text):
        """Set the text to show in the log dialog."""
        self._log_textbuffer.set_text(text)

    def show(self):
        """Show the log dialog."""
        self._log_dialog.show()
