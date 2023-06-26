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

import os
import re
import shlex
from locale import gettext as _

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, Gio, GObject, GLib, Pango, Gdk


class CommandEditorDialog(Gtk.Dialog):

    def __init__(self, parent, initial_text, use_header_bar):
        super().__init__(title=_("Command Editor"), transient_for=parent,
                         use_header_bar=use_header_bar, flags=0)
        self.add_buttons(
            _('Cancel'), Gtk.ResponseType.CANCEL,
                _('Apply'), Gtk.ResponseType.OK
        )

        self.set_default_size(400, 200)
        self.set_default_response(Gtk.ResponseType.OK)

        box = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        box.set_margin_top(9)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        command_box = Gtk.Box.new(
            orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.pack_start(command_box, False, False, 0)

        entry = CommandEditorEntry(initial_text)
        command_box.pack_start(entry, False, False, 0)

        toolbox = CommandToolBox()
        toolbox.connect('env-var-activated', self.on_env_var_activated, entry)
        toolbox.connect('command-activated', self.on_command_activated, entry)
        toolbox.connect('code-activated', self.on_code_activated, entry)
        command_box.pack_start(toolbox, False, False, 0)

        grid = Gtk.Grid()
        grid.set_row_spacing(3)
        grid.set_column_spacing(6)
        box.pack_start(grid, False, False, 0)

        self.state = {
            'env': entry.get_state('env'),
            'cmd': entry.get_state('cmd'),
            'field': entry.get_state('field')
        }

        env_hint = CommandEditorHint(grid, 0)
        env_hint.set_state(self.state['env'])

        cmd_hint = CommandEditorHint(grid, 1)
        cmd_hint.set_state(self.state['cmd'])

        fields_hint = CommandEditorHint(grid, 2)
        fields_hint.set_state(self.state['field'])

        entry.connect('env-state-changed',
                      self.on_state_changed, 'env', env_hint)
        entry.connect('cmd-state-changed',
                      self.on_state_changed, 'cmd', cmd_hint)
        entry.connect('field-state-changed',
                      self.on_state_changed, 'field', fields_hint)

        help = HelpButton(
            "https://github.com/bluesabre/menulibre/wiki/Recognized-Desktop-Entry-Keys#exec",
            _("Help")
        )
        box.pack_start(help, False, False, 0)

        self.get_content_area().add(box)
        self.show_all()

        self.text = ""

        self.connect("response", self.on_response, entry)

    def on_env_var_activated(self, widget, variable, value, entry):
        entry.insert_env_var(variable, value)

    def on_command_activated(self, widget, value, entry):
        entry.insert_command(value)

    def on_code_activated(self, widget, value, entry):
        entry.insert_field_code(value)

    def on_state_changed(self, widget, success, message, key, hint):
        self.state[key] = (success, message)
        hint.set_state(self.state[key])

        for key in list(self.state.keys()):
            if not self.state[key][0]:
                self.set_response_sensitive(Gtk.ResponseType.OK, False)
                return

        self.set_response_sensitive(Gtk.ResponseType.OK, True)

    def on_response(self, dialog, response_id, entry):
        if response_id == Gtk.ResponseType.OK:
            self.text = entry.get_text().strip()

    def get_text(self):
        return self.text


class HelpButton(Gtk.LinkButton):
    def __init__(self, uri, label):
        super().__init__(uri=uri)

        self.set_label(label)

        screen = Gdk.Screen.get_default()
        provider = Gtk.CssProvider()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        provider.load_from_data("#helpbutton {padding: 0;}".encode())

        self.set_name('helpbutton')

        self.set_halign(Gtk.Align.START)


class CommandEditorEntry(Gtk.Box):
    __gsignals__ = {
        'env-state-changed': (GObject.SignalFlags.RUN_FIRST, None, (bool, str)),
        'cmd-state-changed': (GObject.SignalFlags.RUN_FIRST, None, (bool, str)),
        'field-state-changed': (GObject.SignalFlags.RUN_FIRST, None, (bool, str)),
    }

    def __init__(self, initial_text):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        context = self.get_style_context()
        context.add_class("linked")

        self.entry = Gtk.Entry()
        self.entry.set_text("delete.me")
        self.pack_start(self.entry, True, True, 0)

        revert_button = Gtk.Button.new_from_icon_name(
            "document-revert", Gtk.IconSize.BUTTON)
        revert_button.set_tooltip_text(_("Revert"))
        revert_button.connect("clicked", self.on_revert_button_clicked)
        self.pack_start(revert_button, False, False, 0)

        clear_button = Gtk.Button.new_from_icon_name(
            "edit-clear", Gtk.IconSize.BUTTON)
        clear_button.set_tooltip_text(_("Clear"))
        clear_button.connect("clicked", self.on_clear_button_clicked)
        self.pack_start(clear_button, False, False, 0)

        self.entry.connect("changed", self.on_entry_changed,
                           revert_button, clear_button)

        self.state = {
            'env': (True, ""),
            'cmd': (True, ""),
            'field': (True, ""),
        }

        self.text = initial_text
        self.entry.set_text(initial_text)

        self.show_all()

    def get_text(self):
        return self.entry.get_text()

    def set_text(self, text):
        self.entry.set_text(text)

    def get_state(self, key):
        return self.state[key]

    def insert_text(self, text):
        pos = self.entry.get_position()
        self.entry.insert_text(text, pos)
        self.entry.set_position(pos + len(text))

    def store_text(self, text):
        self.text = text

    def revert(self):
        self.set_text(self.text)

    def clear(self):
        self.set_text("")

    def on_revert_button_clicked(self, button):
        self.revert()
        self.entry.grab_focus()
        self.entry.set_position(len(self.text))

    def on_clear_button_clicked(self, button):
        self.clear()
        self.entry.grab_focus()

    def insert_env_var(self, var, val):
        if " " in val:
            val = shlex.quote(val)

        varval = "%s=%s" % (var, val)

        current = shlex.split(self.entry.get_text())

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

        self.entry.set_text(shlex.join(new))
        self.entry.set_position(position)

    def insert_component(self, value):
        if len(value) == 0:
            return

        text = self.entry.get_text()
        pos = self.entry.get_position()

        is_equals = pos > 0 and text[pos-1] == "="
        need_space_before = pos > 0 and text[pos-1] != "="
        need_space_after = len(text) > pos

        if is_equals and " " in value:
            value = shlex.quote(value)

        if need_space_before:
            value = " " + value

        if need_space_after:
            value = value + " "

        self.insert_text(value)

    def insert_command(self, value):
        self.insert_component(value)

    def insert_field_code(self, value):
        self.insert_component(value)

    def validate_field_codes(self, text):
        deprecated = ["%d", "%D", "%n", "%N", "%v", "%m"]
        singleton = ["%f", "%u", "%F", "%U"]
        desktop = ["%i", "%c", "%k"]
        keys = deprecated + singleton + desktop

        found = {}
        quoted = {}

        for key in keys:
            found[key] = 0
            quoted[key] = 0

            q = re.compile(key)
            found[key] = len(re.findall(q, text))

            q = re.compile('\"%s\"' % key)
            quoted[key] = len(re.findall(q, text))

            q = re.compile('\'%s\'' % key)
            quoted[key] += len(re.findall(q, text))

        single = 0
        for key in singleton:
            single += found[key]

        if single > 1:
            return _("A single command line may only contain one of %f, %u, %F, or %U")

        for key in keys:
            if quoted[key] > 0:
                return _("Field code '%s' can not be used inside a quoted argument") % key

        for key in deprecated:
            if found[key] > 0:
                return _("Field code '%s' has been deprecated") % key

        return None

    def is_env_var(self, text):
        if "=" not in text:
            return False
        k = text.split("=")[0]
        return k == k.upper()

    def validate_cmd(self, text):
        results = {
            "env": [],
            "cmd": None,
            "args": [],
            "errors": {
                "env": None,
                "cmd": _("No command found"),
                "fields": None
            }
        }

        try:
            parts = shlex.split(text)
        except ValueError:
            return self._last_results

        if len(parts) == 0:
            return results

        env_found = parts[0] == "env"
        non_env_found = False

        for part in parts:
            if part == "env":
                continue

            if self.is_env_var(part):
                if not env_found:
                    results["errors"]["env"] = \
                        _("Environment variables should be preceded by env")
                elif non_env_found:
                    results["errors"]["env"] = \
                        _("Environment variables should precede the command")
                else:
                    results["env"].append(part)
                    continue
            else:
                non_env_found = True

            if results["cmd"] is None:
                results["cmd"] = part
            else:
                results["args"].append(part)

        if results["cmd"] is None:
            results["errors"]["cmd"] = _("No command found")
        elif results["cmd"].startswith("/") and not os.path.isfile(results["cmd"]):
            results["errors"]["cmd"] = \
                _("File '%s' not found") % results["cmd"]
        elif GLib.find_program_in_path(results["cmd"]) is None:
            results["errors"]["cmd"] = \
                _("Command '%s' not found") % results["cmd"]
        else:
            results["errors"]["cmd"] = None

        results["errors"]["fields"] = self.validate_field_codes(text)

        self._last_results = results

        return results

    def on_entry_changed(self, widget, revert_button, clear_button):
        text = widget.get_text()

        revert_button.set_sensitive(text != self.text)
        clear_button.set_sensitive(len(text) > 0)

        context = self.validate_cmd(text)

        if context["errors"]["env"] is not None:
            env = (False, context["errors"]["env"])
        else:
            env = (True, _('No environment variable errors'))

        if context["errors"]["cmd"] is not None:
            cmd = (False, context["errors"]["cmd"])
        else:
            cmd = (True, _('No command errors'))

        if context["errors"]["fields"] is not None:
            field = (False, context["errors"]["fields"])
        else:
            field = (True, _('No invalid field codes'))

        if env != self.state['env']:
            self.state['env'] = env
            self.emit('env-state-changed', env[0], env[1])

        if cmd != self.state['cmd']:
            self.state['cmd'] = cmd
            self.emit('cmd-state-changed', cmd[0], cmd[1])

        if field != self.state['field']:
            self.state['field'] = field
            self.emit('field-state-changed', field[0], field[1])


class CommandToolBox(Gtk.Box):
    __gsignals__ = {
        'env-var-activated': (GObject.SignalFlags.RUN_FIRST, None, (str, str)),
        'command-activated': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'code-activated': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        label = Gtk.Label.new("")
        label.set_markup("<b>%s</b>" % _("Add"))
        self.pack_start(label, False, False, 0)

        box = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        context = box.get_style_context()
        context.add_class("linked")

        popover = CommandEditorEnvEditor()
        popover.connect("activated", self.on_env_var_activated)
        box.pack_start(popover, False, False, 0)

        popover = CommandEditorCommandEntry()
        popover.connect("activated", self.on_command_activated)
        box.pack_start(popover, False, False, 0)

        size_group = Gtk.SizeGroup.new(Gtk.SizeGroupMode.BOTH)

        popover = FieldCodeMenu(_("File"))
        popover.add_option("%f", _("A single file or directory."), size_group)
        popover.add_option(
            "%F", _("A list of files or directories."), size_group)
        popover.connect("row-activated", self.on_field_code_activated)
        box.pack_start(popover, False, False, 0)

        popover = FieldCodeMenu(_("URL"))
        popover.add_option("%u", _("A single URL."), size_group)
        popover.add_option("%U", _("A list of URLs."), size_group)
        popover.connect("row-activated", self.on_field_code_activated)
        box.pack_start(popover, False, False, 0)

        popover = FieldCodeMenu(_("Extra"))
        popover.add_option(
            "%i", _("The <tt>Icon</tt> key of this launcher."), size_group)
        popover.add_option(
            "%c", _("The translated <tt>Name</tt> key of this launcher."), size_group)
        popover.add_option(
            "%k", _("The file path of this launcher."), size_group)
        popover.connect("row-activated", self.on_field_code_activated)
        box.pack_start(popover, False, False, 0)

        self.add(box)

        self.show_all()

    def on_env_var_activated(self, widget, variable, value):
        self.emit('env-var-activated', variable, value)

    def on_command_activated(self, widget, value):
        self.emit('command-activated', value)

    def on_field_code_activated(self, widget, value):
        self.emit('code-activated', value)


class CommandEditorEnvEditor(Gtk.MenuButton):
    __gsignals__ = {
        'activated': (GObject.SignalFlags.RUN_FIRST, None, (str, str,)),
    }

    def __init__(self):
        super().__init__()

        self.set_label(_("Environment variable"))
        self.set_mode(True)

        popover = Gtk.Popover(relative_to=self)
        popover.set_constrain_to(Gtk.PopoverConstraint.NONE)

        grid = Gtk.Grid()
        grid.set_row_spacing(6)
        grid.set_column_spacing(6)
        grid.set_border_width(6)

        label = Gtk.Label.new("")
        label.set_markup("<b>%s</b>" % _("Variable"))
        label.set_xalign(0.00)
        var_entry = Gtk.Entry()

        grid.attach(label, 0, 0, 1, 1)
        grid.attach(var_entry, 1, 0, 1, 1)
        var_entry.grab_focus()

        label = Gtk.Label.new("")
        label.set_markup("<b>%s</b>" % _("Value"))
        label.set_xalign(0.00)
        val_entry = Gtk.Entry()

        var_entry.connect("changed", self.on_var_entry_changed, val_entry)
        val_entry.connect("changed", self.on_val_entry_changed)

        var_entry.connect('activate', self.on_activate,
                          var_entry, val_entry, popover)
        val_entry.connect('activate', self.on_activate,
                          var_entry, val_entry, popover)

        popover.connect('closed', self.on_closed, var_entry, val_entry)

        grid.attach(label, 0, 1, 1, 1)
        grid.attach(val_entry, 1, 1, 1, 1)

        grid.show_all()

        popover.add(grid)

        self.set_popover(popover)
        self.show_all()

    def on_var_entry_changed(self, var_entry, val_entry):
        text = var_entry.get_text()
        text = text.lstrip()

        if "=" in text:
            parts = text.split("=", 2)
            if len(parts[1]) > 0:
                val_entry.set_text(parts[1].rstrip())
            text = parts[0].strip()

        text = text.upper()
        var_entry.set_text(text)

        if len(text) == 0:
            var_entry.set_icon_from_icon_name(
                Gtk.EntryIconPosition.SECONDARY, None)
            var_entry.set_icon_tooltip_text(
                Gtk.EntryIconPosition.SECONDARY, None)
        elif " " in text:
            var_entry.set_icon_from_icon_name(
                Gtk.EntryIconPosition.SECONDARY, "dialog-error")
            var_entry.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY,
                _("Spaces not permitted in environment variables"))
        else:
            var_entry.set_icon_from_icon_name(
                Gtk.EntryIconPosition.SECONDARY, "gtk-apply")
            var_entry.set_icon_tooltip_text(
                Gtk.EntryIconPosition.SECONDARY, None)

    def on_val_entry_changed(self, val_entry):
        text = val_entry.get_text()
        text = text.strip()

        if len(text) == 0:
            val_entry.set_icon_from_icon_name(
                Gtk.EntryIconPosition.SECONDARY, None)
            val_entry.set_icon_tooltip_text(
                Gtk.EntryIconPosition.SECONDARY, None)
        else:
            val_entry.set_icon_from_icon_name(
                Gtk.EntryIconPosition.SECONDARY, "gtk-apply")
            val_entry.set_icon_tooltip_text(
                Gtk.EntryIconPosition.SECONDARY, None)

    def on_activate(self, widget, var_entry, val_entry, popover):
        if var_entry.get_icon_name(Gtk.EntryIconPosition.SECONDARY) != "gtk-apply":
            return
        if val_entry.get_icon_name(Gtk.EntryIconPosition.SECONDARY) != "gtk-apply":
            return

        var = var_entry.get_text().strip()
        val = val_entry.get_text().strip()

        self.emit("activated", var, val)

        popover.popdown()

    def on_closed(self, popover, var_entry, val_entry):
        var_entry.set_text("")
        val_entry.set_text("")


class CommandEditorCommandEntry(Gtk.MenuButton):
    __gsignals__ = {
        'activated': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self):
        super().__init__()

        self.set_label(_("Command"))
        self.set_mode(True)

        popover = Gtk.Popover(relative_to=self)

        grid = Gtk.Grid()
        grid.set_row_spacing(6)
        grid.set_column_spacing(6)
        grid.set_border_width(6)

        label = Gtk.Label.new("")
        label.set_xalign(0.00)
        label.set_markup("<b>%s</b>" % _("Command"))
        entry = Gtk.Entry()
        entry.connect('activate', self.on_command_entry_activate, popover)

        grid.attach(label, 0, 0, 1, 1)
        grid.attach(entry, 1, 0, 1, 1)

        bbox = Gtk.ButtonBox.new(Gtk.Orientation.HORIZONTAL)
        bbox.set_layout(Gtk.ButtonBoxStyle.START)
        bbox.set_spacing(6)
        bbox.set_homogeneous(True)
        grid.attach(bbox, 0, 1, 2, 1)

        file_chooser = Gtk.FileChooserButton.new(
            _("Select an executable"), Gtk.FileChooserAction.OPEN)
        file_chooser.connect('file-set', self.on_file_chooser_set, entry)
        filter = Gtk.FileFilter.new()
        filter.add_custom(Gtk.FileFilterFlags.FILENAME, self.exec_filter)
        file_chooser.set_filter(filter)
        bbox.pack_start(file_chooser, False, False, 0)

        app_chooser = AppChooserMenu()
        app_chooser.connect('selected', self.on_app_chooser_selected, entry)
        bbox.pack_start(app_chooser, False, False, 0)

        grid.show_all()

        popover.add(grid)

        popover.connect('closed', self.on_closed, entry)

        self.set_popover(popover)
        self.show_all()

    def exec_filter(self, filter_info):
        path = filter_info.filename
        return os.access(path, os.X_OK)

    def on_command_entry_activate(self, widget, popover):
        value = widget.get_text().strip()
        self.emit('activated', value)
        popover.popdown()

    def on_file_chooser_set(self, widget, entry):
        filename = widget.get_filename()
        entry.set_text(filename)
        entry.grab_focus()
        entry.set_position(len(filename))
        widget.set_filename("")

    def on_app_chooser_selected(self, widget, value, entry):
        entry.set_text(value)
        entry.grab_focus()
        entry.set_position(len(value))

    def on_closed(self, widget, entry):
        entry.set_text("")


class AppChooserMenu(Gtk.ComboBox):
    __gsignals__ = {
        'selected': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self):
        super().__init__()

        store = Gtk.ListStore.new([str, str, Gio.Icon])
        store.append([_("Select an application"), None, None])

        app_list = []
        infos = Gio.AppInfo.get_all()
        for info in infos:
            executable = info.get_commandline()
            icon = info.get_icon()
            name = info.get_name()
            app_list.append([name, executable, icon])

        app_list = sorted(app_list, key=lambda x: x[0].lower())

        for app in app_list:
            store.append(app)

        self.set_model(store)

        renderer_pixbuf = Gtk.CellRendererPixbuf()
        self.pack_start(renderer_pixbuf, True)
        self.add_attribute(renderer_pixbuf, "gicon", 2)

        renderer_text = Gtk.CellRendererText()
        renderer_text.set_property('width-chars', 20)
        renderer_text.set_property('ellipsize', Pango.EllipsizeMode.END)
        self.pack_start(renderer_text, True)
        self.add_attribute(renderer_text, "text", 0)

        self.set_active(0)

        self.connect('changed', self.on_changed)

    def on_changed(self, widget):
        executable = self.get_executable()
        if executable is not None:
            self.emit('selected', executable)
        self.set_active(0)

    def get_executable(self):
        treemodel = self.get_model()
        treeiter = self.get_active_iter()
        if treeiter is None:
            return None
        row = treemodel[treeiter][:]
        return row[1]


class FieldCodeMenu(Gtk.MenuButton):
    __gsignals__ = {
        'row-activated': (GObject.SignalFlags.RUN_FIRST, None,
                          (str,))
    }

    def __init__(self, label):
        super().__init__()

        self.set_label(label)
        self.set_mode(True)

        popover = Gtk.Popover(relative_to=self)

        self.listbox = Gtk.ListBox.new()
        popover.add(self.listbox)

        self.set_popover(popover)

        self.show_all()

        self.listbox.connect("row-activated", self.on_row_activated, popover)

    def add_option(self, value, text, size_group):
        option = FieldCodeOption(value, text, size_group)
        self.listbox.add(option)
        self.listbox.show_all()

    def on_row_activated(self, listbox, row, popover):
        self.emit("row-activated", row.get_value())
        popover.popdown()


class FieldCodeOption(Gtk.ListBoxRow):
    def __init__(self, value, text, size_group):
        super().__init__()

        box = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box.set_border_width(3)

        label = Gtk.Label.new("")
        label.set_markup("<i>%s</i>" % value)
        box.pack_start(label, False, False, 0)

        size_group.add_widget(label)

        label = Gtk.Label.new(text)
        label.set_markup(text)
        box.pack_start(label, False, False, 0)

        self.add(box)

        self.show_all()

        self.value = value

    def get_value(self):
        return self.value


class CommandEditorHint():
    def __init__(self, grid, row):
        self.image = Gtk.Image.new_from_icon_name(
            "gtk-apply", Gtk.IconSize.BUTTON)
        self.label = Gtk.Label.new("")
        self.label.set_xalign(0.00)
        self.label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        grid.attach(self.image, 0, row, 1, 1)
        grid.attach(self.label, 1, row, 1, 1)

    def set_success(self, message):
        self.image.set_from_icon_name('gtk-apply', Gtk.IconSize.BUTTON)
        self.label.set_text(message)

    def set_error(self, message):
        self.image.set_from_icon_name('gtk-cancel', Gtk.IconSize.BUTTON)
        self.label.set_text(message)

    def set_state(self, state):
        if state[0]:
            self.set_success(state[1])
        else:
            self.set_error(state[1])


class CommandEntry(Gtk.Entry):
    __gsignals__ = {
        'value-changed': (GObject.SignalFlags.RUN_FIRST, None, (str, str,)),
    }

    def __init__(self):
        Gtk.Entry.__init__(self)

        self.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, 'document-edit-symbolic')

        self.connect("icon-release", self.on_icon_release)

        self.connect('changed', self._on_changed)

    def on_icon_release(self, entry, icon_pos, event):
        if icon_pos != Gtk.EntryIconPosition.SECONDARY:
            return

        dialog = CommandEditorDialog(self.get_toplevel(), self.get_text(), True)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            self.set_text(dialog.get_text())

        dialog.destroy()

    def unescape_value(self, value):
        value = str(value)
        args = []
        for arg in shlex.split(value, posix=False):
            if arg.startswith("\""):
                arg = arg.replace("%%", "%")
            args.append(arg)
        return " ".join(args)

    def escape_value(self, value):
        value = str(value)
        args = []
        for arg in shlex.split(value, posix=False):
            if arg.startswith("\""):
                arg = arg.replace("%%", "%")  # Make it consistent for the pros
                arg = arg.replace("%", "%%")
            args.append(arg)
        return " ".join(args)

    def set_value(self, value):
        if value is None:
            value = ""
        self.set_text(self.unescape_value(value))

    def get_value(self):
        return self.escape_value(self.get_text())

    def _on_changed(self, widget):
        self.emit('value-changed', 'Exec', self.get_value())


class CommandEditorDemoWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Command Editor Dialog Example")

        self.set_border_width(6)

        entry = CommandEntry()

        self.add(entry)


if __name__ == "__main__":
    win = CommandEditorDemoWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
