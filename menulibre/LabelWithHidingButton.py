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
from gi.repository import Gtk, Gdk

class LabelWithHidingButton(Gtk.EventBox):

    def __init__(self, label, icon_name, icon_size):
        super().__init__()

        box = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        self.add(box)

        self._label = Gtk.Label.new(label)
        self._label.set_xalign(0.0)

        box.add(self._label)

        self._button = Gtk.Button.new_from_icon_name(icon_name, icon_size)
        self._button.set_name('hideybutton')
        self._button.set_opacity(0.0)

        context = self._button.get_style_context()
        context.add_class("flat")

        screen = Gdk.Screen.get_default()
        provider = Gtk.CssProvider()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        provider.load_from_data(
            "#hideybutton {padding: 0; border-radius: 0; min-height: 18px; min-width: 18px;}".encode())

        box.add(self._button)

        self.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK |
                        Gdk.EventMask.LEAVE_NOTIFY_MASK)

        self._label_entered = False
        self._button_entered = False
        self._button_focused = False

        self.connect("enter-notify-event", self._enter_notify_cb, self._button)
        self.connect("leave-notify-event", self._leave_notify_cb, self._button)

        self._button.connect(
            "enter-notify-event",
            self._button_enter_notify_cb,
            self._button)
        self._button.connect(
            "leave-notify-event",
            self._button_leave_notify_cb,
            self._button)

        self._button.connect(
            "focus-in-event",
            self._button_focus_in_cb,
            self._button)
        self._button.connect(
            "focus-out-event",
            self._button_focus_out_cb,
            self._button)

    def get_button(self):
        return self._button

    def get_label(self):
        return self._label

    def _toggle_button_visibility(self, button):
        if self._label_entered or self._button_entered or self._button_focused:
            button.set_opacity(1.0)
        else:
            button.set_opacity(0.0)

    def _enter_notify_cb(self, widget, event, button):
        self._label_entered = True
        self._toggle_button_visibility(button)

    def _leave_notify_cb(self, widget, event, button):
        self._label_entered = False
        self._toggle_button_visibility(button)

    def _button_enter_notify_cb(self, widget, event, button):
        self._button_entered = True
        self._toggle_button_visibility(button)

    def _button_leave_notify_cb(self, widget, event, button):
        self._button_entered = False
        self._toggle_button_visibility(button)

    def _button_focus_in_cb(self, widget, event, button):
        self._button_focused = True
        self._toggle_button_visibility(button)

    def _button_focus_out_cb(self, widget, event, button):
        self._button_focused = False
        self._toggle_button_visibility(button)
