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
from .LabelWithHidingButton import LabelWithHidingButton

import menulibre_lib

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango, GObject

class FieldLabel(LabelWithHidingButton):
    __gsignals__ = {
        'value-changed': (GObject.SignalFlags.RUN_FIRST, None, (str, str,)),
    }

    def __init__(self, label, key_name, description, help_text = None, help_url = None):
        super().__init__(label=label, icon_name="dialog-question-symbolic", icon_size=Gtk.IconSize.BUTTON)
        self._value = None

        label = self.get_label()
        label.set_ellipsize(Pango.EllipsizeMode.NONE)

        button = self.get_button()
        button.set_tooltip_markup(_("More information about <i>%s</i>") % key_name)
        button.connect("clicked", self._button_clicked_cb, key_name, description, help_text, help_url)

    def _button_clicked_cb(self, widget, key_name, description, help_text, help_url):
        dlg = FieldInfo(self.get_toplevel(), key_name=key_name, description=description, help_text=help_text, help_url=help_url)
        dlg.show()


class FieldInfo(Gtk.MessageDialog):
    def __init__(self, parent, key_name, description, help_text, help_url):
        primary = key_name
        secondary = description

        Gtk.MessageDialog.__init__(self, transient_for=parent, modal=True,
                                   message_type=Gtk.MessageType.ERROR,
                                   buttons=Gtk.ButtonsType.CLOSE,
                                   text=primary, use_header_bar=False)
        self.format_secondary_markup(secondary)

        message_area = self.get_content_area().get_children()[0]
        if isinstance(message_area.get_children()[0], Gtk.Image):
            message_area.get_children()[0].destroy()

        if help_text:
            button = self.add_button(help_text, Gtk.ResponseType.HELP)
            bbox = self.get_action_area()
            bbox.set_child_secondary(button, True)

        self.connect("response", self.response_cb, help_url)

    def response_cb(self, widget, response, help_url):
        if response == Gtk.ResponseType.HELP:
            menulibre_lib.show_uri(self.get_transient_for(), help_url)
            return
        widget.destroy()
