#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2024 Sean Davis <sean@bluesabre.org>
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

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject  # type: ignore


class SwitchEntry(Gtk.Switch):
    __gsignals__ = {
        'value-changed': (GObject.SignalFlags.RUN_FIRST, None, (str, str,)),
    }

    def __init__(self, property_name):
        super().__init__()
        self._property_name = property_name

        self.set_halign(Gtk.Align.END)
        self.set_valign(Gtk.Align.CENTER)
        self.set_margin_end(1)

        self.connect('notify::active', self._on_changed)

    def set_value(self, value):
        self.set_active(value)

    def get_value(self):
        return self.get_active()

    def _on_changed(self, status, widget):
        self.emit('value-changed', self._property_name, self.get_value())
