#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2023 Sean Davis <sean@bluesabre.org>
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

import logging
import os
import subprocess
import shlex

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gio, Gtk, GLib  # type: ignore


logger = logging.getLogger('menulibre')


class FileHandler:

    def open_folder(self, path):
        if not os.path.isdir(path):
            path = os.path.dirname(path)

        uri = "file://%s" % path

        if "show_uri_on_window" in dir(Gtk):
            Gtk.show_uri_on_window(None, uri, 0)
        else:
            Gtk.show_uri(None, uri, 0)

        return True

    def open_editor(self, path):
        if os.path.isdir(path):
            return self.open_folder(path)

        file = self._get_file(path)

        if not self._file_is_writable(file):
            admin = self._get_preferred_admin_editor()
            if admin is not None:
                return admin.launch(
                    [self._get_file("admin://%s" % file.get_path())])

            logging.warning(
                "Could not find a text editor supporting admin://")

            root = self._get_root_editor()
            if root is not None:
                return root.launch([file])

            logging.warning(
                "Could not find a text editor supporting pkexec")

        editor = self._get_editor()
        if editor is not None:
            return editor.launch([file])

        logging.warning(
            "Could not find a supported text editor")

        return False

    def copy_to_clipboard(self, path):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(path, -1)

    def _get_file(self, path):
        if "://" in path:
            return Gio.File.new_for_uri(path)
        else:
            return Gio.File.new_for_path(path)

    def _file_is_writable(self, file: Gio.File):
        try:
            info = file.query_info(
                Gio.FILE_ATTRIBUTE_ACCESS_CAN_WRITE,
                Gio.FileQueryInfoFlags.NONE,
                None)
            return info.get_attribute_boolean(
                Gio.FILE_ATTRIBUTE_ACCESS_CAN_WRITE)
        except BaseException:
            return False

    def _get_preferred_admin_editor(self):
        default = self._get_editor()
        if self._editor_supports_admin_protocol(default):
            return default
        for editor in self._get_editors():
            if self._editor_supports_admin_protocol(editor):
                return editor
        return None

    def _get_editor(self):
        info = Gio.AppInfo.get_default_for_type("text/plain", False)
        if info is not None:
            return info
        return None

    def _get_editors(self):
        execs = {}
        infos = Gio.AppInfo.get_all_for_type("text/plain")
        for info in infos:
            appid = info.get_id()
            if appid is not None:
                appid = appid[:-8]
                execs[appid] = info
        return execs

    def _editor_supports_admin_protocol(self, editor):
        return editor in [
            "gedit",
            "pluma"
        ]

    def _get_keyfile(self, editor: Gio.AppInfo):
        app_id = editor.get_id()
        fname = app_id

        keyfile = GLib.KeyFile.new()

        data_dirs = [GLib.get_user_data_dir()] + GLib.get_system_data_dirs()
        for data_dir in data_dirs:
            for path, directories, files in os.walk(data_dir):
                if fname in files:
                    filename = os.path.join(data_dir, path, fname)
                    if keyfile.load_from_file(
                            filename, GLib.KeyFileFlags.NONE):
                        return keyfile

        return None

    def _get_pkexec_editor(self, editor: Gio.AppInfo, pkexec: str):
        keyfile = self._get_keyfile(editor)
        if keyfile is None:
            return None

        try:
            commandline = keyfile.get_string("Desktop Entry", "Exec")
            command = shlex.join([pkexec] + shlex.split(commandline))
            keyfile.set_string("Desktop Entry", "Exec", command)
        except GLib.Error:
            return None

        desktop = Gio.DesktopAppInfo.new_from_keyfile(keyfile)
        if desktop is None:
            return None

        return desktop

    def _get_root_editor(self):
        pkexec_bin = GLib.find_program_in_path("pkexec")
        if pkexec_bin is None:
            logging.warning(
                "Could not find pkexec to for executing root editors")
            return None
        if self._get_display_server() == "wayland":
            logging.warning(
                "pkexec is not supported under Wayland")
            return None
        pkexecs = self._get_pkexecs()
        default = self._get_editor()
        preferred = None
        for appid, editor in self._get_editors().items():
            for pkexec in pkexecs:
                if pkexec == appid or pkexec == "org.freedesktop.policykit.pkexec.%s" % appid:
                    if default is not None and editor.get_id() == default.get_id():
                        return self._get_pkexec_editor(editor, pkexec_bin)
                    if preferred is None:
                        preferred = editor
        if preferred is not None:
            return self._get_pkexec_editor(preferred, pkexec_bin)
        if default is not None and default.get_id() not in ["code.desktop"]:
            return self._get_pkexec_editor(default, pkexec_bin)
        logging.warning(
            "Could not find a text editor supporting pkexec")
        return None

    def _get_display_server(self):
        wayland = os.getenv("WAYLAND_DISPLAY")
        if wayland is not None:
            return "wayland"
        x11 = os.getenv("DISPLAY")
        if x11 is not None:
            return "x11"
        logging.warning(
            "Could not determine display server. Assuming x11")
        return "x11"

    def _get_pkexecs(self):
        try:
            output = subprocess.check_output(
                ["pkaction"], stderr=subprocess.STDOUT)
        except Exception as e:
            output = e.output  # type: ignore
        try:
            return output.decode('utf-8').split("\n")
        except BaseException:
            return []
