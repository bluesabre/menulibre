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

from gi.repository import Gtk, GObject

from .MenulibreStackSwitcher import StackSwitcherBox

from .CommandEditor import CommandEntry
from .IconEntry import IconEntry
from .FilenameLabel import FilenameLabel
from .PathEntry import PathEntry
from .SwitchEntry import SwitchEntry
from .TextEntryButton import TextEntryButton
from .CategoryEditor import CategoryEditor
from .ActionEditor import ActionEditor
from .AdvancedPage import AdvancedPage
from .Section import Section

from .util import getDefaultMenuPrefix


class ApplicationEditor(Gtk.Box):
    __gsignals__ = {
        'value-changed': (GObject.SignalFlags.RUN_FIRST, None, (str, str,)),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._directory_hide_widgets = []
        self._internal_values = {
            'Type': '',
            'Version': ''
        }

        self.set_border_width(6)
        self.set_size_request(400, -1)

        scrolled = Gtk.ScrolledWindow.new(hadjustment=None, vadjustment=None)
        scrolled.set_shadow_type(Gtk.ShadowType.NONE)
        self.pack_start(scrolled, True, True, 0)

        vbox = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        scrolled.add(vbox)

        # Icon, Name, and Comment Entry
        hbox = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vbox.add(hbox)

        self._icon_entry = IconEntry()
        self._icon_entry.connect("value-changed", self._on_changed)
        hbox.pack_start(self._icon_entry, False, False, 0)

        namebox = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        hbox.pack_start(namebox, True, True, 0)

        self._name_entry = TextEntryButton('Name', bold_font=True, required=True, placeholder_text=_('Add name'))
        self._name_entry.connect("value-changed", self._on_changed)
        namebox.pack_start(self._name_entry, True, True, 0)

        self._comment_entry = TextEntryButton('Comment', placeholder_text=_('Add comment'))
        self._comment_entry.connect("value-changed", self._on_changed)
        namebox.pack_start(self._comment_entry, True, True, 0)

        # Application Details Frame
        self._app_details = Section(_("Application Details"))
        vbox.add(self._app_details)

        self._directory_hide_widgets.append(self._app_details)

        grid = Gtk.Grid.new()
        grid.set_row_spacing(3)
        grid.set_column_spacing(12)
        self._app_details.add(grid)

        label = Gtk.Label.new(_("Command"))
        label.set_xalign(0.0)
        label.set_tooltip_text(_("Program to execute with arguments. This key is required if DBusActivatable is not set to \"True\" or if you need compatibility with implementations that do not understand D-Bus activation.\n"
                                 "See https://github.com/bluesabre/menulibre/wiki/Recognized-Desktop-Entry-Keys#exec for a list of supported arguments."))
        grid.attach(label, 0, 0, 1, 1)

        self._exec_entry = CommandEntry()
        self._exec_entry.connect("value-changed", self._on_changed)
        self._exec_entry.set_hexpand(True)
        grid.attach(self._exec_entry, 1, 0, 1, 1)

        label = Gtk.Label.new(_("Working Directory"))
        label.set_xalign(0.0)
        label.set_tooltip_text(_("The working directory."))
        grid.attach(label, 0, 1, 1, 1)

        self._path_entry = PathEntry()
        self._path_entry.connect("value-changed", self._on_changed)
        self._path_entry.set_hexpand(True)
        grid.attach(self._path_entry, 1, 1, 1, 1)

        # Options Frame
        self._options = Section(_("Options"))
        vbox.add(self._options)

        grid = Gtk.Grid.new()
        grid.set_row_spacing(3)
        grid.set_column_spacing(12)
        self._options.add(grid)

        label = Gtk.Label.new(_("Run in terminal"))
        label.set_xalign(0.0)
        label.set_hexpand(True)
        label.set_tooltip_text(_("If set to \"True\", the program will be ran in a terminal window."))
        grid.attach(label, 0, 0, 1, 1)

        self._terminal_entry = SwitchEntry('Terminal')
        self._terminal_entry.connect("value-changed", self._on_changed)
        grid.attach(self._terminal_entry, 1, 0, 1, 1)

        self._directory_hide_widgets.append(label)
        self._directory_hide_widgets.append(self._terminal_entry)

        label = Gtk.Label.new(_("Use startup notification"))
        label.set_xalign(0.0)
        label.set_hexpand(True)
        label.set_tooltip_text(_("If set to \"True\", a startup notification is sent. Usually means that a busy cursor is shown while the application launches."))
        grid.attach(label, 0, 1, 1, 1)

        self._startup_notify_entry = SwitchEntry('StartupNotify')
        self._startup_notify_entry.connect("value-changed", self._on_changed)
        grid.attach(self._startup_notify_entry, 1, 1, 1, 1)

        self._directory_hide_widgets.append(label)
        self._directory_hide_widgets.append(self._startup_notify_entry)

        label = Gtk.Label.new(_("Hide from menus"))
        label.set_xalign(0.0)
        label.set_hexpand(True)
        label.set_tooltip_text(_("If set to \"True\", this entry will not be shown in menus, but will be available for MIME type associations etc."))
        grid.attach(label, 0, 2, 1, 1)

        self._no_display_entry = SwitchEntry('NoDisplay')
        self._no_display_entry.connect("value-changed", self._on_changed)
        grid.attach(self._no_display_entry, 1, 2, 1, 1)

        # Settings Switcher
        self._additional_settings = StackSwitcherBox()
        vbox.pack_start(self._additional_settings, True, True, 0)

        self._directory_hide_widgets.append(self._additional_settings)

        # Categories Treeview and Inline Toolbar
        self._category_editor = CategoryEditor()
        self._category_editor.set_prefix(getDefaultMenuPrefix())
        self._category_editor.connect("value-changed", self._on_changed)
        self._additional_settings.add_child(self._category_editor,
                                            # Translators: "Categories" launcher section
                                            'categories', _('Categories'))

        # Actions Treeview and Inline Toolbar
        self._action_editor = ActionEditor()
        self._action_editor.connect("value-changed", self._on_changed)
        self._additional_settings.add_child(self._action_editor,
                                            # Translators: "Actions" launcher section
                                            'actions', _('Actions'))
    
        # Advanced Settings
        self._advanced_page = AdvancedPage()
        self._advanced_page.connect("value-changed", self._on_changed)
        self._additional_settings.add_child(self._advanced_page,
                                            # Translators: "Advanced" launcher section
                                            'advanced', _('Advanced'))

        # Filename
        self._filename_label = FilenameLabel()
        self._filename_label.connect("value-changed", self._on_changed)
        vbox.pack_end(self._filename_label, False, False, 0)

    def set_value(self, key, value):
        """Set the DesktopSpec key, value pair in the editor."""
        if self._advanced_page.has_value(key):
            self._advanced_page.set_value(key, value)
        elif key == 'Filename':
            self._filename_label.set_value(value)
        elif key == 'Icon':
            self._icon_entry.set_value(value)
        elif key == 'Name':
            self._name_entry.set_value(value)
        elif key == 'Comment':
            self._comment_entry.set_value(value)
        elif key == 'Categories':
            self._category_editor.set_value(value)
        elif key == 'Actions':
            self._action_editor.set_value(value)
        elif key == 'Exec':
            self._exec_entry.set_value(value)
        elif key == 'Path':
            self._path_entry.set_value(value)
        elif key == 'Terminal':
            self._terminal_entry.set_value(value)
        elif key == 'StartupNotify':
            self._startup_notify_entry.set_value(value)
        elif key == 'NoDisplay':
            self._no_display_entry.set_value(value)
        elif key in self._internal_values.keys():
            self._internal_values[key] = value
        else:
            print("SET", key, value)

        if key == 'Type':
            for widget in self._directory_hide_widgets:
                if value == 'Directory':
                    widget.hide()
                else:
                    widget.show()

    def get_value(self, key):
        """Return the value stored for the specified key."""
        if self._advanced_page.has_value(key):
            return self._advanced_page.get_value(key)
        elif key == 'Name':
            return self._name_entry.get_value()
        elif key == 'Comment':
            return self._comment_entry.get_value()
        elif key == 'Icon':
            return self._icon_entry.get_value()
        elif key == 'Categories':
            return self._category_editor.get_value()
        elif key == 'Actions':
            return self._action_editor.get_value()
        elif key == 'Filename':
            return self._filename_label.get_value()
        elif key == 'Exec':
            return self._exec_entry.get_value()
        elif key == 'Path':
            return self._path_entry.get_value()
        elif key == 'Terminal':
            return self._terminal_entry.get_value()
        elif key == 'StartupNotify':
            return self._startup_notify_entry.get_value()
        elif key == 'NoDisplay':
            return self._no_display_entry.get_value()
        elif key in self._internal_values.keys():
            return self._internal_values[key]
        else:
            print("GET", key)
        return None
    
    def remove_incomplete_actions(self):
        self._action_editor.remove_incomplete_actions()

    def get_actions(self):
        return self._action_editor.get_actions()

    def clear_categories(self):
        self._category_editor.set_value("")

    def insert_required_categories(self, parent_directory):
        self._category_editor.insert_required_categories(parent_directory)

    def cancel(self):
        self._name_entry.cancel()
        self._comment_entry.cancel()

    def commit(self):
        self._name_entry.commit()
        self._comment_entry.commit()

    def take_focus(self):
        self._icon_entry.grab_focus()

    def _on_changed(self, widget, key, value):
        self.emit('value-changed', key, value)