#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2023 Sean Davis <sean@bluesabre.org>
#   Copyright (C) 2017-2018 OmegaPhil <OmegaPhil@startmail.com>
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

from gi.repository import Gtk, Pango, GObject

try:
    from . import FileHandler
except ImportError:
    pass

class ParsingErrorsDialog(Gtk.Dialog):

    def __init__(self, parent, use_header_bar=False, demo_mode=False):
        super().__init__(title=_("Parsing Errors"), transient_for=parent,
                         use_header_bar=use_header_bar, flags=0)
        self.add_buttons(
            _('Close'), Gtk.ResponseType.CLOSE,
        )

        self.set_default_size(900, 480)
        #self.set_default_size(1240, 480)

        box = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(9)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        message_area = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.pack_start(message_area, False, False, 0)

        image = Gtk.Image.new_from_icon_name("dialog-warning", Gtk.IconSize.DIALOG)
        message_area.pack_start(image, False, False, 0)

        message = Gtk.Label.new(_(
            "The following desktop files have failed parsing by the underlying library, and will therefore not show up in MenuLibre.\n"
            "Please investigate these problems with the associated package maintainer."
        ))
        message.set_line_wrap(True)
        message.set_xalign(0.0)
        message_area.pack_start(message, True, True, 0)

        scrolled = Gtk.ScrolledWindow.new(None, None)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        box.pack_start(scrolled, True, True, 0)

        self.listbox = Gtk.ListBox.new()
        scrolled.add(self.listbox)

        self.demo_mode = demo_mode
        if self.demo_mode:
            self.file_handler = None
        else:
            self.file_handler = FileHandler.FileHandler()

        self.get_content_area().pack_start(box, True, True, 0)
        self.show_all()

    def add_item(self, filename, error):
        row = ErrorRow(filename, error)
        row.connect("action", self.on_row_action)
        self.listbox.add(row)

    def on_row_action(self, row, action, filename):
        if self.demo_mode:
            print(action, filename)
            return
        if action == "open-folder":
            self.file_handler.open_folder(filename)
        elif action == "open-editor":
            self.file_handler.open_editor(filename)
        elif action == "copy-location":
            self.file_handler.copy_to_clipboard(filename)


class ErrorRow(Gtk.ListBoxRow):
    __gsignals__ = {
        'action': (GObject.SignalFlags.RUN_FIRST, None, (str,str,)),
    }

    def __init__(self, filename, error):
        super().__init__()

        box = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_border_width(3)
        box.set_margin_start(3)
        box.set_margin_end(3)

        label = Gtk.Label.new("")
        label.set_xalign(0.0)
        label.set_ellipsize(Pango.EllipsizeMode.START)
        label.set_markup("<b>%s</b>\n%s" % (filename, error))
        box.pack_start(label, True, True, 0)

        buttons = Gtk.ButtonBox.new(orientation=Gtk.Orientation.HORIZONTAL)
        buttons.set_layout(Gtk.ButtonBoxStyle.END)
        context = buttons.get_style_context()
        context.add_class("linked")
        box.pack_end(buttons, False, False, 0)

        button = Gtk.Button.new_from_icon_name("folder-symbolic", Gtk.IconSize.BUTTON)
        button.set_tooltip_text(_("Open containing folder"))
        button.connect("clicked", self.emit_action, filename, "open-folder")
        buttons.add(button)

        button = Gtk.Button.new_from_icon_name("text-editor-symbolic", Gtk.IconSize.BUTTON)
        button.set_tooltip_text(_("Open in text editor"))
        button.connect("clicked", self.emit_action, filename, "open-editor")
        buttons.add(button)

        button = Gtk.Button.new_from_icon_name("edit-copy-symbolic", Gtk.IconSize.BUTTON)
        button.set_tooltip_text(_("Copy file location"))
        button.connect("clicked", self.emit_action, filename, "copy-location")
        buttons.add(button)

        self.add(box)

        self.show_all()

    def emit_action(self, button, filename, action):
        self.emit("action", action, filename)


class ParsingErrorsDemoWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Parsing Errors Dialog Example")

        self.set_border_width(6)

        button = Gtk.Button(label="Open dialog")
        button.connect("clicked", self.on_button_clicked)

        self.add(button)

    def on_button_clicked(self, widget):
        dialog = ParsingErrorsDialog(self, True, True)

        for i in range(10):
            dialog.add_item("/var/home/bluesabre/.local/share/applications/broken.desktop", "Exec program 'failed-app' has not been found in the PATH")
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            print("The OK button was clicked")
            print("Filename:", dialog.get_filename())
        elif response == Gtk.ResponseType.CANCEL:
            print("The Cancel button was clicked")

        dialog.destroy()

        self.destroy()


if __name__ == "__main__":
    win = ParsingErrorsDemoWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
