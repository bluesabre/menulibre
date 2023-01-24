#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2022 Sean Davis <sean@bluesabre.org>
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

from gi.repository import Gtk, Gio
from locale import gettext as _
import shlex

import menulibre_lib


class ExecEditor:
    """The MenuLibre ExecEditor."""

    def __init__(self, parent):
        """Initialize all values."""
        self._parent = parent
        self._dialog = None
        self._entry = None
        self._hint_env_img = None
        self._hint_env_label = None
        self._hint_cmd_img = None
        self._hint_cmd_label = None
        self._hint_field_img = None
        self._hint_field_label = None
        self._before = ""

    def edit(self, commandline):
        """Open a selection dialog to choose an icon."""
        response = commandline
        dialog = self._get_dialog()
        self._entry.set_text(commandline)
        if dialog.run() == Gtk.ResponseType.APPLY:
            response = self._entry.get_text()
        dialog.hide()
        return response

    def _get_dialog(self):
        """Get the icon selection dialog."""
        builder = menulibre_lib.get_builder('ExecEditor')

        if self._dialog is not None:
            return self._dialog

        self._dialog = builder.get_object('ExecEditorDialog')
        self._entry = builder.get_object('exec_editor_entry')
        self._hint_env_img = builder.get_object('hint_env_img')
        self._hint_env_label = builder.get_object('hint_env_label')
        self._hint_cmd_img = builder.get_object('hint_cmd_img')
        self._hint_cmd_label = builder.get_object('hint_cmd_label')
        self._hint_field_img = builder.get_object('hint_cmd_img')
        self._hint_field_label = builder.get_object('hint_cmd_label')

        applications_store = builder.get_object('application_list')

        app_list = []
        infos = Gio.AppInfo.get_all()
        for info in infos:
            executable = info.get_executable()
            icon = info.get_icon()
            name = info.get_name()
            app_list.append([name, executable, icon])

        app_list = sorted(app_list, key = lambda x: x[0].lower())

        for app in app_list:
            applications_store.append(app)

        var_entry = builder.get_object('env_var_entry')
        val_entry = builder.get_object('env_val_entry')
        popover = builder.get_object('popover_env')

        var_entry.connect('changed', self.on_env_var_entry_changed, val_entry)
        val_entry.connect('changed', self.on_env_val_entry_changed)

        var_entry.connect('activate', self.on_env_var_activate, var_entry, val_entry, popover)
        val_entry.connect('activate', self.on_env_var_activate, var_entry, val_entry, popover)

        return self._dialog


    def on_env_var_activate(self, widget, var_entry, val_entry, popover):
        if var_entry.get_icon_name(Gtk.EntryIconPosition.SECONDARY) != "gtk-apply":
            return
        if val_entry.get_icon_name(Gtk.EntryIconPosition.SECONDARY) != "gtk-apply":
            return

        var = var_entry.get_text().strip()
        val = val_entry.get_text().strip()

        if " " in val:
            val = shlex.quote(val)

        varval = "%s=%s" % (var, val)

        current = shlex.split(self._entry.get_text())

        if "env" not in current:
            new = ["env", varval] + current

        else:
            added = False
            new = []
            for item in current:
                if item == "env" or "=" in item or added:
                    new.append(item)
                elif not added:
                    new.append(varval)
                    new.append(item)
                    added = True
            if not added:
                new.append(varval)
        
        command = shlex.join(new)
        position = command.find(varval) + len(varval)

        self._entry.set_text(shlex.join(new))
        self._entry.set_position(position)
        popover.popdown()

        var_entry.set_text("")
        val_entry.set_text("")


    def on_env_var_entry_changed(self, widget, val_entry):
        text = widget.get_text()
        text = text.lstrip()

        if "=" in text:
            parts = text.split("=", 2)
            if len(parts[1]) > 0:
                val_entry.set_text(parts[1].rstrip())
            text = parts[0].strip()

        text = text.upper()
        widget.set_text(text)

        if len(text) == 0:
            widget.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, None)
            widget.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, None)
        elif " " in text:
            widget.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "dialog-error")
            widget.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, _("Spaces not permitted in environment variables"))
        else:
            widget.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "gtk-apply")
            widget.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, None)


    def on_env_val_entry_changed(self, widget):
        text = widget.get_text()
        text = text.strip()

        if len(text) == 0:
            widget.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, None)
            widget.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, None)
        else:
            widget.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "gtk-apply")
            widget.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, None)
