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
from gi.repository import Gtk, Pango  # type: ignore


class Section(Gtk.Frame):

    def __init__(self, label):
        super().__init__(label=label)

        label = self.get_label_widget()

        if label is not None:
            attributes = Pango.AttrList.new()
            attributes.insert(Pango.attr_weight_new(Pango.Weight.BOLD))
            label.set_attributes(attributes)  # type: ignore

        self.set_shadow_type(Gtk.ShadowType.NONE)
