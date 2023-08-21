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

from .TextEntry import TextEntry
import os
import subprocess
from locale import gettext as _

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib  # type: ignore


class StartupWmClassEntry(TextEntry):
    def __init__(self, property_name, use_headerbar):
        super().__init__(property_name=property_name)

        xprop = GLib.find_program_in_path("xprop")
        if xprop is not None:
            self.set_icon_from_icon_name(
                Gtk.EntryIconPosition.SECONDARY, 'edit-find-symbolic')
            self.set_icon_tooltip_text(
                Gtk.EntryIconPosition.SECONDARY,
                _('Identify Window')
            )
            self.connect(
                'icon-press', self._on_icon_press, xprop, use_headerbar)

    def _on_icon_press(self, entry, icon, event, xprop, use_headerbar):
        dialog = XpropWindowDialog(self.get_toplevel(), xprop, use_headerbar)
        wm_classes = dialog.run_xprop()
        current = entry.get_text()
        for wm_class in wm_classes:
            if wm_class != current:
                self.set_value(wm_class)
                return


class XpropWindowDialog(Gtk.MessageDialog):
    def __init__(self, parent, xprop_binary, use_headerbar):
        # Translators: Identify Window Dialog, primary text.
        primary = _("Identify Window")
        # Translators: Identify Window Dialog, secondary text. The selected
        # application is displayed in the placeholder text.
        secondary = _(
            "Click on the main application window for this launcher.")

        Gtk.MessageDialog.__init__(self, transient_for=parent, modal=True,
                                   message_type=Gtk.MessageType.INFO,
                                   buttons=Gtk.ButtonsType.OK,
                                   text=primary, use_header_bar=False)
        self.format_secondary_markup(secondary)

        self.binary = xprop_binary
        self.process = None
        self.classes = []

    def run_xprop(self):
        GLib.timeout_add(500, self.start_xprop)
        self.run()
        self.classes.sort()
        return self.classes

    def start_xprop(self):
        cmd = [self.binary, 'WM_CLASS']
        self.classes = []
        env = os.environ.copy()
        self.process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
        )
        GLib.idle_add(self.check_xprop)
        return False

    def check_xprop(self):
        if self.process is None:
            return True
        if self.process.poll() is None:
            return True
        if self.process.stdout is None:
            return True
        output = self.process.stdout.read().decode('UTF-8').strip()
        if output.startswith("WM_CLASS"):
            values = output.split("=", 1)[1].split(", ")
            for value in values:
                value = value.strip()
                value = value[1:-1]
                if value not in self.classes:
                    self.classes.append(value)
        self.destroy()
        return False
