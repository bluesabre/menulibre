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

from gi.repository import Gtk, GObject


class Toolbar(Gtk.Toolbar):

    def __init__(self):
        super().__init__()
        self.set_show_arrow(False)

        context = self.get_style_context()
        context.add_class("primary-toolbar")

    def add_menu_button(self, icon_name, menu):
        item = Gtk.ToolItem.new()

        image = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
        image.set_pixel_size(24)

        button = Gtk.MenuButton.new()
        button.set_popup(menu)
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.add(image)

        context = button.get_style_context()
        context.add_class("toolbutton")

        item.add(button)
        self.add(item)

        return item

    def add_separator(self):
        separator = Gtk.SeparatorToolItem.new()
        self.add(separator)
        return separator

    def add_button(self, icon_name, label):
        image = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
        image.set_pixel_size(24)

        item = Gtk.ToolButton.new(image, label)

        self.add(item)

        return item

    def add_search(self, widget):
        item = Gtk.ToolItem.new()

        item.add(widget)
        self.add(item)

        return item
