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

import json
from locale import gettext as _

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GObject


COL_SHOW = 0
COL_NAME = 1
COL_DISPLAYED = 2
COL_COMMAND = 3


class ActionEditor(Gtk.Box):
    __gsignals__ = {
        'value-changed': (GObject.SignalFlags.RUN_FIRST, None, (str, str,)),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        scrolled = Gtk.ScrolledWindow.new(hadjustment=None, vadjustment=None)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        self.pack_start(scrolled, True, True, 0)

        self._liststore = Gtk.ListStore.new([bool, str, str, str])

        treeview = Gtk.TreeView.new_with_model(self._liststore)
        treeview.set_enable_search(False)
        treeview.set_show_expanders(False)
        scrolled.add(treeview)

        renderer = Gtk.CellRendererToggle()
        renderer.set_property("activatable", True)
        renderer.connect("toggled", self._on_toggle_changed)

        # Translators: "Show" tree column header
        col = Gtk.TreeViewColumn(_("Show"), renderer, active=COL_SHOW)
        treeview.append_column(col)

        renderer = Gtk.CellRendererText()
        renderer.set_property("editable", True)
        renderer.connect('edited', self._on_edited, COL_DISPLAYED)

        # Translators: "Name" tree column header
        col = Gtk.TreeViewColumn(_("Name"), renderer, text=COL_DISPLAYED)
        treeview.append_column(col)

        renderer = Gtk.CellRendererText()
        renderer.set_property("editable", True)
        renderer.connect('edited', self._on_edited, COL_COMMAND)

        # Translators: "Command" tree column header
        col = Gtk.TreeViewColumn(_("Command"), renderer, text=COL_COMMAND)
        treeview.append_column(col)

        toolbar = Gtk.Toolbar.new()
        context = toolbar.get_style_context()
        context.add_class("inline-toolbar")
        self.add(toolbar)

        add_button = self._make_button(_("Add"), "list-add-symbolic")
        add_button.connect("clicked", self._on_add_clicked)
        toolbar.add(add_button)

        remove_button = self._make_button(_("Remove"), "list-remove-symbolic", False)
        remove_button.connect("clicked", self._on_remove_clicked, treeview)
        toolbar.add(remove_button)

        clear_button = self._make_button(_("Clear"), "list-remove-all-symbolic", False)
        clear_button.connect("clicked", self._on_clear_clicked)
        toolbar.add(clear_button)

        up_button = self._make_button(_("Move Up"), "go-up-symbolic", False)
        up_button.connect("clicked", self._on_move_clicked, treeview, -1)
        toolbar.add(up_button)

        down_button = self._make_button(_("Move Down"), "go-down-symbolic", False)
        down_button.connect("clicked", self._on_move_clicked, treeview, 1)
        toolbar.add(down_button)

        treeview.connect("cursor-changed", self._on_cursor_changed, remove_button, up_button, down_button)

        self._row_change_inhibit = False
        self._row_change_singleton = False
        self._liststore.connect("row-changed", self._on_row_changed)
        self._liststore.connect("row-inserted", self._on_row_inserted, treeview, remove_button, clear_button, up_button, down_button)
        self._liststore.connect("row-deleted", self._on_row_deleted, treeview, remove_button, clear_button, up_button, down_button)

        self.show_all()

    def remove_incomplete_actions(self):
        rows = []
        for row in self._liststore:
            if len(row[COL_NAME]) > 0 and len(row[COL_COMMAND]) > 0:
                rows.append(row[:])

        self._liststore.clear()

        for row in rows:
            self._liststore.append(row)

    def _has_prev_path(self, model, path):
        if path.copy().prev():
            return True
        return False

    def _has_next_path(self, model, path):
        try:
            current_path_str = path.to_string()
            next_path_str = str(int(current_path_str) + 1)
            next_path = Gtk.TreePath.new_from_string(next_path_str)
            model.get_iter(next_path)
        except (TypeError, ValueError):
            return False
        return True

    def _toggle_move_buttons(self, treeview, remove_button, up_button, down_button):
        try:
            model, [path] = treeview.get_selection().get_selected_rows()
        except ValueError:
            path = None

        can_up = False
        can_down = False
        can_remove = False

        if path:
            can_up = self._has_prev_path(model, path)
            can_down = self._has_next_path(model, path)
            can_remove = True

        up_button.set_sensitive(can_up)
        down_button.set_sensitive(can_down)
        remove_button.set_sensitive(can_remove)

    def _on_cursor_changed(self, treeview, remove_button, up_button, down_button):
        self._toggle_move_buttons(treeview, remove_button, up_button, down_button)

    def _on_toggle_changed(self, cell, path):
        treeiter = self._liststore.get_iter(path)
        self._liststore.set_value(treeiter, COL_SHOW, not cell.get_active())
        self.emit('value-changed', 'Actions', self.get_value())

    def _on_edited(self, widget, row, new_text, col):
        """Edited callback function to enable modifications to a cell."""
        self._liststore[row][col] = new_text
        self.emit('value-changed', 'Actions', self.get_value())

    def _on_move_clicked(self, widget, treeview, relative_position = 0):
        sel = treeview.get_selection().get_selected()
        if sel:
            model, selected_iter = sel

            # Move the row up if relative_position < 0
            if relative_position < 0:
                sibling = model.iter_previous(selected_iter)
                if sibling is not None:
                    model.move_before(selected_iter, sibling)
            else:
                sibling = model.iter_next(selected_iter)
                if sibling is not None:
                    model.move_after(selected_iter, sibling)
        self.emit('value-changed', 'Actions', self.get_value())

    def _make_button(self, label, icon_name, sensitive=True):
        image = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
        image.set_pixel_size(16)
        button = Gtk.ToolButton.new(image, label)
        button.set_sensitive(sensitive)
        return button

    def _set_actions(self, rows):
        self._row_change_inhibit = True

        self._clear()

        for row in rows:
            self._liststore.append(row)

        self._row_change_inhibit = False

    def set_value(self, value):
        if value is None:
            value = []
        else:
            value = json.loads(value)
        self._set_actions(value)

    def get_actions(self):
        model = self._liststore
        results = []
        for row in model:
            results.append(row[:])
        return results

    def get_value(self):
        return json.dumps(self.get_actions())

    def _on_row_changed(self, model, path, treeiter):
        if self._row_change_singleton:
            self._row_change_singleton = False
            return
        self._row_change_singleton = True
        self.emit('value-changed', 'Actions', self.get_value())

    def _on_row_inserted(self, model, path, treeiter, treeview, remove_button, clear_button, up_button, down_button):
        if not self._row_change_inhibit:
            treeview.set_cursor(path, treeview.get_column(0), True)
        clear_button.set_sensitive(True)
        self._toggle_move_buttons(treeview, remove_button, up_button, down_button)

    def _on_row_deleted(self, model, path, treeview, remove_button, clear_button, up_button, down_button):
        sensitive = len(self._liststore) > 0
        clear_button.set_sensitive(sensitive)
        self._toggle_move_buttons(treeview, remove_button, up_button, down_button)

    def _clear(self):
        self._liststore.clear()
        self._removals = []

    def _on_add_clicked(self, widget):
        existing = list()
        for row in self._liststore:
            existing.append(row[COL_NAME])
        name = 'NewShortcut'
        n = 1
        while name in existing:
            name = 'NewShortcut%i' % n
            n += 1
        # Translators: Placeholder text for a newly created action
        displayed = _("New Shortcut")
        self._liststore.append([True, name, displayed, ''])
        self.emit('value-changed', 'Actions', self.get_value())

    def _on_remove_clicked(self, widget, treeview):
        model, treeiter = treeview.get_selection().get_selected()
        if model is not None and treeiter is not None:
            self._removals.append(model[treeiter][0])
            model.remove(treeiter)
            self.emit('value-changed', 'Actions', self.get_value())

    def _on_clear_clicked(self, widget):
        self._clear()
        self.emit('value-changed', 'Actions', self.get_value())


class ActionEditorDemoWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Action Editor Example")

        self.set_default_size(600, 300)

        page = ActionEditor()
        page.set_value('[[true, "NewShortcut", "New Shortcut", ""], [true, "NewShortcut1", "New Shortcut", "Test"]]')
        page.connect('value-changed', self._on_value_changed)
        self.add(page)

    def _on_value_changed(self, widget, key, value):
        print(key, value)


if __name__ == "__main__":
    win = ActionEditorDemoWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
