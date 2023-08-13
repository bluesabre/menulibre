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
import os

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango, GObject, GdkPixbuf


class IconEntry(Gtk.MenuButton):
    __gsignals__ = {
        'value-changed': (GObject.SignalFlags.RUN_FIRST, None, (str, str,)),
    }

    def __init__(self, use_headerbar):
        super().__init__()

        self._value = ""

        menu = Gtk.Menu.new()
        self.set_popup(menu)

        item = Gtk.MenuItem.new_with_label(_("Browse Icons…"))
        item.connect("activate", self._on_browse_icons_clicked, use_headerbar)
        menu.append(item)

        item = Gtk.MenuItem.new_with_label(_("Browse Files…"))
        item.connect("activate", self._on_browse_files_clicked, use_headerbar)
        menu.append(item)

        menu.show_all()

        overlay = Gtk.Overlay.new()
        overlay.set_size_request(48, 48)
        self.add(overlay)

        self._image = Gtk.Image.new_from_icon_name(
            "folder", Gtk.IconSize.DIALOG)
        self._image.set_pixel_size(48)
        overlay.add(self._image)

        self._overlay_image = Gtk.Image.new_from_icon_name(
            "dialog-warning", Gtk.IconSize.MENU)
        self._overlay_image.set_pixel_size(16)
        self._overlay_image.set_halign(Gtk.Align.END)
        self._overlay_image.set_valign(Gtk.Align.END)
        self._overlay_image.set_no_show_all(True)
        overlay.add_overlay(self._overlay_image)
        overlay.set_overlay_pass_through(self._overlay_image, True)

    def _on_browse_icons_clicked(self, widget, use_headerbar):
        dialog = IconSelectionDialog(self.get_toplevel(), "", use_headerbar)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            self._set_image(dialog.get_icon())

        dialog.destroy()

    def _on_browse_files_clicked(self, widget, use_headerbar):
        dialog = IconFileSelectionDialog(
            self.get_toplevel(), "", use_headerbar)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            self._set_image(dialog.get_filename())

        dialog.destroy()

    def set_value(self, value):
        self._set_image(value)

    def _set_image(self, icon_name):
        # Load the Icon Theme.
        icon_theme = Gtk.IconTheme.get_default()

        if icon_name is not None:
            # If the Icon Theme has the icon, set the image to that icon.
            if icon_theme.has_icon(icon_name):
                self._image.set_from_icon_name(icon_name, 48)
                self._on_successful_image(icon_name, icon_name)
                return

            # If the Icon Theme has a symbolic version of the icon, set the
            # image to that icon.
            if icon_theme.has_icon(icon_name + "-symbolic"):
                icon_name = icon_name + "-symbolic"
                self._image.set_from_icon_name(icon_name, 48)
                self._on_successful_image(icon_name, icon_name)
                return

            # If the icon name is actually a file, render it to the Image.
            elif os.path.isfile(icon_name):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_name)
                scaled = pixbuf.scale_simple(48, 48,
                                             GdkPixbuf.InterpType.HYPER)
                self._image.set_from_pixbuf(scaled)
                self._on_successful_image(icon_name, icon_name)
                return

            else:
                if icon_name.startswith("applications-"):
                    replacement_icon_name = "folder"
                elif icon_name == "gnome-settings":
                    replacement_icon_name = "folder"
                else:
                    replacement_icon_name = "application-x-executable"

                self._image.set_from_icon_name(replacement_icon_name, 48)
                self._on_error_image(
                    icon_name,
                    _("<i>Missing icon:</i> %s") %
                    icon_name)
                return

        if icon_theme.has_icon("applications-other"):
            icon_name = "applications-other"
        else:
            icon_name = "application-x-executable"

        self._image.set_from_icon_name(icon_name, 48)
        self._on_successful_image(icon_name, icon_name)

    def get_value(self):
        return self._value

    def _on_successful_image(self, icon_name, tooltip_text):
        self.set_tooltip_text(tooltip_text)
        self._image.set_opacity(1.0)
        self._overlay_image.hide()
        self._value = icon_name
        self.emit('value-changed', 'Icon', icon_name)

    def _on_error_image(self, icon_name, tooltip_markup):
        self.set_tooltip_markup(tooltip_markup)
        self._image.set_opacity(0.7)
        self._overlay_image.show()
        self._value = icon_name
        self.emit('value-changed', 'Icon', icon_name)


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


