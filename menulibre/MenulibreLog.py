#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2021 Sean Davis <sean@bluesabre.org>
#   Copyright (C) 2017-2018 OmegaPhil <OmegaPhil@startmail.com>
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
from . util import find_program

import logging

logger = logging.getLogger('menulibre')


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
        self._log_treeview.connect("row-activated", self.row_activated_cb)
        self._log_treeview.connect("button-release-event",
                                   self.button_release_event_cb)
        self._log_treeview.connect("motion-notify-event",
                                   self.motion_notify_event_cb)
        self._log_treeview.connect("enter-notify-event",
                                   self.enter_notify_event_cb)
        self._log_treeview.connect("leave-notify-event",
                                   self.leave_notify_event_cb)

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
    
    def get_pkexecs(self):
        try:
            output = subprocess.check_output(["pkaction"], stderr=subprocess.STDOUT)
        except Exception as e:
            output = e.output
        try:
            return output.decode('utf-8').split("\n")
        except:
            return []

    def get_editor_executables(self):
        execs = {}
        infos = Gio.AppInfo.get_all_for_type("text/plain")
        for info in infos:
            executable = info.get_executable()
            appid = info.get_id()
            appid = appid[:-8]
            execs[appid] = executable
        return execs
    
    def get_display_server(self):
        wayland = os.getenv("WAYLAND_DISPLAY")
        if wayland is not None:
            return "wayland"
        x11 = os.getenv("DISPLAY")
        if x11 is not None:
            return "x11"
        logging.warning(
            "Could not determine display server. Assuming x11")
        return "x11"

    def get_root_editor_executable(self):
        if not find_program("pkexec"):
            logging.warning(
                "Could not find pkexec to for executing root editors")
            return None
        if self.get_display_server() == "wayland":
            logging.warning(
                "pkexec is not supported under Wayland")
            return None
        pkexecs = self.get_pkexecs()
        default = self.get_editor_executable()
        preferred = None
        for appid, executable in self.get_editor_executables().items():
            for pkexec in pkexecs:
                if pkexec == appid or pkexec == "org.freedesktop.policykit.pkexec.%s" % appid:
                    if executable == default:
                        return executable
                    if preferred is None:
                        preferred = executable
        if preferred is not None:
            return preferred
        if default is None:
            logging.warning(
                "Could not find a text editor supporting pkexec")
        return default

    def file_is_writable(self, path):
        try:
            gfile = Gio.File.new_for_path(path)
            info = gfile.query_info(Gio.FILE_ATTRIBUTE_ACCESS_CAN_WRITE, Gio.FileQueryInfoFlags.NONE, None)
            return info.get_attribute_boolean(Gio.FILE_ATTRIBUTE_ACCESS_CAN_WRITE)
        except:
            return False
    
    def editor_supports_admin_protocol(self, binary):
        return binary in [
            "gedit",
            "pluma"
        ]
    
    def get_preferred_admin_editor(self):
        default = self.get_editor_executable()
        if self.editor_supports_admin_protocol(default):
            return default
        for editor in self.get_editor_executables():
            if self.editor_supports_admin_protocol(editor):
                return editor
        return None

    def view_path(self, path):
        if os.path.isdir(path):
            uri = "file://%s" % path
            if "show_uri_on_window" in dir(Gtk):
                Gtk.show_uri_on_window(None, uri, 0)
            else:
                Gtk.show_uri(None, uri, 0)
            return True
        else:
            binary = self.get_editor_executable()

            if not self.file_is_writable(path):
                admin = self.get_preferred_admin_editor()
                if admin is not None:
                    subprocess.Popen([admin, "admin://%s" % path])
                    return True

                logging.warning(
                    "Could not find a text editor supporting admin://")
                
                root = self.get_root_editor_executable()
                if root is not None:
                    subprocess.Popen(["pkexec", root, path])
                    return True

                logging.warning(
                    "Could not find a text editor supporting pkexec")
            
            if binary is not None:
                subprocess.Popen([binary, path])
                return True

            logging.warning(
                "Could not find a supported text editor")

            return False

    def get_path_details_at_pos(self, x, y):
        pos = self._log_treeview.get_path_at_pos(x, y)

        if pos is None:
            return None

        treepath, treecol, cell_x, cell_y = pos
        treeiter = self._log_treeview.get_model().get_iter(treepath)
        treecol_name = treecol.get_name()
        filename = self._log_treeview.get_model()[treeiter][1]

        return {"path": treepath, "column": treecol, "x": cell_x, "y": cell_y,
                "iter": treeiter, "column_name": treecol_name,
                "filename": filename}

    def button_release_event_cb(self, widget, event):
        details = self.get_path_details_at_pos(event.x, event.y)
        if details is not None:
            if details["column_name"] == "log_action_file":
                self.view_path(details["filename"])
            if details["column_name"] == "log_action_directory":
                self.view_path(os.path.dirname(details["filename"]))
            if details["column_name"] == "log_action_copy":
                self.set_clipboard(details["filename"])

    def set_cursor(self, cursor=None):
        if cursor is not None:
            cursor = Gdk.Cursor(Gdk.CursorType.HAND1)
        self._log_dialog.get_window().set_cursor(cursor)
        return True

    def set_clipboard(self, text):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text, -1)

    def motion_notify_event_cb(self, widget, event):
        details = self.get_path_details_at_pos(event.x, event.y)
        if details is not None and details["column_name"] != "log_text":
            return self.set_cursor(Gdk.CursorType.HAND1)
        return self.set_cursor(None)

    def enter_notify_event_cb(self, widget, event):
        details = self.get_path_details_at_pos(event.x, event.y)
        if details is not None and details["column_name"] != "log_text":
            return self.set_cursor(Gdk.CursorType.HAND1)
        return self.set_cursor(None)

    def leave_notify_event_cb(self, widget, event):
        self.set_cursor(None)

    def row_activated_cb(self, treeview, path, column):
        treeiter = self._log_treeview.get_model().get_iter(path)
        filename = self._log_treeview.get_model()[treeiter][1]
        self.view_path(filename)

    def log_close_cb(self, widget):
        """Destroy the LogDialog when it is OK'd."""
        self._log_dialog.destroy()

    def show(self):
        """Show the log dialog."""
        self._log_dialog.show()
