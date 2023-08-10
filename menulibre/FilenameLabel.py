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

from locale import gettext as _

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango, GObject

class FilenameLabel(Gtk.EventBox):
    __gsignals__ = {
        'value-changed': (GObject.SignalFlags.RUN_FIRST, None, (str, str,)),
    }

    def __init__(self):
        super().__init__()
        self._value = None

        box = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        self.add(box)

        self._label = Gtk.Label.new("")
        self._label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self._label.set_xalign(0.0)
        self._label.set_yalign(1.0)

        attributes = Pango.AttrList.new()
        attributes.insert(Pango.attr_style_new(Pango.Style.ITALIC))
        attributes.insert(Pango.attr_weight_new(Pango.Weight.NORMAL))
        self._label.set_attributes(attributes)

        box.add(self._label)

        button = Gtk.Button.new_from_icon_name("edit-copy-symbolic", Gtk.IconSize.BUTTON)
        button.set_name('copybutton')
        button.set_opacity(0.0)
        button.set_tooltip_text(_("Copy"))

        context = button.get_style_context()
        context.add_class("flat")

        screen = Gdk.Screen.get_default()
        provider = Gtk.CssProvider()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        provider.load_from_data("#copybutton {padding: 0; border-radius: 0; min-height: 18px; min-width: 18px;}".encode())

        box.add(button)

        self.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)

        self._label_entered = False
        self._button_entered = False

        self.connect("enter-notify-event", self._enter_notify_cb, button)
        self.connect("leave-notify-event", self._leave_notify_cb, button)

        button.connect("enter-notify-event", self._button_enter_notify_cb, button)
        button.connect("leave-notify-event", self._button_leave_notify_cb, button)

        button.connect("clicked", self._button_clicked_cb)


    def set_value(self, value):
        if value is None or value == "":
            value = None
            text = ""
        else:
            text = value
        self._label.set_text(text)
        self._label.set_tooltip_text(text)
        self._value = value
        self.emit('value-changed', 'Filename', self._value)

    def get_value(self):
        return self._value
    
    def toggle_button_visibility(self, button):
        if self._label_entered or self._button_entered:
            button.set_opacity(1.0)
        else:
            button.set_opacity(0.0)

    def _enter_notify_cb(self, widget, event, button):
        self._label_entered = True
        self.toggle_button_visibility(button)

    def _leave_notify_cb(self, widget, event, button):
        self._label_entered = False
        self.toggle_button_visibility(button)

    def _button_enter_notify_cb(self, widget, event, button):
        self._button_entered = True
        self.toggle_button_visibility(button)

    def _button_leave_notify_cb(self, widget, event, button):
        self._button_entered = False
        self.toggle_button_visibility(button)

    def _button_clicked_cb(self, widget):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(self._value, -1)
