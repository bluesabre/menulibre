#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2023 Sean Davis <sean@bluesabre.org>
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
import shlex

from . util import find_program

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gdk, Gio, Gtk

import logging

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

        if not self._file_is_writable(path):
            admin = self._get_preferred_admin_editor()
            if admin is not None:
                return admin.launch([self._get_file("admin://%s" % path)])

            logging.warning(
                "Could not find a text editor supporting admin://")

            root = self._get_root_editor()
            if root is not None:
                command = self._get_command(root, path, True)
                subprocess.Popen(command)
                return True

            logging.warning(
                "Could not find a text editor supporting pkexec")

        editor = self._get_editor()
        if editor is not None:
            return editor.launch([self._get_file(path)])

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

    def _get_command(self, appinfo, path, pkexec=False):
        commandline = appinfo.get_commandline()

        supports_uri = "%u" in commandline or "%U" in commandline
        supports_path = "%f" in commandline or "%F" in commandline

        file = self._get_file(path)
        uri = file.get_uri()
        path = file.get_path()

        find = replace = append = None

        if supports_uri and "%u" in commandline:
            find = "%u"
            replace = uri
        elif supports_uri and "%U" in commandline:
            find = "%U"
            replace = uri
        elif supports_path and "%f" in commandline:
            find = "%f"
            replace = path
        elif supports_path and "%F" in commandline:
            find = "%F"
            replace = path
        else:
            append = path

        command = []

        if find is not None:
            for part in shlex.split(commandline):
                if part == find:
                    command.append(replace)
                else:
                    command.append(part)
        else:
            command = shlex.split(commandline)
            command.append(append)

        if pkexec:
            command = ["pkexec"] + command

        return command


    def _file_is_writable(self, path):
        try:
            gfile = Gio.File.new_for_path(path)
            info = gfile.query_info(Gio.FILE_ATTRIBUTE_ACCESS_CAN_WRITE, Gio.FileQueryInfoFlags.NONE, None)
            return info.get_attribute_boolean(Gio.FILE_ATTRIBUTE_ACCESS_CAN_WRITE)
        except:
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
            executable = info.get_commandline()
            appid = info.get_id()
            appid = appid[:-8]
            execs[appid] = info
        return execs
    
    def _editor_supports_admin_protocol(self, editor):
        return editor.get_executable() in [
            "gedit",
            "pluma"
        ]
    
    def _get_root_editor(self):
        if not find_program("pkexec"):
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
                    if editor.get_id() == default.get_id():
                        return editor
                    if preferred is None:
                        preferred = editor
        if preferred is not None:
            return preferred
        if default is None:
            logging.warning(
                "Could not find a text editor supporting pkexec")
        return default
    
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
            output = subprocess.check_output(["pkaction"], stderr=subprocess.STDOUT)
        except Exception as e:
            output = e.output
        try:
            return output.decode('utf-8').split("\n")
        except:
            return []
