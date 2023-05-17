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

import os
import re
from locale import gettext as _

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GObject


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
        'X-XFCE-SettingsDialog', 'X-XFCE-SystemSettings', 'Xfce'
    ),
    'GNOME': (
        'X-GNOME-NetworkSettings', 'X-GNOME-PersonalSettings', 'X-GNOME-Settings-Panel',
        'X-GNOME-Utilities', 'GNOME', 'GTK'
    )
}


category_descriptions = {
    # Translators: Launcher section description
    'AudioVideo': _('Multimedia'),
    # Translators: Launcher section description
    'Development': _('Development'),
    # Translators: Launcher section description
    'Education': _('Education'),
    # Translators: Launcher section description
    'Game': _('Games'),
    # Translators: Launcher section description
    'Graphics': _('Graphics'),
    # Translators: Launcher section description
    'Network': _('Internet'),
    # Translators: Launcher section description
    'Office': _('Office'),
    # Translators: Launcher section description
    'Settings': _('Settings'),
    # Translators: Launcher section description
    'System': _('System'),
    # Translators: Launcher section description
    'Utility': _('Accessories'),
    # Translators: Launcher section description
    'WINE': _('WINE'),
    # Translators: Launcher section description
    'Other': _('Other'),

    # Translators: Launcher category in the Utility section
    'Accessibility': _('Accessibility'),
    # Translators: Launcher category in the Utility section
    'Archiving': _('Archiving'),
    # Translators: Launcher category in the Utility section
    'Calculator': _('Calculator'),
    # Translators: Launcher category in the Utility section
    'Clock': _('Clock'),
    # Translators: Launcher category in the Utility section
    'Compression': _('Compression'),
    # Translators: Launcher category in the Utility section
    'FileTools': _('File Tools'),
    # Translators: Launcher category in the Utility section
    'TextEditor': _('Text Editor'),
    # Translators: Launcher category in the Utility section
    'TextTools': _('Text Tools'),

    # Translators: Launcher category in the Development section
    'Building': _('Building'),
    # Translators: Launcher category in the Development section
    'Debugger': _('Debugger'),
    # Translators: Launcher category in the Development section
    'IDE': _('IDE'),
    # Translators: Launcher category in the Development section
    'GUIDesigner': _('GUI Designer'),
    # Translators: Launcher category in the Development section
    'Profiling': _('Profiling'),
    # Translators: Launcher category in the Development section
    'RevisionControl': _('Revision Control'),
    # Translators: Launcher category in the Development section
    'Translation': _('Translation'),
    # Translators: Launcher category in the Development section
    'WebDevelopment': _('Web Development'),

    # Translators: Launcher category in the Education section
    'Art': _('Art'),
    # Translators: Launcher category in the Education section
    'ArtificialIntelligence': _('Artificial Intelligence'),
    # Translators: Launcher category in the Education section
    'Astronomy': _('Astronomy'),
    # Translators: Launcher category in the Education section
    'Biology': _('Biology'),
    # Translators: Launcher category in the Education section
    'Chemistry': _('Chemistry'),
    # Translators: Launcher category in the Education section
    'ComputerScience': _('Computer Science'),
    # Translators: Launcher category in the Education section
    'Construction': _('Construction'),
    # Translators: Launcher category in the Education section
    'DataVisualization': _('Data Visualization'),
    # Translators: Launcher category in the Education section
    'Economy': _('Economy'),
    # Translators: Launcher category in the Education section
    'Electricity': _('Electricity'),
    # Translators: Launcher category in the Education section
    'Geography': _('Geography'),
    # Translators: Launcher category in the Education section
    'Geology': _('Geology'),
    # Translators: Launcher category in the Education section
    'Geoscience': _('Geoscience'),
    # Translators: Launcher category in the Education section
    'History': _('History'),
    # Translators: Launcher category in the Education section
    'Humanities': _('Humanities'),
    # Translators: Launcher category in the Education section
    'ImageProcessing': _('Image Processing'),
    # Translators: Launcher category in the Education section
    'Languages': _('Languages'),
    # Translators: Launcher category in the Education section
    'Literature': _('Literature'),
    # Translators: Launcher category in the Education section
    'Maps': _('Maps'),
    # Translators: Launcher category in the Education section
    'Math': _('Math'),
    # Translators: Launcher category in the Education section
    'MedicalSoftware': _('Medical Software'),
    # Translators: Launcher category in the Education section
    'Music': _('Music'),
    # Translators: Launcher category in the Education section
    'NumericalAnalysis': _('Numerical Analysis'),
    # Translators: Launcher category in the Education section
    'ParallelComputing': _('Parallel Computing'),
    # Translators: Launcher category in the Education section
    'Physics': _('Physics'),
    # Translators: Launcher category in the Education section
    'Robotics': _('Robotics'),
    # Translators: Launcher category in the Education section
    'Spirituality': _('Spirituality'),
    # Translators: Launcher category in the Education section
    'Sports': _('Sports'),

    # Translators: Launcher category in the Game section
    'ActionGame': _('Action Game'),
    # Translators: Launcher category in the Game section
    'AdventureGame': _('Adventure Game'),
    # Translators: Launcher category in the Game section
    'ArcadeGame': _('Arcade Game'),
    # Translators: Launcher category in the Game section
    'BoardGame': _('Board Game'),
    # Translators: Launcher category in the Game section
    'BlocksGame': _('Blocks Game'),
    # Translators: Launcher category in the Game section
    'CardGame': _('Card Game'),
    # Translators: Launcher category in the Game section
    'Emulator': _('Emulator'),
    # Translators: Launcher category in the Game section
    'KidsGame': _('Kids Game'),
    # Translators: Launcher category in the Game section
    'LogicGame': _('Logic Game'),
    # Translators: Launcher category in the Game section
    'RolePlaying': _('Role Playing'),
    # Translators: Launcher category in the Game section
    'Shooter': _('Shooter'),
    # Translators: Launcher category in the Game section
    'Simulation': _('Simulation'),
    # Translators: Launcher category in the Game section
    'SportsGame': _('Sports Game'),
    # Translators: Launcher category in the Game section
    'StrategyGame': _('Strategy Game'),

    # Translators: Launcher category in the Graphics section
    '2DGraphics': _('2D Graphics'),
    # Translators: Launcher category in the Graphics section
    '3DGraphics': _('3D Graphics'),
    # Translators: Launcher category in the Graphics section
    'OCR': _('OCR'),
    # Translators: Launcher category in the Graphics section
    'Photography': _('Photography'),
    # Translators: Launcher category in the Graphics section
    'Publishing': _('Publishing'),
    # Translators: Launcher category in the Graphics section
    'RasterGraphics': _('Raster Graphics'),
    # Translators: Launcher category in the Graphics section
    'Scanning': _('Scanning'),
    # Translators: Launcher category in the Graphics section
    'VectorGraphics': _('Vector Graphics'),
    # Translators: Launcher category in the Graphics section
    'Viewer': _('Viewer'),

    # Translators: Launcher category in the Network section
    'Chat': _('Chat'),
    # Translators: Launcher category in the Network section
    'Dialup': _('Dialup'),
    # Translators: Launcher category in the Network section
    'Feed': _('Feed'),
    # Translators: Launcher category in the Network section
    'FileTransfer': _('File Transfer'),
    # Translators: Launcher category in the Network section
    'HamRadio': _('Ham Radio'),
    # Translators: Launcher category in the Network section
    'InstantMessaging': _('Instant Messaging'),
    # Translators: Launcher category in the Network section
    'IRCClient': _('IRC Client'),
    # Translators: Launcher category in the Network section
    'Monitor': _('Monitor'),
    # Translators: Launcher category in the Network section
    'News': _('News'),
    # Translators: Launcher category in the Network section
    'P2P': _('P2P'),
    # Translators: Launcher category in the Network section
    'RemoteAccess': _('Remote Access'),
    # Translators: Launcher category in the Network section
    'Telephony': _('Telephony'),
    # Translators: Launcher category in the Network section
    'TelephonyTools': _('Telephony Tools'),
    # Translators: Launcher category in the Network section
    'WebBrowser': _('Web Browser'),
    # Translators: Launcher category in the Network section
    'WebDevelopment': _('Web Development'),

    # Translators: Launcher category in the AudioVideo section
    'Audio': _('Audio'),
    # Translators: Launcher category in the AudioVideo section
    'AudioVideoEditing': _('Audio Video Editing'),
    # Translators: Launcher category in the AudioVideo section
    'DiscBurning': _('Disc Burning'),
    # Translators: Launcher category in the AudioVideo section
    'Midi': _('Midi'),
    # Translators: Launcher category in the AudioVideo section
    'Mixer': _('Mixer'),
    # Translators: Launcher category in the AudioVideo section
    'Player': _('Player'),
    # Translators: Launcher category in the AudioVideo section
    'Recorder': _('Recorder'),
    # Translators: Launcher category in the AudioVideo section
    'Sequencer': _('Sequencer'),
    # Translators: Launcher category in the AudioVideo section
    'Tuner': _('Tuner'),
    # Translators: Launcher category in the AudioVideo section
    'TV': _('TV'),
    # Translators: Launcher category in the AudioVideo section
    'Video': _('Video'),

    # Translators: Launcher category in the Office section
    'Calendar': _('Calendar'),
    # Translators: Launcher category in the Office section
    'ContactManagement': _('Contact Management'),
    # Translators: Launcher category in the Office section
    'Database': _('Database'),
    # Translators: Launcher category in the Office section
    'Dictionary': _('Dictionary'),
    # Translators: Launcher category in the Office section
    'Chart': _('Chart'),
    # Translators: Launcher category in the Office section
    'Email': _('Email'),
    # Translators: Launcher category in the Office section
    'Finance': _('Finance'),
    # Translators: Launcher category in the Office section
    'FlowChart': _('Flow chart'),
    # Translators: Launcher category in the Office section
    'PDA': _('PDA'),
    # Translators: Launcher category in the Office section
    'Photography': _('Photography'),
    # Translators: Launcher category in the Office section
    'ProjectManagement': _('Project Management'),
    # Translators: Launcher category in the Office section
    'Presentation': _('Presentation'),
    # Translators: Launcher category in the Office section
    'Publishing': _('Publishing'),
    # Translators: Launcher category in the Office section
    'Spreadsheet': _('Spreadsheet'),
    # Translators: Launcher category in the Office section
    'WordProcessor': _('Word Processor'),

    # Translators: Launcher category in the Settings section
    'Accessibility': _('Accessibility'),
    # Translators: Launcher category in the Settings section
    'DesktopSettings': _('Desktop Settings'),
    # Translators: Launcher category in the Settings section
    'HardwareSettings': _('Hardware Settings'),
    # Translators: Launcher category in the Settings section
    'PackageManager': _('Package Manager'),
    # Translators: Launcher category in the Settings section
    'Printing': _('Printing'),
    # Translators: Launcher category in the Settings section
    'Security': _('Security'),

    # Translators: Launcher category in the System section
    'Emulator': _('Emulator'),
    # Translators: Launcher category in the System section
    'FileManager': _('File Manager'),
    # Translators: Launcher category in the System section
    'Filesystem': _('Filesystem'),
    # Translators: Launcher category in the System section
    'FileTools': _('File Tools'),
    # Translators: Launcher category in the System section
    'Monitor': _('Monitor'),
    # Translators: Launcher category in the System section
    'Security': _('Security'),
    # Translators: Launcher category in the System section
    'TerminalEmulator': _('Terminal Emulator'),
    
    # Translators: Vendor-neutral launcher category
    'NetworkSettings': _('Network Settings'),
    # Translators: Vendor-neutral launcher category
    'PersonalSettings': _('Personal Settings'),
    # Translators: Vendor-neutral launcher category
    'Settings-Panel': _('Panel Settings'),
    # Translators: Vendor-neutral launcher category
    'SettingsDialog': _('Settings Dialog'),
    # Translators: Vendor-neutral launcher category
    'SystemSettings': _('System Settings'),
    # Translators: Vendor-neutral launcher category
    'Toplevel': _('Toplevel'),
    # Translators: Vendor-neutral launcher category
    'Utilities': _('Utilities'),

    # Translators: Launcher category specific to a desktop environment
    'GNOME': _('GNOME'),
    # Translators: Launcher category specific to a desktop environment
    'GTK': _('GTK'),
    # Translators: Launcher category specific to a desktop environment
    'XFCE': _('Xfce'),
}


