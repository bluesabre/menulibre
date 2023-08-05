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


class PathEntry(Gtk.Entry):
    __gsignals__ = {
        'value-changed': (GObject.SignalFlags.RUN_FIRST, None, (str, str,)),
    }

    def __init__(self, use_headerbar):
        super().__init__()

        self._value = ""

        self.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "folder-open")

        self.connect("changed", self._on_entry_changed)
        self.connect("icon-release", self._on_icon_clicked, use_headerbar)

    def set_value(self, value):
        if value is None:
            value = ""
        self.set_text(value)

    def get_value(self):
        return self.get_text()

    def _on_entry_changed(self, widget):
        self.emit('value-changed', 'Path', self.get_value())

    def _on_icon_clicked(self, entry, icon_pos, event, use_headerbar):
        """Show the file selection dialog when Path Browse is clicked."""
        # Translators: File Chooser Dialog, window title.
        title = _("Select a working directory…")
        action = Gtk.FileChooserAction.SELECT_FOLDER

        dialog = FileChooserDialog(self.get_toplevel(), title, action, use_headerbar)
        dialog.set_filename(self.get_value())
        result = dialog.run()
        if result == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            self.set_value(filename)
        dialog.destroy()
        entry.grab_focus()


class FileChooserDialog(Gtk.FileChooserDialog):
    def __init__(self, parent, title, action, use_headerbar):
        Gtk.FileChooserDialog.__init__(self, title=title, transient_for=parent,
                                       action=action, use_header_bar=use_headerbar)
        # Translators: File Chooser Dialog, cancel button.
        self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        # Translators: File Chooser Dialog, confirmation button.
        self.add_button(_("OK"), Gtk.ResponseType.OK)


class PathEntryDemoWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Path Dialog Example")

        self.set_border_width(6)

        entry = PathEntry()
        entry.set_value('badicon')
        entry.connect("value-changed", self._on_value_changed)

        self.add(entry)

    def _on_value_changed(self, widget, name, value):
        print("%s: %s" % (name, value))


if __name__ == "__main__":
    win = PathEntryDemoWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
