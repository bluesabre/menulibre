#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2015 Sean Davis <smd.seandavis@gmail.com>
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

from gi.repository import Gtk
from locale import gettext as _

import menulibre_lib

class IconSelector:
    """The MenuLibre IconSelector."""

    def __init__(self, parent):
        """Initialize all values."""
        self._parent = parent
        self._filename = None
        self._icon_name = None
        self._icons_list = None
        self._icon_sel_dialog = None
        self._icon_sel_treeview = None

    def select_by_icon_name(self):
        """Open a selection dialog to choose an icon."""
        icon_name = None
        dialog, treeview = self._get_icon_selection_dialog()
        if dialog.run() == Gtk.ResponseType.APPLY:
            model, treeiter = treeview.get_selection().get_selected()
            icon_name = model[treeiter][0]
            self.set_icon_name(icon_name)
        dialog.hide()
        return icon_name

    def select_by_filename(self):
        """Open a selection dialog to choose an image."""
        filename = None
        dialog = self._get_file_selection_dialog()
        if dialog.run() == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            self.set_filename(filename)
        dialog.destroy()
        return filename

    def set_icon_name(self, icon_name):
        """Set the current icon name for the icon selection."""
        self._icon_name = icon_name
        self._filename = None

    def set_filename(self, filename):
        """Set the current filename for the image selection."""
        self._filename = filename
        self._icon_name = None

    def get_icon_name(self):
        """Return the current or last chosen icon name, and True if it is an
        icon instead of a filename."""
        if self._filename is not None:
            return self._filename, False
        else:
            return self._icon_name, True

    def _get_file_selection_dialog(self):
        """Get the image selection dialog."""
        dialog = Gtk.FileChooserDialog(title=_("Select an image"),
                                       transient_for=self._parent,
                                       action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(_("Cancel"), Gtk.ResponseType.CANCEL,
                           _("OK"), Gtk.ResponseType.OK)
        if self._filename is not None:
            dialog.set_filename(self._filename)
        file_filter = Gtk.FileFilter()
        file_filter.set_name(_("Images"))
        file_filter.add_mime_type("image/*")
        dialog.add_filter(file_filter)
        return dialog

    def _get_icon_selection_dialog(self):
        """Get the icon selection dialog."""
        builder = menulibre_lib.get_builder('MenulibreWindow')

        # Clear the entry.
        entry = builder.get_object('icon_selection_search')
        entry.set_text("")

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
