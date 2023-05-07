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

from gi.repository import Gtk, Gdk, Pango


class IconFileSelectionDialog(Gtk.FileChooserDialog):

    def __init__(self, parent, initial_file="", use_header_bar=False):
        super().__init__(title=_("Select an image"), transient_for=parent,
                         action=Gtk.FileChooserAction.OPEN,
                         use_header_bar=use_header_bar)
        self.add_buttons(
            _('Cancel'), Gtk.ResponseType.CANCEL, 
            _('Apply'), Gtk.ResponseType.OK
        )

        file_filter = Gtk.FileFilter()
        # Translators: "Images" file chooser dialog filter
        file_filter.set_name(_("Images"))
        file_filter.add_mime_type("image/*")
        self.add_filter(file_filter)

        if len(initial_file) > 0:
            self.set_filename(initial_file)


class IconFileSelectionDemoWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Icon File Selection Dialog Example")

        self.set_border_width(6)

        button = Gtk.Button(label="Open dialog")
        button.connect("clicked", self.on_button_clicked)

        self.add(button)

    def on_button_clicked(self, widget):
        dialog = IconFileSelectionDialog(self, "", False)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            print("The OK button was clicked")
            print("Filename:", dialog.get_filename())
        elif response == Gtk.ResponseType.CANCEL:
            print("The Cancel button was clicked")

        dialog.destroy()

        self.destroy()


if __name__ == "__main__":
    win = IconFileSelectionDemoWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