class IconSelectionDialog(Gtk.Dialog):

    def __init__(self, parent, initial_icon="", use_header_bar=False):
        super().__init__(title=_("Select an icon"), transient_for=parent,
                         use_header_bar=use_header_bar, flags=0)
        self.add_buttons(
            _('Cancel'), Gtk.ResponseType.CANCEL,
            _('Apply'), Gtk.ResponseType.OK
        )

        self.set_default_size(640, 480)
        self.set_default_response(Gtk.ResponseType.OK)

        box = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(9)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)

        search = Gtk.SearchEntry.new()
        box.pack_start(search, False, False, 0)

        scrolled = Gtk.ScrolledWindow.new(None, None)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        box.pack_start(scrolled, True, True, 0)

        self.treeview = IconSelectionTreeView(search)
        self.treeview.connect("row-activated", self._on_treeview_row_activated)
        scrolled.add(self.treeview)

        search.connect(
            "search-changed",
            self._on_search_changed,
            self.treeview)
        self.connect("key-press-event", self._on_key_press_event, search)

        self.get_content_area().pack_start(box, True, True, 0)
        self.show_all()

        if len(initial_icon) > 0:
            self.treeview.set_icon(initial_icon)

        self.treeview.grab_focus()

    def _on_search_changed(self, widget, treeview):
        treeview.refilter()
        treeview.set_cursor(Gtk.TreePath.new_first())

    def _on_treeview_row_activated(self, tree_view, path, column):
        self.response(Gtk.ResponseType.OK)

    def _on_key_press_event(self, widget, event, search):
        if not bool(event.get_state() & Gdk.ModifierType.CONTROL_MASK):
            return False
        if Gdk.keyval_name(event.get_keyval()[1]).lower() != 'f':
            return False
        search.grab_focus()

    def get_icon(self):
        return self.treeview.get_icon()


class IconSelectionTreeView(Gtk.TreeView):
    def __init__(self, search_entry):
        super().__init__()

        icons = Gtk.ListStore.new([str, str])

        icon_theme = Gtk.IconTheme.get_default()
        icons_list = icon_theme.list_icons(None)
        icons_list = sorted(icons_list, key=lambda x: x[0].lower())

        for icon_name in icons_list:
            icons.append([icon_name.lower(), icon_name])

        self.filter = icons.filter_new()
        self.filter.set_visible_func(self._icon_sel_match_func, search_entry)

        self.set_model(Gtk.TreeModelSort(model=self.filter))
        self.set_headers_visible(False)
        self.set_enable_search(False)

        icon_col = Gtk.TreeViewColumn.new()
        icon_col.set_sort_column_id(0)
        renderer_pixbuf = Gtk.CellRendererPixbuf()
        renderer_pixbuf.set_property('width', 32)
        renderer_pixbuf.set_property('height', 32)
        icon_col.pack_start(renderer_pixbuf, False)
        icon_col.add_attribute(renderer_pixbuf, "icon-name", 1)
        self.append_column(icon_col)

        text_col = Gtk.TreeViewColumn.new()
        text_col.set_sort_column_id(0)
        renderer_text = Gtk.CellRendererText()
        renderer_text.set_property('ellipsize', Pango.EllipsizeMode.END)
        text_col.pack_start(renderer_text, True)
        text_col.add_attribute(renderer_text, "text", 1)
        self.append_column(text_col)
        text_col.emit("clicked")

    def refilter(self):
        self.filter.refilter()

    def _icon_sel_match_func(self, model, treeiter, entry):
        query = str(entry.get_text().lower())

        if query == "":
            return True

        return query in model[treeiter][0].lower()

    def _get_path_to_icon(self, icon_name):
        model = self.get_model()
        idx = 0
        treeiter = model.get_iter_first()
        while treeiter is not None:
            if model[treeiter][0] == icon_name:
                return Gtk.TreePath.new_from_string(str(idx))
            treeiter = model.iter_next(treeiter)
            idx = idx + 1
        return None

    def set_icon(self, icon_name):
        path = self._get_path_to_icon(icon_name.lower())
        if path is not None:
            self.set_cursor(path)
        else:
            self.set_cursor(Gtk.TreePath.new_first())

    def get_icon(self):
        model, treeiter = self.get_selection().get_selected()
        return model[treeiter][0]
