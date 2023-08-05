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


class Headerbar(Gtk.HeaderBar):

    def __init__(self):
        super().__init__()

        self.set_title("MenuLibre")
        self.set_custom_title(Gtk.Label.new())
        self.set_show_close_button(True)

    def add_menu_button(self, icon_name, label, menu):
        image = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
        image.set_pixel_size(16)
        image.set_property('use-fallback', True)

        button = Gtk.MenuButton.new()
        button.set_menu_model(menu)
        button.set_use_popover(True)
        button.set_tooltip_text(label)
        button.add(image)

        self.add(button)

        return button

    def add_button(self, icon_name, label):
        item = Gtk.Button.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
        item.set_tooltip_text(label)

        image = item.get_image()
        image.set_property('use-fallback', True)

        self.add(item)

        return item

    def add_buttons(self, button_specs):
        box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)

        context = box.get_style_context()
        context.add_class("linked")

        items = []

        for icon_name, label in button_specs:
            item = Gtk.Button.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
            item.set_tooltip_text(label)
            image = item.get_image()
            image.set_property('use-fallback', True)
            box.add(item)
            items.append(item)

        self.add(box)

        return items

    def add_search(self, widget):
        # Need to insert on right side
        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        box.set_valign(Gtk.Align.CENTER)

        box.add(widget)
        self.pack_end(box)

        return box