def lookup_vendor_category_description(spec_name):
    if spec_name.lower().startswith("x-red-hat-"):
        unvendored = spec_name[10:]
    elif spec_name.startswith("X-"):
        unvendored = "-".join(spec_name.split("-")[2:])

    try:
        description = category_descriptions[unvendored]
        return _("%s (%s)") % (description, spec_name)
    except KeyError:
        pass

    return spec_name


def lookup_category_description(spec_name):
    """Return a valid description string for a spec entry."""
    try:
        return category_descriptions[spec_name]
    except KeyError:
        pass

    if spec_name.startswith("X-"):
        return lookup_vendor_category_description(spec_name)

    try:
        return category_descriptions[spec_name]
    except KeyError:
        pass

    # Regex <3 Split CamelCase into separate words.
    try:
        description = re.sub('(?!^)([A-Z]+)', r' \1', spec_name)
        description = description.replace("X- ", "")
        description = description.replace("-", "")
    except TypeError:
        # Translators: "Other" category group. This item is only displayed for
        # unknown or non-standard categories.
        description = _("Other")
    return description


def lookup_section_description(spec_name):
    if spec_name in ['GNOME', 'GTK', 'XFCE', 'Xfce']:
        return spec_name
    return lookup_category_description(spec_name)


COL_CATEGORY = 0
COL_SECTION = 1
COL_DESC = 2


