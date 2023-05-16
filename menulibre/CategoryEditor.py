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


class CategoryEditor(Gtk.Box):
    __gsignals__ = {
        'value-changed': (GObject.SignalFlags.RUN_FIRST, None, (str, str,)),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        scrolled = Gtk.ScrolledWindow.new(hadjustment=None, vadjustment=None)
        self.pack_start(scrolled, True, True, 0)

        self._options = Gtk.TreeStore.new([str])
        self._treestore = Gtk.TreeStore.new([str, str])

        self._section_lookup = {}
        self._category_lookup = {}
        self._initialize_categories()

        treeview = Gtk.TreeView.new_with_model(self._treestore)
        scrolled.add(treeview)

        treeview.set_enable_search(False)

        renderer_combo = Gtk.CellRendererCombo()
        renderer_combo.set_property("editable", True)
        renderer_combo.set_property("model", self._options)
        renderer_combo.set_property("text-column", 0)
        renderer_combo.set_property("has-entry", False)

        # Translators: Placeholder text for the launcher-specific category
        # selection.
        renderer_combo.set_property("placeholder-text", _("Select a category"))
        renderer_combo.connect("edited", self._on_combo_changed)

        # Translators: "Category Name" tree column header
        column_combo = Gtk.TreeViewColumn(_("Category Name"),
                                          renderer_combo, text=0)
        treeview.append_column(column_combo)

        renderer_text = Gtk.CellRendererText()

        # Translators: "Section" tree column header
        column_text = Gtk.TreeViewColumn(_("Section"),
                                         renderer_text, text=1)
        treeview.append_column(column_text)

        toolbar = Gtk.Toolbar.new()
        context = toolbar.get_style_context()
        context.add_class("inline-toolbar")
        self.add(toolbar)

        image = Gtk.Image.new_from_icon_name("list-add-symbolic", Gtk.IconSize.MENU)
        image.set_pixel_size(16)
        button = Gtk.ToolButton.new(image, _("Add"))
        button.connect("clicked", self._on_add_clicked)
        toolbar.add(button)

        image = Gtk.Image.new_from_icon_name("list-remove-symbolic", Gtk.IconSize.MENU)
        image.set_pixel_size(16)
        remove_button = Gtk.ToolButton.new(image,  _("Remove"))
        remove_button.set_sensitive(False)
        remove_button.connect("clicked", self._on_remove_clicked, treeview)
        toolbar.add(remove_button)

        image = Gtk.Image.new_from_icon_name("list-remove-all-symbolic", Gtk.IconSize.MENU)
        image.set_pixel_size(16)
        clear_button = Gtk.ToolButton.new(image,  _("Clear"))
        clear_button.set_sensitive(False)
        clear_button.connect("clicked", self._on_clear_clicked)
        toolbar.add(clear_button)

        self._row_change_singleton = False
        self._treestore.connect("row-changed", self._on_row_changed)
        self._treestore.connect("row-inserted", self._on_row_inserted, treeview, remove_button, clear_button)
        self._treestore.connect("row-deleted", self._on_row_deleted, remove_button, clear_button)

        self.show_all()

    def set_value(self, value):
        self._clear()

        categories = []
        for cat in value.split(";"):
            cat = cat.strip()
            if len(cat) > 0 and cat not in categories:
                categories.append(cat)
        categories.sort()

        for category in categories:
            self._append(category)

    def get_value(self):
        model = self._treestore
        categories = []
        for row in model:
            if row[0] not in categories:
                categories.append(row[0])
        if len(categories) > 0:
            categories.sort()
            return "%s;" % ";".join(categories)
        return ""
    
    def _on_row_changed(self, model, path, treeiter):
        if self._row_change_singleton:
            self._row_change_singleton = False
            return
        self._row_change_singleton = True
        self.emit('value-changed', 'Categories', self.get_value())

    def _on_row_inserted(self, model, path, treeiter, treeview, remove_button, clear_button):
        treeview.set_cursor(path, treeview.get_column(0), True)
        remove_button.set_sensitive(True)
        clear_button.set_sensitive(True)

    def _on_row_deleted(self, model, path, remove_button, clear_button):
        sensitive = len(self._treestore) > 0
        remove_button.set_sensitive(sensitive)
        clear_button.set_sensitive(sensitive)

    def _clear(self):
        self._treestore.clear()

    def _append(self, category):
        section = self._add_category(category)
        self._treestore.append(None, [category, section])

    def _on_add_clicked(self, widget):
        self._treestore.append(None, ["", ""])

    def _on_remove_clicked(self, widget, treeview):
        model, treeiter = treeview.get_selection().get_selected()
        if model is not None and treeiter is not None:
            model.remove(treeiter)
            self.emit('value-changed', 'Categories', self.get_value())

    def _on_clear_clicked(self, widget):
        self._clear()
        self.emit('value-changed', 'Categories', self.get_value())

    def _add_category(self, category, section=None):
        if category in list(self._category_lookup.keys()):
            return self._category_lookup[category]
        if section is None and category.startswith("X-"):
            if "x-gnome-" in category.lower():
                section = "GNOME"
            elif "x-xfce-" in category.lower():
                section = "Xfce"
            else:
                section = _("Other")
        elif section is None:
            section = _("Other")
        if section is not None and section not in list(self._section_lookup.keys()):
            self._options.append(None, [section])
            self._section_lookup[section] = str(len(list(self._section_lookup.keys())))
        parent = self._options.get_iter(self._section_lookup[section])
        self._options.append(parent, [category])
        self._category_lookup[category] = section
        return section

    def _initialize_categories(self):
        # Sourced from https://specifications.freedesktop.org/menu-spec/latest/apa.html
        # and https://specifications.freedesktop.org/menu-spec/latest/apas02.html ,
        # in addition category group names have been added to the list where launchers
        # typically use them (e.g. plain 'Utility' to add to Accessories), to allow the
        # user to restore default categories that have been manually removed
        category_groups = {
            'Utility': (
                'Accessibility', 'Archiving', 'Calculator', 'Clock',
                'Compression', 'FileTools', 'TextEditor', 'TextTools', 'Utility'
            ),
            'Development': (
                'Building', 'Debugger', 'Development', 'IDE', 'GUIDesigner',
                'Profiling', 'RevisionControl', 'Translation', 'WebDevelopment'
            ),
            'Education': (
                'Art', 'ArtificialIntelligence', 'Astronomy', 'Biology', 'Chemistry',
                'ComputerScience', 'Construction', 'DataVisualization', 'Economy',
                'Education', 'Electricity', 'Geography', 'Geology', 'Geoscience',
                'History', 'Humanities', 'ImageProcessing', 'Languages', 'Literature',
                'Maps', 'Math', 'MedicalSoftware', 'Music', 'NumericalAnalysis',
                'ParallelComputing', 'Physics', 'Robotics', 'Spirituality', 'Sports'
            ),
            'Game': (
                'ActionGame', 'AdventureGame', 'ArcadeGame', 'BoardGame',
                'BlocksGame', 'CardGame', 'Emulator', 'Game', 'KidsGame', 'LogicGame',
                'RolePlaying', 'Shooter', 'Simulation', 'SportsGame',
                'StrategyGame'
            ),
            'Graphics': (
                '2DGraphics', '3DGraphics', 'Graphics', 'OCR', 'Photography',
                'Publishing', 'RasterGraphics', 'Scanning', 'VectorGraphics', 'Viewer'
            ),
            'Network': (
                'Chat', 'Dialup', 'Feed', 'FileTransfer', 'HamRadio',
                'InstantMessaging', 'IRCClient', 'Monitor', 'News', 'Network', 'P2P',
                'RemoteAccess', 'Telephony', 'TelephonyTools', 'WebBrowser',
                'WebDevelopment'
            ),
            'AudioVideo': (
                'Audio', 'AudioVideoEditing', 'DiscBurning', 'Midi', 'Mixer', 'Player',
                'Recorder', 'Sequencer', 'Tuner', 'TV', 'Video'
            ),
            'Office': (
                'Calendar', 'ContactManagement', 'Database', 'Dictionary',
                'Chart', 'Email', 'Finance', 'FlowChart', 'Office', 'PDA',
                'Photography', 'ProjectManagement', 'Presentation', 'Publishing',
                'Spreadsheet', 'WordProcessor'
            ),
            'Settings': (
                'Accessibility', 'DesktopSettings', 'HardwareSettings',
                'PackageManager', 'Printing', 'Security', 'Settings'
            ),
            'System': (
                'Emulator', 'FileManager', 'Filesystem', 'FileTools', 'Monitor',
                'Security', 'System', 'TerminalEmulator'
            ),
            'Xfce': (
                'X-XFCE', 'X-Xfce-Toplevel', 'X-XFCE-PersonalSettings', 'X-XFCE-HardwareSettings',
                'X-XFCE-SettingsDialog', 'X-XFCE-SystemSettings'
            ),
            'GNOME': (
                'X-GNOME-NetworkSettings', 'X-GNOME-PersonalSettings', 'X-GNOME-Settings-Panel',
                'X-GNOME-Utilities'
            )
        }

        keys = list(category_groups.keys())
        keys.sort()

        for key in keys:
            try:
                categories = list(category_groups[key])
                categories.sort()
                for category in categories:
                    self._add_category(category, key)
            except KeyError:
                pass

    def _on_combo_changed(self, widget, path, text):
        section = self._category_lookup[text]
        self._treestore[path][0] = text
        self._treestore[path][1] = section


class CategoryEditorDemoWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Category Editor Example")

        self.set_default_size(600, 300)

        page = CategoryEditor()
        page.set_value("Development;ArcadeGame;SomethingCrazy")
        page.connect('value-changed', self._on_value_changed)
        self.add(page)

    def _on_value_changed(self, widget, key, value):
        print(key, value)


if __name__ == "__main__":
    win = CategoryEditorDemoWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
