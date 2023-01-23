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
from operator import itemgetter

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
        icon_name = None
        dialog = self._get_dialog()
        if dialog.run() == Gtk.ResponseType.APPLY:
            print("Apply")
        dialog.hide()

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
        
        app_list = sorted(app_list, key=itemgetter(0))

        for app in app_list:
            applications_store.append(app)
        
        return self._dialog

        # Load the dialog
        if self._icon_sel_dialog is None:

            self._icon_sel_dialog = \
                builder.get_object('icon_selection_dialog')
            self._icon_sel_dialog.set_transient_for(self._parent)

        # Load the icons list
        if self._icons_list is None:
            icon_theme = Gtk.IconTheme.get_default()
            self.icons_list = icon_theme.list_icons(None)
            self.icons_list.sort()

        # Load the Icon Selection Treeview.
        if self._icon_sel_treeview is None:
            self._icon_sel_treeview = \
                builder.get_object('icon_selection_treeview')

            button = builder.get_object('icon_selection_apply')

            # Create the searchable model.
            model = self._icon_sel_treeview.get_model()
            model_filter = model.filter_new()
            model_filter.set_visible_func(self._icon_sel_match_func, entry)
            self._icon_sel_treeview.set_model(model_filter)

            # Attach signals.
            entry.connect("changed", self._on_search_changed, model_filter)
            entry.connect('icon-press', self._on_search_cleared)
            self._icon_sel_treeview.connect("row-activated",
                                            self._on_row_activated,
                                            button)
            self._icon_sel_treeview.connect("cursor-changed",
                                            self._on_cursor_changed,
                                            None, button)

            model = self._get_icon_sel_tree_model()
            for icon_name in self.icons_list:
                model.append([icon_name])

        self._icon_sel_select_icon_name(self._icon_name)

        return self._icon_sel_dialog, self._icon_sel_treeview

    def _icon_sel_select_icon_name(self, icon_name=None):
        if icon_name is not None:
            model = self._get_icon_sel_tree_model()
            for i in range(len(model)):
                if model[i][0] == icon_name:
                    self._icon_sel_treeview.set_cursor(i, None, False)
                    return

        self._icon_sel_treeview.set_cursor(0, None, False)

    def _get_icon_sel_tree_model(self):
        return self._icon_sel_treeview.get_model().get_model()

    def _icon_sel_match_func(self, model, treeiter, entry):
        """Match function for filtering IconSelection search results."""
        # Make the query case-insensitive.
        query = str(entry.get_text().lower())

        if query == "":
            return True

        return query in model[treeiter][0].lower()

    def _on_row_activated(self, widget, path, column, button):
        """Allow row activation to select the icon and close the dialog."""
        button.activate()

    def _on_cursor_changed(self, widget, selection, button):
        """When the cursor selects a row, make the Apply button sensitive."""
        button.set_sensitive(True)

    def _on_search_changed(self, widget, treefilter, expand=False):
        """Generic search entry changed callback function."""
        query = widget.get_text()

        if len(query) == 0:
            widget.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY,
                                           None)

        else:
            widget.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY,
                                           'edit-clear-symbolic')
            if expand:
                self.treeview.expand_all()

        treefilter.refilter()

    def _on_search_cleared(self, widget, event, user_data=None):
        """Generic search cleared callback function."""
        widget.set_text("")