class CategoryEditor(Gtk.Box):
    __gsignals__ = {
        'value-changed': (GObject.SignalFlags.RUN_FIRST, None, (str, str,)),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        scrolled = Gtk.ScrolledWindow.new(hadjustment=None, vadjustment=None)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        self.pack_start(scrolled, True, True, 0)

        self._options = Gtk.TreeStore.new([str])
        self._treestore = Gtk.TreeStore.new([str, str, str])

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
                                          renderer_combo, text=2)
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

        self._row_change_inhibit = False
        self._row_change_singleton = False
        self._treestore.connect("row-changed", self._on_row_changed)
        self._treestore.connect("row-inserted", self._on_row_inserted, treeview, remove_button, clear_button)
        self._treestore.connect("row-deleted", self._on_row_deleted, remove_button, clear_button)

        self._prefix = ""
        self._removals = []

        self.show_all()

    def set_prefix(self, value):
        self._prefix = value

    def set_value(self, value):
        self._row_change_inhibit = True

        self._clear()

        categories = []
        if value is not None:
            for cat in value.split(";"):
                cat = cat.strip()
                if len(cat) > 0 and cat not in categories:
                    categories.append(cat)
            categories.sort()

        for category in categories:
            self._append(category)

        self._row_change_inhibit = False

    def _get_categories(self):
        model = self._treestore
        categories = []
        for row in model:
            if row[0] not in categories:
                categories.append(row[0])
        categories.sort()
        return categories

    def get_value(self):
        categories = self._get_categories()
        if len(categories) > 0:
            categories.sort()
            return "%s;" % ";".join(categories)
        return ""

    def _get_required_categories(self, parent_directory):
        if parent_directory is None:
            if self._prefix == "xfce-":
                return ['X-XFCE', 'X-Xfce-Toplevel']
            return []

        basename = os.path.basename(parent_directory)
        name, ext = os.path.splitext(basename)

        # Handle directories like xfce-development
        if name.startswith(self._prefix):
            name = name[len(self._prefix):]
            name = name.title()

        if name == 'Accessories':
            return ['Utility']

        if name == 'Games':
            return ['Game']

        if name == 'Multimedia':
            return ['AudioVideo']

        return [name]

    def insert_required_categories(self, parent_directory):
        current_categories = self._get_categories()
        for category in self._get_required_categories(parent_directory):
            if category not in current_categories:
                self._append(category)

    def _on_row_changed(self, model, path, treeiter):
        if self._row_change_singleton:
            self._row_change_singleton = False
            return
        self._row_change_singleton = True
        self.emit('value-changed', 'Categories', self.get_value())

    def _on_row_inserted(self, model, path, treeiter, treeview, remove_button, clear_button):
        if not self._row_change_inhibit:
            treeview.set_cursor(path, treeview.get_column(0), True)
        remove_button.set_sensitive(True)
        clear_button.set_sensitive(True)

    def _on_row_deleted(self, model, path, remove_button, clear_button):
        sensitive = len(self._treestore) > 0
        remove_button.set_sensitive(sensitive)
        clear_button.set_sensitive(sensitive)

    def _clear(self):
        self._treestore.clear()
        self._removals = []

    def _append(self, category):
        section_desc, category_desc = self._add_category(category)
        self._treestore.append(None, [category, section_desc, category_desc])

    def _on_add_clicked(self, widget):
        self._treestore.append(None, ["", "", ""])

    def _on_remove_clicked(self, widget, treeview):
        model, treeiter = treeview.get_selection().get_selected()
        if model is not None and treeiter is not None:
            self._removals.append(model[treeiter][0])
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
                section = "Other"
        elif section is None:
            section = "Other"
        section_desc = lookup_section_description(section)
        if section is not None and section not in list(self._section_lookup.keys()):
            self._options.append(None, [section_desc])
            self._section_lookup[section] = str(len(list(self._section_lookup.keys())))
        parent = self._options.get_iter(self._section_lookup[section])
        self._options.append(parent, [category])
        category_desc = lookup_category_description(category)
        self._category_lookup[category] = (section_desc, category_desc)
        return self._category_lookup[category]

    def _initialize_categories(self):
        # Sourced from https://specifications.freedesktop.org/menu-spec/latest/apa.html
        # and https://specifications.freedesktop.org/menu-spec/latest/apas02.html ,
        # in addition category group names have been added to the list where launchers
        # typically use them (e.g. plain 'Utility' to add to Accessories), to allow the
        # user to restore default categories that have been manually removed

        keys = list(category_groups.keys())
        keys = sorted(keys, key=lambda group: lookup_section_description(group))

        for key in keys:
            try:
                categories = list(category_groups[key])
                categories.sort()
                for category in categories:
                    self._add_category(category, key)
            except KeyError:
                pass

    def _on_combo_changed(self, widget, path, text):
        section_desc, category_desc = self._category_lookup[text]
        self._treestore[path][COL_CATEGORY] = text
        self._treestore[path][COL_SECTION] = section_desc
        self._treestore[path][COL_DESC] = category_desc


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
