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

from locale import gettext as _

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango, GObject  # type: ignore


class TextEntryButton(Gtk.Stack):
    __gsignals__ = {
        'value-changed': (GObject.SignalFlags.RUN_FIRST, None, (str, str,)),
    }

    def __init__(
            self,
            property_name,
            bold_font=False,
            required=False,
            placeholder_text=""):
        super().__init__()
        self._property_name = property_name
        self._value = ""
        self._required = required
        self._placeholder_text = placeholder_text
        self._bold_font = bold_font

        self._button = Gtk.Button.new()
        self._button.connect('clicked', self._on_clicked)
        self._button.set_relief(Gtk.ReliefStyle.NONE)
        self._button.connect('focus-in-event', self._on_button_focus_in)
        self._button.connect('focus-out-event', self._on_button_focus_out)
        self.add(self._button)

        self._label = Gtk.Label.new("")
        self._label.set_xalign(0.0)
        self._label.set_ellipsize(Pango.EllipsizeMode.END)
        self._button.add(self._label)

        self._entry = Gtk.Entry.new()
        self._entry.set_placeholder_text(placeholder_text)
        self._entry.connect('key-press-event', self._on_entry_key_press)
        self._entry.connect('activate', self._on_entry_activate)
        self._entry.connect('changed', self._on_entry_changed)
        self._entry.connect('icon-press', self._on_entry_icon_press)
        self.add(self._entry)

        self.set_homogeneous(True)

        self._on_entry_changed(self._entry)

    def set_value(self, value):
        if value is None:
            value = ""
        value = value.strip()
        self._value = value
        self._entry.set_text(value)
        attributes = Pango.AttrList.new()
        if len(value) > 0:
            self._label.set_text(value)
            attributes.insert(Pango.attr_style_new(Pango.Style.NORMAL))
            if self._bold_font:
                attributes.insert(Pango.attr_weight_new(Pango.Weight.BOLD))
                attributes.insert(Pango.attr_size_new(12000))
        else:
            self._label.set_text(self._placeholder_text)
            attributes.insert(Pango.attr_style_new(Pango.Style.ITALIC))
            attributes.insert(Pango.attr_weight_new(Pango.Weight.NORMAL))
        self._label.set_attributes(attributes)
        self.set_visible_child(self._button)
        self.emit('value-changed', self._property_name, self._value)

    def get_value(self):
        return self._entry.get_text()

    def _on_button_focus_in(self, button, event):
        button.set_relief(Gtk.ReliefStyle.NORMAL)

    def _on_button_focus_out(self, button, event):
        button.set_relief(Gtk.ReliefStyle.NONE)

    def _on_clicked(self, button):
        self.set_visible_child(self._entry)
        self._entry.grab_focus()

    def commit(self):
        if self._entry.get_icon_name(
                Gtk.EntryIconPosition.SECONDARY) == "gtk-apply":
            self.set_value(self._entry.get_text().strip())
        else:
            self.cancel()

    def cancel(self):
        self.set_visible_child(self._button)
        self._entry.set_text(self._value)

    def _on_entry_key_press(self, entry, event):
        keyval_name = Gdk.keyval_name(event.get_keyval()[1])
        if keyval_name is None:
            return
        if keyval_name.lower() == 'escape':
            self.cancel()
            self._button.grab_focus()

    def _on_entry_activate(self, entry):
        if entry.get_icon_name(Gtk.EntryIconPosition.SECONDARY) == "gtk-apply":
            self.commit()
            self._button.grab_focus()
        else:
            self.cancel()

    def _on_entry_changed(self, entry):
        text = entry.get_text().strip()
        if self._required and len(text) == 0:
            entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY,
                                          "gtk-cancel")
        else:
            entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY,
                                          "gtk-apply")

    def _on_entry_icon_press(self, entry, icon_pos, event):
        self._on_entry_activate(entry)
