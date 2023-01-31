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
from collections import OrderedDict

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
        dialog.destroy()
        self._dialog = None
        return response

    def _get_dialog(self):
        """Get the icon selection dialog."""
        if self._dialog is not None:
            return self._dialog

        builder = menulibre_lib.get_builder('ExecEditor')

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

        self._dialog.connect('show', self.on_dialog_show)

        var_entry = builder.get_object('env_var_entry')
        val_entry = builder.get_object('env_val_entry')
        popover = builder.get_object('popover_env')

        popover.connect('show', self.on_env_popover_show, var_entry, val_entry)

        var_entry.connect('changed', self.on_env_var_entry_changed, val_entry)
        val_entry.connect('changed', self.on_env_val_entry_changed)

        var_entry.connect('activate', self.on_env_var_activate, var_entry, val_entry, popover)
        val_entry.connect('activate', self.on_env_var_activate, var_entry, val_entry, popover)

        popover = builder.get_object('popover_command')

        entry = builder.get_object('command_entry')
        entry.connect('activate', self.on_command_entry_activate, popover)

        file_chooser = builder.get_object('command_file_chooser')
        file_chooser.connect('file-set', self.on_file_chooser_set, entry)

        select = builder.get_object('command_app_chooser')
        select.connect('changed', self.on_app_chooser_changed, entry)

        popover = builder.get_object('popover_file')
        listbox = builder.get_object('file_list')
        listbox.connect('row-activated', self.on_field_listbox_row_activated, popover)

        popover = builder.get_object('popover_url')
        listbox = builder.get_object('url_list')
        listbox.connect('row-activated', self.on_field_listbox_row_activated, popover)

        popover = builder.get_object('popover_extra')
        listbox = builder.get_object('extra_list')
        listbox.connect('row-activated', self.on_field_listbox_row_activated, popover)

        return self._dialog

    
    def on_field_listbox_row_activated(self, listbox, listrow, popover):
        field_value = listrow.get_children()[0].get_children()[0].get_text()
        self.insert_at_command(field_value)
        popover.popdown()


    def on_app_chooser_changed(self, widget, entry):
        treeiter = widget.get_active_iter()
        if treeiter is None:
            return
        treemodel = widget.get_model()
        row = treemodel[treeiter][:]
        binary = row[1]
        entry.set_text(binary)
        entry.grab_focus()
        entry.set_position(len(binary))
        widget.set_active_iter(None)


    def on_dialog_show(self, widget):
        text = self._entry.get_text()
        self._entry.set_position(len(text))
        self._entry.grab_focus()
        self._entry.select_region(-1,-1)


    def on_env_popover_show(self, widget, var_entry, val_entry):
        var_entry.set_text('')
        val_entry.set_text('')
        var_entry.grab_focus()


    def insert_at_command(self, value):
        current = self._entry.get_text()
        pos = self._entry.get_position()
        before = current[0:pos]
        after = current[pos:]

        value = value.strip()

        if len(before) > 0 and before[-1] != "=":
            value = " " + value

        if len(after) > 0 and after[0] != " ":
            value += " "

        self._entry.set_text(before + value + after)
        self._entry.set_position(pos + len(value))


    def on_command_entry_activate(self, widget, popover):
        value = widget.get_text().strip()
        self.insert_at_command(value)
        popover.popdown()


    def on_file_chooser_set(self, widget, entry):
        filename = widget.get_filename()
        entry.set_text(filename)
        entry.grab_focus()
        entry.set_position(len(filename))
        widget.set_filename("")



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
