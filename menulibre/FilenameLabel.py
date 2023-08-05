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

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango, GObject


class FilenameLabel(Gtk.Label):
    __gsignals__ = {
        'value-changed': (GObject.SignalFlags.RUN_FIRST, None, (str, str,)),
    }

    def __init__(self):
        super().__init__()
        self._value = None

        self.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self.set_xalign(0.0)

        attributes = Pango.AttrList.new()
        attributes.insert(Pango.attr_style_new(Pango.Style.ITALIC))
        attributes.insert(Pango.attr_weight_new(Pango.Weight.NORMAL))
        self.set_attributes(attributes)

    def set_value(self, value):
        if value is None or value == "":
            value = None
            text = ""
        else:
            text = value
        self.set_text(text)
        self.set_tooltip_text(text)
        self._value = value
        self.emit('value-changed', 'Filename', self._value)

    def get_value(self):
        return self._value
