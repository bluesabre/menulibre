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

from gi.repository import Gtk
from locale import gettext as _

from . import IconSelectionDialog
import menulibre_lib


class IconSelector:
    """The MenuLibre IconSelector."""

    def __init__(self, parent, use_header_bar):
        """Initialize all values."""
        self._parent = parent
        self._filename = None
        self._icon_name = None
        self._icons_list = None
        self._icon_sel_dialog = None
        self._icon_sel_treeview = None
        self._use_header_bar = use_header_bar

    def select_by_icon_name(self, current_icon_name):
        """Open a selection dialog to choose an icon."""
        icon_name = None
        dialog = IconSelectionDialog.IconSelectionDialog(parent=self._parent, initial_icon=current_icon_name, use_header_bar=self._use_header_bar)
        if dialog.run() == Gtk.ResponseType.OK:
            icon_name = dialog.get_icon()
            self.set_icon_name(icon_name)
        dialog.destroy()
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
        # Translators: File Chooser Dialog, window title.
        dialog = Gtk.FileChooserDialog(title=_("Select an image…"),
                                       transient_for=self._parent,
                                       action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(_("Cancel"), Gtk.ResponseType.CANCEL,
                           _("OK"), Gtk.ResponseType.OK)
        if self._filename is not None:
            dialog.set_filename(self._filename)
        file_filter = Gtk.FileFilter()
        # Translators: "Images" file chooser dialog filter
        file_filter.set_name(_("Images"))
        file_filter.add_mime_type("image/*")
        dialog.add_filter(file_filter)
        return dialog
