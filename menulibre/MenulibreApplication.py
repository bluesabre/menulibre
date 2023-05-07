#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2022 Sean Davis <sean@bluesabre.org>
#   Copyright (C) 2016-2018 OmegaPhil <OmegaPhil@startmail.com>
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
import shlex
import sys

import subprocess
import tempfile

from locale import gettext as _

from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gio, GLib, GObject, Gtk, Gdk, GdkPixbuf

from . import MenulibreStackSwitcher, CommandEditor
from . import IconSelectionDialog, IconFileSelectionDialog
from . import MenulibreTreeview, MenulibreHistory, Dialogs
from . import MenulibreXdg, util, MenulibreLog
from . import MenuEditor
from .util import MenuItemTypes, check_keypress, getBasename, getRelativeName, getRelatedKeys
from .util import escapeText, getCurrentDesktop, find_program, getProcessList
import menulibre_lib

import logging

logger = logging.getLogger('menulibre')

session = os.getenv("DESKTOP_SESSION", "")
root = os.getuid() == 0

current_desktop = getCurrentDesktop()

category_descriptions = {
    # Translators: Launcher category description
    'AudioVideo': _('Multimedia'),
    # Translators: Launcher category description
    'Development': _('Development'),
    # Translators: Launcher category description
    'Education': _('Education'),
    # Translators: Launcher category description
    'Game': _('Games'),
    # Translators: Launcher category description
    'Graphics': _('Graphics'),
    # Translators: Launcher category description
    'Network': _('Internet'),
    # Translators: Launcher category description
    'Office': _('Office'),
    # Translators: Launcher category description
    'Settings': _('Settings'),
    # Translators: Launcher category description
    'System': _('System'),
    # Translators: Launcher category description
    'Utility': _('Accessories'),
    # Translators: Launcher category description
    'WINE': _('WINE'),
    # Translators: Launcher category description
    'DesktopSettings': _('Desktop configuration'),
    # Translators: Launcher category description
    'PersonalSettings': _('User configuration'),
    # Translators: Launcher category description
    'HardwareSettings': _('Hardware configuration'),
    # Translators: Launcher category description
    'GNOME': _('GNOME application'),
    # Translators: Launcher category description
    'GTK': _('GTK+ application'),
    # Translators: Launcher category description
    'X-GNOME-PersonalSettings': _('GNOME user configuration'),
    # Translators: Launcher category description
    'X-GNOME-HardwareSettings': _('GNOME hardware configuration'),
    # Translators: Launcher category description
    'X-GNOME-SystemSettings': _('GNOME system configuration'),
    # Translators: Launcher category description
    'X-GNOME-Settings-Panel': _('GNOME system configuration'),
    # Translators: Launcher category description
    'XFCE': _('Xfce menu item'),
    # Translators: Launcher category description
    'X-XFCE': _('Xfce menu item'),
    # Translators: Launcher category description
    'X-Xfce-Toplevel': _('Xfce toplevel menu item'),
    # Translators: Launcher category description
    'X-XFCE-PersonalSettings': _('Xfce user configuration'),
    # Translators: Launcher category description
    'X-XFCE-HardwareSettings': _('Xfce hardware configuration'),
    # Translators: Launcher category description
    'X-XFCE-SettingsDialog': _('Xfce system configuration'),
    # Translators: Launcher category description
    'X-XFCE-SystemSettings': _('Xfce system configuration'),
}

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
    # Translators: "Other" category group. This item is only displayed for
    # unknown or non-standard categories.
    _('Other'): (
        'Amusement', 'ConsoleOnly', 'Core', 'Documentation',
        'Electronics', 'Engineering', 'GNOME', 'GTK', 'Java', 'KDE',
        'Motif', 'Qt', 'XFCE'
    ),
    'Settings': (
        'Accessibility', 'DesktopSettings', 'HardwareSettings',
        'PackageManager', 'Printing', 'Security', 'Settings'
    ),
    'System': (
        'Emulator', 'FileManager', 'Filesystem', 'FileTools', 'Monitor',
        'Security', 'System', 'TerminalEmulator'
    )
}

# DE-specific categories
if util.getDefaultMenuPrefix() == 'xfce-':
    category_groups['Xfce'] = (
        'X-XFCE', 'X-Xfce-Toplevel', 'X-XFCE-PersonalSettings', 'X-XFCE-HardwareSettings',
        'X-XFCE-SettingsDialog', 'X-XFCE-SystemSettings'
    )
elif util.getDefaultMenuPrefix() == 'gnome-':
    category_groups['GNOME'] = (
        'X-GNOME-NetworkSettings', 'X-GNOME-PersonalSettings', 'X-GNOME-Settings-Panel',
        'X-GNOME-Utilities'
    )

# Create a reverse-lookup
category_lookup = dict()
for key in list(category_groups.keys()):
    for item in category_groups[key]:
        category_lookup[item] = key


def lookup_category_description(spec_name):
    """Return a valid description string for a spec entry."""
    # if spec_name.startswith("menulibre-"):
    #    return _("User Category")
    try:
        return category_descriptions[spec_name]
    except KeyError:
        pass

    try:
        group = category_lookup[spec_name]
        return lookup_category_description(group)
    except KeyError:
        pass

    # Regex <3 Split CamelCase into separate words.
    try:
        description = re.sub('(?!^)([A-Z]+)', r' \1', spec_name)
    except TypeError:
        # Translators: "Other" category group. This item is only displayed for
        # unknown or non-standard categories.
        description = _("Other")
    return description


class MenulibreWindow(Gtk.ApplicationWindow):
    """The Menulibre application window."""

    __gsignals__ = {
        'about': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,
                  (GObject.TYPE_BOOLEAN,)),
        'help': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,
                 (GObject.TYPE_BOOLEAN,)),
        'quit': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,
                 (GObject.TYPE_BOOLEAN,))
    }

    def __init__(self, app, headerbar_pref=True):
        """Initialize the Menulibre application."""
        self.root_lockout()

        # Initialize the GtkBuilder to get our widgets from Glade.
        builder = menulibre_lib.get_builder('MenulibreWindow')

        # Set up History
        self.history = MenulibreHistory.History()
        self.history.connect('undo-changed', self.on_undo_changed)
        self.history.connect('redo-changed', self.on_redo_changed)
        self.history.connect('revert-changed', self.on_revert_changed)

        # Steal the window contents for the GtkApplication.
        self.configure_application_window(builder, app)

        self.values = dict()

        # Set up the actions and toolbar
        self.configure_application_actions(builder)

        self.use_headerbar = headerbar_pref
        if headerbar_pref:
            self.configure_headerbar(builder)
        else:
            self.configure_application_toolbar(builder)

        self.configure_css()

        # Set up the application editor
        self.configure_application_editor(builder)

        # Set up the application browser
        self.configure_application_treeview(builder)

        self.configure_menu_restart_infobar(builder)

        # Determining paths of bad desktop files GMenu can't load - if some are
        # detected, alerting user via InfoBar
        self.bad_desktop_files = util.determine_bad_desktop_files()
        if self.bad_desktop_files:
            self.configure_application_bad_desktop_files_infobar(builder)

    def root_lockout(self):
        if root:
            # Translators: This error is displayed when the application is run
            # as a root user. The application exits once the dialog is
            # dismissed.
            primary = _("MenuLibre cannot be run as root.")

            docs_url = "https://github.com/bluesabre/menulibre/wiki/Frequently-Asked-Questions"

            # Translators: This link goes to the online documentation with more
            # information.
            secondary = _("Please see the "
                          "<a href='%s'>online documentation</a> "
                          "for more information.") % docs_url

            dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.ERROR,
                                       Gtk.ButtonsType.CLOSE, primary)
            dialog.format_secondary_markup(secondary)
            dialog.run()
            sys.exit(1)

    def menu_load_failure(self):
        primary = _("MenuLibre failed to load.")

        docs_url = "https://github.com/bluesabre/menulibre/wiki/Frequently-Asked-Questions"

        # Translators: This link goes to the online documentation with more
        # information.
        secondary = _("The default menu could not be found. Please see the "
                        "<a href='%s'>online documentation</a> "
                        "for more information.") % docs_url

        secondary += "\n\n<big><b>%s</b></big>" % _("Diagnostics")

        diagnostics = util.getMenuDiagnostics()
        for k, v in diagnostics.items():
            secondary += "\n<b>%s</b>: %s" % (k, v)

        dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.ERROR,
                                    Gtk.ButtonsType.CLOSE, primary)
        dialog.format_secondary_markup(secondary)

        label = self.find_secondary_label(dialog)
        if label is not None:
            label.set_selectable(True)

        dialog.run()
        sys.exit(1)

    def find_secondary_label(self, container = None):
        try:
            children = container.get_children()
            if len(children) == 0:
                return None
            if isinstance(children[0], Gtk.Label):
                return children[1]
            for child in children:
                label = self.find_secondary_label(child)
                if label is not None:
                    return label
        except AttributeError:
            pass
        except IndexError:
            pass
        return None

    def configure_application_window(self, builder, app):
        """Glade is currently unable to create a GtkApplicationWindow.  This
        function takes the GtkWindow from the UI file and reparents the
        contents into the Menulibre GtkApplication window, preserving the
        window's properties.'"""
        # Get the GtkWindow.
        window = builder.get_object('menulibre_window')

        # Back up the window properties.
        window_title = window.get_title()
        window_icon = window.get_icon_name()
        window_contents = window.get_children()[0]
        size = window.get_default_size()
        size_request = window.get_size_request()
        position = window.get_property("window-position")

        # Initialize the GtkApplicationWindow.
        Gtk.Window.__init__(self, title=window_title, application=app)
        self.set_wmclass("MenuLibre", "MenuLibre")

        # Restore the window properties.
        self.set_title(window_title)
        self.set_icon_name(window_icon)
        self.set_default_size(size[0], size[1])
        self.set_size_request(size_request[0], size_request[1])
        self.set_position(position)

        # Reparent the widgets.
        window_contents.reparent(self)

        # Connect any window-specific events.
        self.connect('key-press-event', self.on_window_keypress_event)
        self.connect('delete-event', self.on_window_delete_event)

    def configure_css(self):
        css = """
        #MenulibreSidebar GtkToolbar.inline-toolbar,
        #MenulibreSidebar GtkScrolledWindow.frame {
            border-radius: 0px;
            border-width: 0px;
            border-right-width: 1px;
        }
        #MenulibreSidebar GtkScrolledWindow.frame {
            border-bottom-width: 1px;
        }
        """
        style_provider = Gtk.CssProvider.new()
        style_provider.load_from_data(bytes(css.encode()))

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def configure_headerbar(self, builder):
        # Configure the Add, Save, Undo, Redo, Revert, Delete widgets.
        for action_name in ['save_launcher', 'undo', 'redo',
                            'revert', 'execute', 'delete']:
            widget = builder.get_object("headerbar_%s" % action_name)
            widget.connect("clicked", self.activate_action_cb, action_name)

        self.action_items = dict()
        self.action_items['add_button'] = builder.get_object('headerbar_add')

        for action_name in ['add_launcher', 'add_directory', 'add_separator']:
            self.action_items[action_name] = []
            widget = builder.get_object('popup_%s' % action_name)
            widget.connect('activate', self.activate_action_cb, action_name)
            self.action_items[action_name].append(widget)

        # Save
        self.save_button = builder.get_object('headerbar_save_launcher')

        # Undo/Redo/Revert
        self.undo_button = builder.get_object('headerbar_undo')
        self.redo_button = builder.get_object('headerbar_redo')
        self.revert_button = builder.get_object('headerbar_revert')

        # Configure the Delete widget.
        self.delete_button = builder.get_object('headerbar_delete')

        # Configure the Test Launcher widget.
        self.execute_button = builder.get_object('headerbar_execute')

        # Configure the search widget.
        self.search_box = builder.get_object('search')
        self.search_box.connect('icon-press', self.on_search_cleared)

        self.search_box.reparent(builder.get_object('headerbar_search'))

        headerbar = builder.get_object('headerbar')
        headerbar.set_title("MenuLibre")
        headerbar.set_custom_title(Gtk.Label.new())

        builder.get_object("toolbar").hide()

        self.set_titlebar(headerbar)
        headerbar.show_all()

    def configure_application_actions(self, builder):
        """Configure the GtkActions that are used in the Menulibre
        application."""
        self.actions = {}

        # Add Launcher
        self.actions['add_launcher'] = Gtk.Action(
                name='add_launcher',
                # Translators: Add Launcher action label
                label=_('Add _Launcher…'),
                # Translators: Add Launcher action tooltip
                tooltip=_('Add Launcher…'),
                stock_id=Gtk.STOCK_NEW)

        # Add Directory
        self.actions['add_directory'] = Gtk.Action(
                name='add_directory',
                # Translators: Add Directory action label
                label=_('Add _Directory…'),
                # Translators: Add Directory action tooltip
                tooltip=_('Add Directory…'),
                stock_id=Gtk.STOCK_NEW)

        # Add Separator
        self.actions['add_separator'] = Gtk.Action(
                name='add_separator',
                # Translators: Add Separator action label
                label=_('_Add Separator…'),
                # Translators: Add Separator action tooltip
                tooltip=_('Add Separator…'),
                stock_id=Gtk.STOCK_NEW)

        # Save Launcher
        self.actions['save_launcher'] = Gtk.Action(
                name='save_launcher',
                # Translators: Save Launcher action label
                label=_('_Save'),
                # Translators: Save Launcher action tooltip
                tooltip=_('Save'),
                stock_id=Gtk.STOCK_SAVE)

        # Undo
        self.actions['undo'] = Gtk.Action(
                name='undo',
                # Translators: Undo action label
                label=_('_Undo'),
                # Translators: Undo action tooltip
                tooltip=_('Undo'),
                stock_id=Gtk.STOCK_UNDO)

        # Redo
        self.actions['redo'] = Gtk.Action(
                name='redo',
                # Translators: Redo action label
                label=_('_Redo'),
                # Translators: Redo action tooltip
                tooltip=_('Redo'),
                stock_id=Gtk.STOCK_REDO)

        # Revert
        self.actions['revert'] = Gtk.Action(
                name='revert',
                # Translators: Revert action label
                label=_('_Revert'),
                # Translators: Revert action tooltip
                tooltip=_('Revert'),
                stock_id=Gtk.STOCK_REVERT_TO_SAVED)

        # Execute
        self.actions['execute'] = Gtk.Action(
                name='execute',
                # Translators: Execute action label
                label=_('_Execute'),
                # Translators: Execute action tooltip
                tooltip=_('Execute Launcher'),
                stock_id=Gtk.STOCK_MEDIA_PLAY)

        # Delete
        self.actions['delete'] = Gtk.Action(
                name='delete',
                # Translators: Delete action label
                label=_('_Delete'),
                # Translators: Delete action tooltip
                tooltip=_('Delete'),
                stock_id=Gtk.STOCK_DELETE)

        # Quit
        self.actions['quit'] = Gtk.Action(
                name='quit',
                # Translators: Quit action label
                label=_('_Quit'),
                # Translators: Quit action tooltip
                tooltip=_('Quit'),
                stock_id=Gtk.STOCK_QUIT)

        # Help
        self.actions['help'] = Gtk.Action(
                name='help',
                # Translators: Help action label
                label=_('_Contents'),
                # Translators: Help action tooltip
                tooltip=_('Help'),
                stock_id=Gtk.STOCK_HELP)

        # About
        self.actions['about'] = Gtk.Action(
                name='about',
                # Translators: About action label
                label=_('_About'),
                # Translators: About action tooltip
                tooltip=_('About'),
                stock_id=Gtk.STOCK_ABOUT)

        # Connect the GtkAction events.
        self.actions['add_launcher'].connect('activate',
                                             self.on_add_launcher_cb)
        self.actions['add_directory'].connect('activate',
                                              self.on_add_directory_cb)
        self.actions['add_separator'].connect('activate',
                                              self.on_add_separator_cb)
        self.actions['save_launcher'].connect('activate',
                                              self.on_save_launcher_cb,
                                              builder)
        self.actions['undo'].connect('activate', self.on_undo_cb)
        self.actions['redo'].connect('activate', self.on_redo_cb)
        self.actions['revert'].connect('activate', self.on_revert_cb)
        self.actions['execute'].connect('activate', self.on_execute_cb,
                                        builder)
        self.actions['delete'].connect('activate', self.on_delete_cb)
        self.actions['quit'].connect('activate', self.on_quit_cb)
        self.actions['help'].connect('activate', self.on_help_cb)
        self.actions['about'].connect('activate', self.on_about_cb)

    def configure_application_bad_desktop_files_infobar(self, builder):
        """Configure InfoBar to alert user to bad desktop files."""

        # Fetching UI widgets
        self.infobar = builder.get_object('bad_desktop_files_infobar')

        # Configuring buttons for the InfoBar - looks like you can't set a
        # response ID via a button defined in glade?
        # Can't get a stock button then change its icon, so leaving with no
        # icon
        self.infobar.add_button('Details', Gtk.ResponseType.YES)

        self.infobar.show()

        # Hook up events
        self.infobar.set_default_response(Gtk.ResponseType.CLOSE)
        self.infobar.connect('response',
                             self.on_bad_desktop_files_infobar_response)

    def configure_menu_restart_infobar(self, builder):
        self.menu_restart_infobar = builder.get_object('menu_restart_required')
        self.menu_restart_infobar.set_default_response(Gtk.ResponseType.CLOSE)

        button = builder.get_object('menu_restart_button')
        button.connect('clicked', self.on_menu_restart_button_activate)

        self.menu_restart_infobar.connect('response',
                             self.on_bad_desktop_files_infobar_response)

    def on_menu_restart_infobar_response(self, infobar, response_id):
        infobar.hide()

    def configure_application_toolbar(self, builder):
        """Configure the application toolbar."""
        # Configure the Add, Save, Undo, Redo, Revert, Delete widgets.
        for action_name in ['save_launcher', 'undo', 'redo',
                            'revert', 'execute', 'delete']:
            widget = builder.get_object("toolbar_%s" % action_name)
            widget.connect("clicked", self.activate_action_cb, action_name)

        self.action_items = dict()
        self.action_items['add_button'] = builder.get_object('toolbar_add')

        for action_name in ['add_launcher', 'add_directory', 'add_separator']:
            self.action_items[action_name] = []
            widget = builder.get_object('popup_%s' % action_name)
            widget.connect('activate', self.activate_action_cb, action_name)
            self.action_items[action_name].append(widget)

        # Save
        self.save_button = builder.get_object('toolbar_save_launcher')

        # Undo/Redo/Revert
        self.undo_button = builder.get_object('toolbar_undo')
        self.redo_button = builder.get_object('toolbar_redo')
        self.revert_button = builder.get_object('toolbar_revert')

        # Configure the Delete widget.
        self.delete_button = builder.get_object('toolbar_delete')

        # Configure the Test Launcher widget.
        self.execute_button = builder.get_object('toolbar_execute')

        # Configure the search widget.
        self.search_box = builder.get_object('search')
        self.search_box.connect('icon-press', self.on_search_cleared)

    def configure_application_treeview(self, builder):
        """Configure the menu-browsing GtkTreeView."""
        self.treeview = MenulibreTreeview.Treeview(self, builder)
        if not self.treeview.loaded:
            self.menu_load_failure()
        treeview = self.treeview.get_treeview()
        treeview.set_search_entry(self.search_box)
        self.search_box.connect('changed', self.on_app_search_changed,
                                treeview, True)
        self.treeview.set_can_select_function(self.get_can_select)
        self.treeview.connect("cursor-changed",
                              self.on_apps_browser_cursor_changed, builder)
        self.treeview.connect("add-directory-enabled",
                              self.on_apps_browser_add_directory_enabled,
                              builder)
        self.treeview.connect("requires-menu-reload",
                              self.on_apps_browser_requires_menu_reload,
                              builder)
        treeview.set_cursor(Gtk.TreePath.new_from_string("1"))
        treeview.set_cursor(Gtk.TreePath.new_from_string("0"))

    def get_can_select(self):
        if self.save_button.get_sensitive():
            dialog = Dialogs.SaveOnLeaveDialog(self)

            response = dialog.run()
            dialog.destroy()
            # Cancel prevents leaving this launcher.
            if response == Gtk.ResponseType.CANCEL:
                return False
            # Don't Save allows leaving this launcher, deleting 'new'.
            elif response == Gtk.ResponseType.NO:
                filename = self.treeview.get_selected_filename()
                if filename is None:
                    self.delete_launcher()
                    return False
                return True
            # Save and move on.
            else:
                self.save_launcher()
                return True
            return False
        else:
            return True

    def configure_application_editor(self, builder):
        """Configure the editor frame."""
        placeholder = builder.get_object('settings_placeholder')
        self.switcher = MenulibreStackSwitcher.StackSwitcherBox()
        placeholder.add(self.switcher)
        self.switcher.add_child(builder.get_object('page_categories'),
                                # Translators: "Categories" launcher section
                                'categories', _('Categories'))
        self.switcher.add_child(builder.get_object('page_actions'),
                                # Translators: "Actions" launcher section
                                'actions', _('Actions'))
        self.switcher.add_child(builder.get_object('page_advanced'),
                                # Translators: "Advanced" launcher section
                                'advanced', _('Advanced'))

        # Store the editor.
        self.editor = builder.get_object('application_editor')

        # Keep a dictionary of the widgets for easy lookup and updates.
        # The keys are the DesktopSpec keys.
        self.widgets = {
            'Name': (  # GtkButton, GtkLabel, GtkEntry
                builder.get_object('button_Name'),
                builder.get_object('label_Name'),
                builder.get_object('entry_Name')),
            'Comment': (  # GtkButton, GtkLabel, GtkEntry
                builder.get_object('button_Comment'),
                builder.get_object('label_Comment'),
                builder.get_object('entry_Comment')),
            'Icon': (  # GtkButton, GtkImage
                builder.get_object('button_Icon'),
                builder.get_object('image_Icon')),
            'Filename': builder.get_object('label_Filename'),
            'Exec': builder.get_object('entry_Exec'),
            'Path': builder.get_object('entry_Path'),
            'Terminal': builder.get_object('switch_Terminal'),
            'StartupNotify': builder.get_object('switch_StartupNotify'),
            'NoDisplay': builder.get_object('switch_NoDisplay'),
            'GenericName': builder.get_object('entry_GenericName'),
            'TryExec': builder.get_object('entry_TryExec'),
            'OnlyShowIn': builder.get_object('entry_OnlyShowIn'),
            'NotShowIn': builder.get_object('entry_NotShowIn'),
            'MimeType': builder.get_object('entry_Mimetype'),
            'Keywords': builder.get_object('entry_Keywords'),
            'StartupWMClass': builder.get_object('entry_StartupWMClass'),
            'Implements': builder.get_object('entry_Implements'),
            'Hidden': builder.get_object('switch_Hidden'),
            'DBusActivatable': builder.get_object('switch_DBusActivatable'),
            'PrefersNonDefaultGPU': builder.get_object('switch_PrefersNonDefaultGPU'),
            'X-GNOME-UsesNotifications': builder.get_object('switch_UsesNotifications')
        }

        # Configure the switches
        for widget_name in ['Terminal', 'StartupNotify', 'NoDisplay', 'Hidden',
                            'DBusActivatable', 'PrefersNonDefaultGPU']:
            widget = self.widgets[widget_name]
            widget.connect('notify::active', self.on_switch_toggle,
                           widget_name)

        # These widgets are hidden when the selected item is a Directory.
        self.directory_hide_widgets = []
        for widget_name in ['details_frame', 'settings_placeholder',
                            'terminal_label', 'switch_Terminal',
                            'notify_label', 'switch_StartupNotify']:
            self.directory_hide_widgets.append(builder.get_object(widget_name))

        # Configure the Name/Comment widgets.
        for widget_name in ['Name', 'Comment']:
            button = builder.get_object('button_%s' % widget_name)
            builder.get_object('cancel_%s' % widget_name)
            builder.get_object('apply_%s' % widget_name)
            entry = builder.get_object('entry_%s' % widget_name)
            button.connect('clicked', self.on_NameComment_clicked,
                           widget_name, builder)
            entry.connect('key-press-event',
                          self.on_NameComment_key_press_event,
                          widget_name, builder)
            entry.connect('activate', self.on_NameComment_activate,
                          widget_name, builder)
            entry.connect('icon-press', self.on_NameComment_apply,
                          widget_name, builder)

        # Button Focus events
        for widget_name in ['Name', 'Comment', 'Icon']:
            button = builder.get_object('button_%s' % widget_name)
            button.connect('focus-in-event',
                           self.on_NameCommentIcon_focus_in_event)
            button.connect('focus-out-event',
                           self.on_NameCommentIcon_focus_out_event)

        for widget_name in ['Name', 'Comment']:
            entry = builder.get_object('entry_%s' % widget_name)

            # Commit changes to entries when focusing out.
            entry.connect('focus-out-event',
                          self.on_entry_focus_out_event,
                          widget_name)

            # Enable saving on any edit with an Entry.
            entry.connect("changed",
                          self.on_entry_changed,
                          widget_name)

        for widget_name in ['Exec', 'Path', 'GenericName', 'TryExec',
                            'OnlyShowIn', 'NotShowIn', 'MimeType', 'Keywords',
                            'StartupWMClass', 'Implements']:

            # Commit changes to entries when focusing out.
            self.widgets[widget_name].connect('focus-out-event',
                                              self.on_entry_focus_out_event,
                                              widget_name)

            # Enable saving on any edit with an Entry.
            self.widgets[widget_name].connect("changed",
                                              self.on_entry_changed,
                                              widget_name)

        # Configure the Exec/Path widgets.
        for widget_name in ['Path']:
            button = builder.get_object('entry_%s' % widget_name)
            button.connect('icon-press', self.on_Path_clicked, widget_name,
                           builder)
        
        button = builder.get_object('entry_Exec')
        button.connect('icon-press', self.on_Exec_clicked)

        xprop = find_program('xprop')
        if xprop is None:
            self.widgets['StartupWMClass'].set_icon_from_icon_name(
                Gtk.EntryIconPosition.SECONDARY, None)
        else:
            self.widgets['StartupWMClass'].connect(
                'icon-press', self.on_StartupWmClass_clicked)

        # Connect the Icon menu.
        select_icon_name = builder.get_object("icon_select_by_icon_name")
        select_icon_name.connect("activate",
                                 self.on_IconSelectFromIcons_clicked,
                                 builder)
        select_icon_file = builder.get_object("icon_select_by_filename")
        select_icon_file.connect("activate",
                                 self.on_IconSelectFromFilename_clicked)
        
        # Connect the Icon overlay.
        overlay = builder.get_object("icon_overlay")
        self.overlay_icon = builder.get_object("overlay_icon")
        overlay.add_overlay(self.overlay_icon)
        overlay.set_overlay_pass_through(self.overlay_icon, True)

        # Categories Treeview and Inline Toolbar
        self.categories_treeview = builder.get_object('categories_treeview')
        add_button = builder.get_object('categories_add')
        add_button.connect("clicked", self.on_categories_add)
        remove_button = builder.get_object('categories_remove')
        remove_button.connect("clicked", self.on_categories_remove)
        clear_button = builder.get_object('categories_clear')
        clear_button.connect("clicked", self.on_categories_clear)
        self.configure_categories_treeview(builder)

        # Actions Treeview and Inline Toolbar
        self.actions_treeview = builder.get_object('actions_treeview')
        model = self.actions_treeview.get_model()
        add_button = builder.get_object('actions_add')
        add_button.connect("clicked", self.on_actions_add)
        remove_button = builder.get_object('actions_remove')
        remove_button.connect("clicked", self.on_actions_remove)
        clear_button = builder.get_object('actions_clear')
        clear_button.connect("clicked", self.on_actions_clear)
        move_up = builder.get_object('actions_move_up')
        move_up.connect('clicked', self.move_action, (self.actions_treeview,
                                                      - 1))
        move_down = builder.get_object('actions_move_down')
        move_down.connect('clicked', self.move_action, (self.actions_treeview,
                                                        1))
        renderer = builder.get_object('actions_show_renderer')
        renderer.connect('toggled', self.on_actions_show_toggled, model)
        renderer = builder.get_object('actions_name_renderer')
        renderer.connect('edited', self.on_actions_text_edited, model, 2)
        renderer = builder.get_object('actions_command_renderer')
        renderer.connect('edited', self.on_actions_text_edited, model, 3)

    def configure_categories_treeview(self, builder):
        """Set the up combobox in the categories treeview editor."""
        # Populate the ListStore.
        self.categories_treestore = Gtk.TreeStore(str)
        self.categories_treefilter = self.categories_treestore.filter_new()
        self.categories_treefilter.set_visible_func(
                self.categories_treefilter_func)

        keys = list(category_groups.keys())
        keys.sort()

        # Translators: Launcher-specific categories, camelcase "This Entry"
        keys.append(_('ThisEntry'))

        for key in keys:
            parent = self.categories_treestore.append(None, [key])
            try:
                for category in category_groups[key]:
                    self.categories_treestore.append(parent, [category])
            except KeyError:
                pass

        # Create the TreeView...
        treeview = builder.get_object('categories_treeview')

        renderer_combo = Gtk.CellRendererCombo()
        renderer_combo.set_property("editable", True)
        renderer_combo.set_property("model", self.categories_treefilter)
        renderer_combo.set_property("text-column", 0)
        renderer_combo.set_property("has-entry", False)

        # Translators: Placeholder text for the launcher-specific category
        # selection.
        renderer_combo.set_property("placeholder-text", _("Select a category"))
        renderer_combo.connect("edited", self.on_category_combo_changed)

        # Translators: "Category Name" tree column header
        column_combo = Gtk.TreeViewColumn(_("Category Name"),
                                          renderer_combo, text=0)
        treeview.append_column(column_combo)

        renderer_text = Gtk.CellRendererText()

        # Translators: "Description" tree column header
        column_text = Gtk.TreeViewColumn(_("Description"),
                                         renderer_text, text=1)
        treeview.append_column(column_text)

        self.categories_treefilter.refilter()

        # Allow to keep track of categories a user has explicitly removed for a
        # desktop file
        self.categories_removed = set()

    def activate_action_cb(self, widget, action_name):
        """Activate the specified GtkAction."""
        self.actions[action_name].activate()

    def on_switch_toggle(self, widget, status, widget_name):
        """Connect switch toggle event for storing in history."""
        self.set_value(widget_name, widget.get_active())

# History Signals
    def on_undo_changed(self, history, enabled):
        """Toggle undo functionality when history is changed."""
        self.undo_button.set_sensitive(enabled)

    def on_redo_changed(self, history, enabled):
        """Toggle redo functionality when history is changed."""
        self.redo_button.set_sensitive(enabled)

    def on_revert_changed(self, history, enabled):
        """Toggle revert functionality when history is changed."""
        self.revert_button.set_sensitive(enabled)
        self.save_button.set_sensitive(enabled)
        self.actions['save_launcher'].set_sensitive(enabled)

# Generic Treeview functions
    def treeview_add(self, treeview, row_data):
        """Append the specified row_data to the treeview."""
        model = treeview.get_model()
        model.append(row_data)

    def treeview_remove(self, treeview):
        """Remove the selected row from the treeview."""
        model, treeiter = treeview.get_selection().get_selected()
        if model is not None and treeiter is not None:
            model.remove(treeiter)

    def treeview_clear(self, treeview):
        """Remove all items from the treeview."""
        model = treeview.get_model()
        model.clear()

    def treeview_get_selected_text(self, treeview, column):
        """Return selected item's text value stored at the given column (text
        is the expected data type)."""

        # Note that the categories treeview is configured to only allow one row
        # to be selected
        model, treeiter = treeview.get_selection().get_selected()
        if model is not None and treeiter is not None:
            return model[treeiter][column]
        else:
            return ''

    def cleanup_treeview(self, treeview, key_columns, sort=False):
        """Cleanup a treeview"""
        rows = []

        model = treeview.get_model()
        for row in model:
            row_data = row[:]
            append_row = True
            for key_column in key_columns:
                text = row_data[key_column].lower()
                if len(text) == 0:
                    append_row = False
            if append_row:
                rows.append(row_data)

        if sort:
            rows = sorted(rows, key=lambda row_data: row_data[key_columns[MenuEditor.COL_NAME]])

        model.clear()
        for row in rows:
            model.append(row)

# Categories
    def cleanup_categories(self):
        """Cleanup the Categories treeview. Remove any rows where category
        has not been set and sort alphabetically."""
        self.cleanup_treeview(self.categories_treeview, [0], sort=True)

    def categories_treefilter_func(self, model, treeiter, data=None):
        """Only show ThisEntry when there are child items."""
        row = model[treeiter]
        if row.get_parent() is not None:
            return True
        # Translators: "This Entry" launcher-specific category group
        if row[0] == _('This Entry'):
            return model.iter_n_children(treeiter) != 0
        return True

    def on_category_combo_changed(self, widget, path, text):
        """Set the active iter to the new text."""
        model = self.categories_treeview.get_model()
        model[path][0] = text
        description = lookup_category_description(text)
        model[path][1] = description
        self.set_value('Categories', self.get_editor_categories(), False)

    def on_categories_add(self, widget):
        """Add a new row to the Categories TreeView."""
        self.treeview_add(self.categories_treeview, ['', ''])
        self.set_value('Categories', self.get_editor_categories(), False)

    def on_categories_remove(self, widget):
        """Remove the currently selected row from the Categories TreeView."""

        # Keep track of category names user has explicitly removed
        name = self.treeview_get_selected_text(self.categories_treeview, 0)
        self.categories_removed.add(name)

        self.treeview_remove(self.categories_treeview)
        self.set_value('Categories', self.get_editor_categories(), False)

    def on_categories_clear(self, widget):
        """Clear all rows from the Categories TreeView."""
        self.treeview_clear(self.categories_treeview)
        self.set_value('Categories', self.get_editor_categories(), False)

    def cleanup_actions(self):
        """Cleanup the Actions treeview. Remove any rows where name or command
        have not been set."""
        self.cleanup_treeview(self.actions_treeview, [2, 3])

# Actions
    def on_actions_text_edited(self, w, row, new_text, model, col):
        """Edited callback function to enable modifications to a cell."""
        model[row][col] = new_text
        self.set_value('Actions', self.get_editor_actions(), False)

    def on_actions_show_toggled(self, cell, path, model=None):
        """Toggled callback function to enable modifications to a cell."""
        treeiter = model.get_iter(path)
        model.set_value(treeiter, 0, not cell.get_active())
        self.set_value('Actions', self.get_editor_actions(), False)

    def on_actions_add(self, widget):
        """Add a new row to the Actions TreeView."""
        model = self.actions_treeview.get_model()
        existing = list()
        for row in model:
            existing.append(row[1])
        name = 'NewShortcut'
        n = 1
        while name in existing:
            name = 'NewShortcut%i' % n
            n += 1
        # Translators: Placeholder text for a newly created action
        displayed = _("New Shortcut")
        self.treeview_add(self.actions_treeview, [True, name, displayed, ''])
        self.set_value('Actions', self.get_editor_actions(), False)

    def on_actions_remove(self, widget):
        """Remove the currently selected row from the Actions TreeView."""
        self.treeview_remove(self.actions_treeview)
        self.set_value('Actions', self.get_editor_actions(), False)

    def on_actions_clear(self, widget):
        """Clear all rows from the Actions TreeView."""
        self.treeview_clear(self.actions_treeview)
        self.set_value('Actions', self.get_editor_actions(), False)

    def move_action(self, widget, user_data):
        """Move row in Actions treeview."""
        # Unpack the user data
        treeview, relative_position = user_data

        sel = treeview.get_selection().get_selected()
        if sel:
            model, selected_iter = sel

            # Move the row up if relative_position < 0
            if relative_position < 0:
                sibling = model.iter_previous(selected_iter)
                model.move_before(selected_iter, sibling)
            else:
                sibling = model.iter_next(selected_iter)
                model.move_after(selected_iter, sibling)

            self.set_value('Actions', self.get_editor_actions(), False)

# Window events
    def on_window_keypress_event(self, widget, event, user_data=None):
        """Handle window keypress events."""
        # Ctrl-F (Find)
        if check_keypress(event, ['Control', 'f']):
            self.search_box.grab_focus()
            return True
        # Ctrl-S (Save)
        if check_keypress(event, ['Control', 's']):
            self.actions['save_launcher'].activate()
            return True
        # Ctrl-Q (Quit)
        if check_keypress(event, ['Control', 'q']):
            self.actions['quit'].activate()
            return True
        return False

    def on_window_delete_event(self, widget, event):
        """Save changes on close."""
        if self.save_button.get_sensitive():
            # Unsaved changes
            dialog = Dialogs.SaveOnCloseDialog(self)
            response = dialog.run()
            dialog.destroy()
            # Cancel prevents the application from closing.
            if response == Gtk.ResponseType.CANCEL:
                return True
            # Don't Save allows the application to close.
            elif response == Gtk.ResponseType.NO:
                return False
            # Save and close.
            else:
                self.save_launcher()
                return False
        return False

# Improved navigation of the Name, Comment, and Icon widgets
    def on_NameCommentIcon_focus_in_event(self, button, event):
        """Make the selected focused widget more noticeable."""
        button.set_relief(Gtk.ReliefStyle.NORMAL)

    def on_NameCommentIcon_focus_out_event(self, button, event):
        """Make the selected focused widget less noticeable."""
        button.set_relief(Gtk.ReliefStyle.NONE)

# Icon Selection
    def on_IconSelectFromIcons_clicked(self, widget, builder):
        current_icon_name = self.get_value("Icon")
        dialog = IconSelectionDialog.IconSelectionDialog(
            parent=self, 
            initial_icon=current_icon_name, 
            use_header_bar=self.use_headerbar)
        if dialog.run() == Gtk.ResponseType.OK:
            icon_name = dialog.get_icon()
            self.set_value('Icon', icon_name)
        dialog.destroy()

    def on_IconSelectFromFilename_clicked(self, widget):
        current_icon_name = self.get_value("Icon")
        dialog = IconFileSelectionDialog.IconFileSelectionDialog(
            parent=self,
            initial_file=current_icon_name,
            use_header_bar=self.use_headerbar)
        if dialog.run() == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            self.set_value('Icon', filename)
        dialog.destroy()

# Name and Comment Widgets
    def on_NameComment_key_press_event(self, widget, ev, widget_name, builder):
        """Handle cancelling the Name/Comment dialogs with Escape."""
        if check_keypress(ev, ['Escape']):
            self.on_NameComment_cancel(widget, widget_name, builder)

    def on_NameComment_activate(self, widget, widget_name, builder):
        """Activate apply button on Enter press."""
        self.on_NameComment_apply(widget, widget_name, builder)

    def on_NameComment_clicked(self, widget, widget_name, builder):
        """Show the Name/Comment editor widgets when the button is clicked."""
        entry = builder.get_object('entry_%s' % widget_name)
        self.values[widget_name] = entry.get_text()
        widget.hide()
        entry.show()
        entry.grab_focus()

    def on_NameComment_cancel(self, widget, widget_name, builder):
        """Hide the Name/Comment editor widgets when canceled."""
        button = builder.get_object('button_%s' % widget_name)
        entry = builder.get_object('entry_%s' % widget_name)
        entry.hide()
        button.show()
        self.history.block()
        entry.set_text(self.values[widget_name])
        self.history.unblock()
        button.grab_focus()

    def on_NameComment_apply(self, *args):
        """Update the Name/Comment fields when the values are to be updated."""
        if len(args) == 5:
            entry, iconpos, void, widget_name, builder = args
        else:
            widget, widget_name, builder = args
            entry = builder.get_object('entry_%s' % widget_name)
        button = builder.get_object('button_%s' % widget_name)
        entry.hide()
        button.show()
        new_value = entry.get_text()
        self.set_value(widget_name, new_value)

# Store entry values when they lose focus.
    def on_entry_focus_out_event(self, widget, event, widget_name):
        """Store the new value in the history when changing fields."""
        text = widget.get_text()
        if "~" in text:
            text = os.path.expanduser(text)
        self.set_value(widget_name, text)

    def on_entry_changed(self, widget, widget_name):
        """Enable saving when an entry has been modified."""
        if not self.history.is_blocked():
            self.actions['save_launcher'].set_sensitive(True)
            self.save_button.set_sensitive(True)

    def on_Exec_clicked(self, entry, icon, event):
        """Show the file selection dialog when Exec/Path Browse is clicked."""
        editor = CommandEditor.CommandEditorDialog(parent=self, initial_text=entry.get_text(), use_header_bar=self.use_headerbar)
        response = editor.run()

        if response == Gtk.ResponseType.OK:
            entry.set_text(editor.get_text())

        editor.destroy()

# Browse button functionality for Exec and Path widgets.
    def on_Path_clicked(self, entry, icon, event, widget_name, builder):
        """Show the file selection dialog when Exec/Path Browse is clicked."""
        if widget_name == 'Path':
            # Translators: File Chooser Dialog, window title.
            title = _("Select a working directory…")
            action = Gtk.FileChooserAction.SELECT_FOLDER
        else:
            # Translators: File Chooser Dialog, window title.
            title = _("Select an executable…")
            action = Gtk.FileChooserAction.OPEN

        dialog = Dialogs.FileChooserDialog(self, title, action)
        result = dialog.run()
        dialog.hide()
        if result == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            if widget_name == 'Exec':
                # Handle spaces to script filenames (lp 1214815)
                if ' ' in filename:
                    filename = '\"%s\"' % filename
            self.set_value(widget_name, filename)
        entry.grab_focus()

    def on_StartupWmClass_clicked(self, entry, icon, event):
        dialog = Dialogs.XpropWindowDialog(self, self.get_value('Name'))
        wm_classes = dialog.run_xprop()
        current = entry.get_text()
        for wm_class in wm_classes:
            if wm_class != current:
                self.set_value("StartupWMClass", wm_class)
                return


# Applications Treeview
    def on_apps_browser_requires_menu_reload(self, widget, required, builder):
        self.menu_restart_infobar.show()


    def on_menu_restart_button_activate(self, widget):
        processes = getProcessList()
        if "mate-panel" in processes:
            cmd = ["mate-panel", "--replace"]
        elif "xfce4-panel" in processes:
            cmd = ["xfce4-panel", "--restart"]
        elif "unity" in processes:
            cmd = ["unity", "--replace"]
        else:
            self.menu_unable_to_restart_dialog()
            return

        self.menu_restart_dialog(cmd)


    def menu_restart_dialog(self, cmd):
        user_cmd = " ".join(cmd)

        primary = _("Menu restart required")
        secondary = _("MenuLibre can do this automatically. "
                      "Do you want to run the following command?\n\n%s") % user_cmd

        dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.ERROR,
                                    Gtk.ButtonsType.YES_NO, primary)
        dialog.format_secondary_markup(secondary)
        response = dialog.run()
        if response == Gtk.ResponseType.YES:
            subprocess.Popen(cmd)
        self.menu_restart_infobar.hide()
        dialog.destroy()


    def menu_unable_to_restart_dialog(self):
        primary = _("Menu restart required")
        secondary = _("However, MenuLibre cannot determine how to do this "
                      "automatically on your system. "
                      "Please log out for you menu to update completely.")

        dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.ERROR,
                                    Gtk.ButtonsType.CLOSE, primary)
        dialog.format_secondary_markup(secondary)
        dialog.run()
        self.menu_restart_infobar.hide()
        dialog.destroy()


    def on_apps_browser_add_directory_enabled(self, widget, enabled, builder):
        """Update the Add Directory menu item when the selected row is
        changed."""
        # Always allow creating sub directories
        enabled = True

        self.actions['add_directory'].set_sensitive(enabled)
        for widget in self.action_items['add_directory']:
            widget.set_sensitive(enabled)
            widget.set_tooltip_text(None)

    def on_apps_browser_cursor_changed(self, widget, value, builder):  # noqa
        """Update the editor frame when the selected row is changed."""
        missing = False

        # Clear history
        self.history.clear()

        # Hide the Name and Comment editors
        builder.get_object('entry_Name').hide()
        builder.get_object('entry_Comment').hide()

        # Prevent updates to history.
        self.history.block()

        # Clear the individual entries.
        for key in ['Exec', 'Path', 'Terminal', 'StartupNotify',
                    'NoDisplay', 'GenericName', 'TryExec',
                    'OnlyShowIn', 'NotShowIn', 'MimeType',
                    'Keywords', 'StartupWMClass', 'Implements', 'Categories',
                    'Hidden', 'DBusActivatable', 'PrefersNonDefaultGPU',
                    'X-GNOME-UsesNotifications']:
                    self.set_value(key, None)

        # Clear the Actions and Icon.
        self.set_value('Actions', None, store=True)
        self.set_value('Icon', None, store=True)

        model, row_data = self.treeview.get_selected_row_data()
        item_type = row_data[MenuEditor.COL_TYPE]

        # If the selected row is a separator, hide the editor.
        if item_type == MenuItemTypes.SEPARATOR:
            self.editor.hide()
            # Translators: Separator menu item
            self.set_value('Name', _("Separator"), store=True)
            self.set_value('Comment', "", store=True)
            self.set_value('Filename', None, store=True)
            self.set_value('Type', 'Separator', store=True)

        # Otherwise, show the editor and update the values.
        else:
            filename = self.treeview.get_selected_filename()
            new_launcher = filename is None

            # Check if this file still exists
            if (not new_launcher) and (not os.path.isfile(filename)):
                # If it does not, try to fallback...
                basename = getRelativeName(filename)
                filename = util.getSystemLauncherPath(basename)
                if filename is not None:
                    row_data[MenuEditor.COL_FILENAME] = filename
                    self.treeview.update_launcher_instances(filename, row_data)

            if new_launcher or (filename is not None):
                self.editor.show()
                displayed_name = row_data[MenuEditor.COL_NAME]
                comment = row_data[MenuEditor.COL_COMMENT]

                self.set_value('Icon', row_data[MenuEditor.COL_ICON_NAME], store=True)
                self.set_value('Name', displayed_name, store=True)
                self.set_value('Comment', comment, store=True)
                self.set_value('Filename', filename, store=True)

                if item_type == MenuItemTypes.APPLICATION:
                    self.editor.show_all()
                    entry = MenulibreXdg.MenulibreDesktopEntry(filename)
                    for key in getRelatedKeys(item_type, key_only=True):
                        if key in ['Actions', 'Comment', 'Filename', 'Icon',
                                   'Name']:
                            continue
                        self.set_value(key, entry[key], store=True)
                    self.set_value('Actions', entry.get_actions(),
                                   store=True)
                    self.set_value('Type', 'Application')
                    self.execute_button.set_sensitive(True)
                else:
                    entry = MenulibreXdg.MenulibreDesktopEntry(filename)
                    for key in getRelatedKeys(item_type, key_only=True):
                        if key in ['Comment', 'Filename', 'Icon', 'Name']:
                            continue
                        self.set_value(key, entry[key], store=True)
                    self.set_value('Type', 'Directory')
                    for widget in self.directory_hide_widgets:
                        widget.hide()
                    self.execute_button.set_sensitive(False)

            else:
                # Display a dialog saying this item is missing
                dialog = Dialogs.LauncherRemovedDialog(self)
                dialog.run()
                dialog.destroy()
                # Mark this item as missing to delete it later.
                missing = True

        # Re-enable updates to history.
        self.history.unblock()

        if self.treeview.get_parent()[1] is None:
            self.treeview.set_sortable(False)
            move_up_enabled = not self.treeview.is_first()
            move_down_enabled = not self.treeview.is_last()
        else:
            self.treeview.set_sortable(True)
            if item_type == MenuItemTypes.APPLICATION or \
                    item_type == MenuItemTypes.LINK or \
                    item_type == MenuItemTypes.SEPARATOR:
                move_up_enabled = True
                move_down_enabled = True
            else:
                move_up_enabled = not self.treeview.is_first()
                move_down_enabled = not self.treeview.is_last()

        self.treeview.set_move_up_enabled(move_up_enabled)
        self.treeview.set_move_down_enabled(move_down_enabled)

        # Remove this item if it happens to be gone.
        if missing:
            self.delete_launcher()

    def on_app_search_changed(self, widget, treeview, expand=False):
        """Update search results when query text is modified."""
        query = widget.get_text()

        # If blank query...
        if len(query) == 0:
            # Remove the clear button.
            widget.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY,
                                           None)

            # If the model is a filter, we want to remove the filter.
            self.treeview.set_searchable(False, expand)

            # Enable add functionality
            for name in ['add_launcher', 'add_directory', 'add_separator',
                         'add_button']:
                for widget in self.action_items[name]:
                    widget.set_sensitive(True)
                if name in self.actions:
                    self.actions[name].set_sensitive(True)

            # Enable deletion (LP: #1751616)
            self.delete_button.set_sensitive(True)
            self.delete_button.set_tooltip_text("")

        # If the entry has a query...
        else:
            # Show the clear button.
            widget.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY,
                                           'edit-clear-symbolic')

            self.treeview.set_searchable(True)

            # Disable add functionality
            for name in ['add_launcher', 'add_directory', 'add_separator',
                         'add_button']:
                for widget in self.action_items[name]:
                    widget.set_sensitive(False)
                if name in self.actions:
                    self.actions[name].set_sensitive(False)

            # Rerun the filter.
            self.treeview.search(self.search_box.get_text())

            # Disable deletion (LP: #1751616)
            self.delete_button.set_sensitive(False)
            self.delete_button.set_tooltip_text("")

    def on_search_cleared(self, widget, event, user_data=None):
        """Generic search cleared callback function."""
        widget.set_text("")

# Setters and Getters
    def set_editor_image_success(self, button, image, text):
        button.set_tooltip_text(text)
        image.set_opacity(1.0)
        self.overlay_icon.hide()


    def set_editor_image_error(self, button, image, markup):
        button.set_tooltip_markup(markup)
        image.set_opacity(0.7)
        self.overlay_icon.show()


    def set_editor_image(self, icon_name):
        """Set the editor Icon button image."""
        button, image = self.widgets['Icon']

        # Load the Icon Theme.
        icon_theme = Gtk.IconTheme.get_default()

        if icon_name is not None:
            # If the Icon Theme has the icon, set the image to that icon.
            if icon_theme.has_icon(icon_name):
                image.set_from_icon_name(icon_name, 48)
                self.set_editor_image_success(button, image, icon_name)
                return

            # If the Icon Theme has a symbolic version of the icon, set the image to that icon.
            if icon_theme.has_icon(icon_name + "-symbolic"):
                icon_name = icon_name + "-symbolic"
                image.set_from_icon_name(icon_name, 48)
                self.set_editor_image_success(button, image, icon_name)
                return

            # If the icon name is actually a file, render it to the Image.
            elif os.path.isfile(icon_name):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_name)
                size = image.get_preferred_height()[1]
                scaled = pixbuf.scale_simple(size, size,
                                             GdkPixbuf.InterpType.HYPER)
                image.set_from_pixbuf(scaled)
                self.set_editor_image_success(button, image, icon_name)
                return
            
            else:
                self.set_editor_image_error(button, image, _("<i>Missing icon:</i> %s") % icon_name)

                if icon_name.startswith("applications-"):
                    icon_name = "folder"
                else:
                    icon_name = "application-x-executable"

                image.set_from_icon_name(icon_name, 48)
                return

        if icon_theme.has_icon("applications-other"):
            image.set_from_icon_name("applications-other", 48)
            return

        image.set_from_icon_name("application-x-executable", 48)

    def set_editor_filename(self, filename):
        """Set the editor filename."""
        # Since the filename has changed, check if it is now writable...
        if filename is None or os.access(filename, os.W_OK):
            self.delete_button.set_sensitive(True)
            self.delete_button.set_tooltip_text("")
        else:
            self.delete_button.set_sensitive(False)
            self.delete_button.set_tooltip_text(
                # Translators: This error is displayed when the user does not
                # have sufficient file system permissions to delete the
                # selected file.
                _("You do not have permission to delete this file."))

        # Disable deletion if we're in search mode (LP: #1751616)
        if self.search_box.get_text() != "":
            self.delete_button.set_sensitive(False)
            self.delete_button.set_tooltip_text("")

        # If the filename is None, make it blank.
        if filename is None:
            filename = ""

        # Get the filename widget.
        widget = self.widgets['Filename']

        # Set the label and tooltip.
        widget.set_label(filename)
        widget.set_tooltip_text(filename)

        # Store the filename value.
        self.values['filename'] = filename

    def get_editor_categories(self):
        """Get the editor categories.

        Return the categories as a semicolon-delimited string."""
        model = self.categories_treeview.get_model()
        categories = ""
        for row in model:
            categories = "%s%s;" % (categories, row[0])
        return categories

    def set_editor_categories(self, entries_string):
        """Populate the Categories treeview with the Categories string."""
        if not entries_string:
            entries_string = ""

        # Split the entries into a list.
        entries = entries_string.split(';')
        entries.sort()

        # Clear the model.
        model = self.categories_treeview.get_model()
        model.clear()

        # Clear tracked categories user explicitly deleted
        self.categories_removed = set()

        # Clear the ThisEntry category list.
        this_index = self.categories_treestore.iter_n_children(None) - 1
        this_entry = self.categories_treestore.iter_nth_child(None, this_index)
        for i in range(self.categories_treestore.iter_n_children(this_entry)):
            child_iter = self.categories_treestore.iter_nth_child(this_entry,
                                                                  0)
            self.categories_treestore.remove(child_iter)

        # Cleanup the entry text and generate a description.
        for entry in entries:
            entry = entry.strip()
            if len(entry) > 0:
                description = lookup_category_description(entry)
                model.append([entry, description])

                # Add unknown entries to the category list...
                category_keys = list(category_groups.keys()) + \
                    list(category_lookup.keys())
                if entry not in category_keys:
                    self.categories_treestore.append(this_entry, [entry])

        self.categories_treefilter.refilter()

    def get_editor_actions_string(self):
        """Return the .desktop formatted actions."""
        # Get the model.
        model = self.actions_treeview.get_model()

        # Start the output string.
        actions = "\nActions="
        groups = "\n"

        # Return None if there are no actions.
        if len(model) == 0:
            return None

        # For each row...
        for row in model:
            # Extract the details.
            show, name, displayed, executable = row[:]

            # Append it to the actions list if it is selected to be shown.
            if show:
                actions = "%s%s;" % (actions, name)

            # Populate the group text.
            group = "[Desktop Action %s]\n" \
                    "Name=%s\n" \
                    "Exec=%s\n" \
                    "OnlyShowIn=Unity\n" % (name, displayed, executable)

            # Append the new group text to the groups string.
            groups = "%s\n%s" % (groups, group)

        # Return the .desktop formatted actions.
        return actions + groups

    def get_editor_actions(self):
        """Get the list of action groups."""
        model = self.actions_treeview.get_model()

        action_groups = []

        # Return [] if there are no actions.
        if len(model) == 0:
            return []

        # For each row...
        for row in model:
            # Extract the details.
            show, name, displayed, command = row[:]
            action_groups.append([name, displayed, command, show])

        return action_groups

    def set_editor_actions(self, action_groups):
        """Set the editor Actions from the list action_groups."""
        model = self.actions_treeview.get_model()
        model.clear()
        if not action_groups:
            return
        for name, displayed, command, show in action_groups:
            model.append([show, name, displayed, command])

    def get_inner_value(self, key):
        """Get the value stored for key."""
        try:
            return self.values[key]
        except:  # noqa
            return None

    def set_inner_value(self, key, value):
        """Set the value stored for key."""
        self.values[key] = value

    """
    Quoting must be done by enclosing the argument between double quotes and escaping
    the double quote character, backtick character ("`"), dollar sign ("$") and
    backslash character ("\") by preceding it with an additional backslash character.
    Implementations must undo quoting before expanding field codes and before passing
    the argument to the executable program. Reserved characters are space (" "),
    tab, newline, double quote, single quote ("'"), backslash character ("\"),
    greater-than sign (">"), less-than sign ("<"), tilde ("~"), vertical bar ("|"),
    ampersand ("&"), semicolon (";"), dollar sign ("$"), asterisk ("*"),
    question mark ("?"), hash mark ("#"), parenthesis ("(") and (")") and backtick
    character ("`").

    Note that the general escape rule for values of type string states that the backslash
    character can be escaped as ("\\") as well and that this escape rule is applied before
    the quoting rule. As such, to unambiguously represent a literal backslash character in
    a quoted argument in a desktop entry file requires the use of four successive backslash
    characters ("\\\\"). Likewise, a literal dollar sign in a quoted argument in a desktop
    entry file is unambiguously represented with ("\\$").

    A number of special field codes have been defined which will be expanded by the file
    manager or program launcher when encountered in the command line. Field codes consist
    of the percentage character ("%") followed by an alpha character. Literal percentage
    characters must be escaped as %%. Deprecated field codes should be removed from the
    command line and ignored. Field codes are expanded only once, the string that is used
    to replace the field code should not be checked for field codes itself.

    Field codes must not be used inside a quoted argument, the result of field code expansion
    inside a quoted argument is undefined. The %F and %U field codes may only be used as an
    argument on their own.
    """

    def escape_exec(self, value):
        value = str(value)
        args = []
        for arg in shlex.split(value, posix=False):
            if arg.startswith("\""):
                arg = arg.replace("%%", "%")  # Make it consistent for the pros
                arg = arg.replace("%", "%%")
            args.append(arg)
        return " ".join(args)

    def unescape_exec(self, value):
        value = str(value)
        args = []
        for arg in shlex.split(value, posix=False):
            if arg.startswith("\""):
                arg = arg.replace("%%", "%")
            args.append(arg)
        return " ".join(args)

    def set_value(self, key, value, adjust_widget=True, store=False):  # noqa
        """Set the DesktopSpec key, value pair in the editor."""
        if store:
            self.history.store(key, value)
        if self.get_inner_value(key) == value:
            return
        self.history.append(key, self.get_inner_value(key), value)
        self.set_inner_value(key, value)
        if not adjust_widget:
            return
        # Name and Comment must formatted correctly for their buttons.
        if key in ['Name', 'Comment']:
            if not value:
                value = ""
            button, label, entry = self.widgets[key]
            if key == 'Name':
                markup = escapeText(value)
            else:
                markup = "%s" % (value)
            tooltip = escapeText(value)

            button.set_tooltip_markup(tooltip)
            entry.set_text(value)
            label.set_markup(markup)

        # Filename, Actions, Categories, and Icon have their own functions.
        elif key == 'Filename':
            self.set_editor_filename(value)
        elif key == 'Actions':
            self.set_editor_actions(value)
        elif key == 'Categories':
            self.set_editor_categories(value)
        elif key == 'Icon':
            self.set_editor_image(value)

        # Type is just stored.
        elif key == 'Type':
            self.values['Type'] = value

        # No associated widget for Version
        elif key == 'Version':
            pass

        elif key == 'Exec':
            widget = self.widgets[key]
            widget.set_text(self.unescape_exec(value))

        # Everything else is set by its widget type.
        elif key in self.widgets.keys():
            widget = self.widgets[key]
            # GtkButton
            if isinstance(widget, Gtk.Button):
                if not value:
                    value = ""
                widget.set_label(value)
            # GtkLabel
            elif isinstance(widget, Gtk.Label):
                if not value:
                    value = ""
                widget.set_label(str(value))
            # GtkEntry
            elif isinstance(widget, Gtk.Entry):
                if not value:
                    value = ""
                widget.set_text(str(value))
            # GtkSwitch
            elif isinstance(widget, Gtk.Switch):
                if not value:
                    value = False
                widget.set_active(value)
                # If "Hide from menus", also clear Hidden setting.
                if key == 'NoDisplay' and value is False:
                    self.set_value('Hidden', False)
            else:
                logger.warning(("Unknown widget: %s" % key))
        else:
            logger.warning(("Unimplemented widget: %s" % key))

    def get_value(self, key):  # noqa
        """Return the value stored for the specified key."""
        if key in ['Name', 'Comment']:
            button, label, entry = self.widgets[key]
            return entry.get_text()
        elif key == 'Icon':
            return self.values[key]
        elif key == 'Type':
            return self.values[key]
        elif key == 'Categories':
            return self.get_editor_categories()
        elif key == 'Filename':
            if 'filename' in list(self.values.keys()):
                return self.values['filename']
        elif key == 'Exec':
            widget = self.widgets[key]
            value = widget.get_text()
            return self.escape_exec(value)
        else:
            widget = self.widgets[key]
            if isinstance(widget, Gtk.Button):
                return widget.get_label()
            elif isinstance(widget, Gtk.Label):
                return widget.get_label()
            elif isinstance(widget, Gtk.Entry):
                return widget.get_text()
            elif isinstance(widget, Gtk.Switch):
                return widget.get_active()
            else:
                return None
        return None

# Action Functions
    def add_launcher(self):
        """Add Launcher callback function."""
        # Translators: Placeholder text for a newly created launcher.
        name = _("New Launcher")
        # Translators: Placeholder text for a newly created launcher's
        # description.
        comment = _("A small descriptive blurb about this application.")
        categories = ""
        item_type = MenuItemTypes.APPLICATION
        icon_name = "application-x-executable"
        icon = Gio.ThemedIcon.new(icon_name)
        filename = None
        executable = ""
        new_row_data = [name, comment, executable, categories, item_type, icon,
                        icon_name, filename, True]

        model, parent_data = self.treeview.get_parent_row_data()
        model, row_data = self.treeview.get_selected_row_data()

        # Exit early if no row is selected (LP #1556664)
        if not row_data:
            return

        # Add to the treeview on the current level or as a child of a selected
        # directory
        dir_selected = row_data[MenuEditor.COL_TYPE] == MenuItemTypes.DIRECTORY
        if dir_selected:
            self.treeview.add_child(new_row_data)
        else:
            self.treeview.append(new_row_data)

        # A parent item has been found, and the current selection is not a
        # directory, so the resulting item will be placed at the current level
        # fetch the parent's categories
        if parent_data is not None and not dir_selected:
            categories = util.getRequiredCategories(parent_data[MenuEditor.COL_FILENAME])

        elif parent_data is not None and dir_selected:

            # A directory lower than the top-level has been selected - the
            # launcher will be added into it (e.g. as the first item),
            # therefore it essentially has a parent of the current selection
            categories = util.getRequiredCategories(row_data[MenuEditor.COL_FILENAME])

        else:

            # Parent was not found, this is a toplevel category
            categories = util.getRequiredCategories(None)

        self.set_editor_categories(';'.join(categories))

        self.actions['save_launcher'].set_sensitive(True)
        self.save_button.set_sensitive(True)

    def add_directory(self):
        """Add Directory callback function."""
        # Translators: Placeholder text for a newly created directory.
        name = _("New Directory")
        # Translators: Placeholder text for a newly created directory's
        # description.
        comment = _("A small descriptive blurb about this directory.")
        categories = ""
        item_type = MenuItemTypes.DIRECTORY
        icon_name = "folder"
        icon = Gio.ThemedIcon.new(icon_name)
        filename = None
        executable = ""
        row_data = [name, comment, executable, categories, item_type, icon,
                    icon_name, filename, True, True]

        self.treeview.append(row_data)

        self.actions['save_launcher'].set_sensitive(True)
        self.save_button.set_sensitive(True)

    def add_separator(self):
        """Add Separator callback function."""
        name = "<s>                    </s>"
        # Translators: Separator menu item
        tooltip = _("Separator")
        categories = ""
        filename = None
        icon = None
        icon_name = ""
        item_type = MenuItemTypes.SEPARATOR
        filename = None
        executable = ""
        row_data = [name, tooltip, executable, categories, item_type, icon,
                    icon_name, filename, False, True]

        self.treeview.append(row_data)

        self.save_button.set_sensitive(False)

        self.treeview.update_menus()

    def list_str_to_list(self, value):
        if isinstance(value, list):
            return value
        values = []
        for value in value.replace(",", ";").split(";"):
            value = value.strip()
            if len(value) > 0:
                values.append(value)
        return values

    def write_launcher(self, filename):  # noqa
        keyfile = GLib.KeyFile.new()

        for key, ktype, required in getRelatedKeys(self.get_value("Type")):
            if key == "Version":
                keyfile.set_string("Desktop Entry", "Version", "1.1")
                continue

            if key == "Actions":
                action_list = []
                for name, displayed, command, show in \
                        self.get_editor_actions():
                    group_name = "Desktop Action %s" % name
                    keyfile.set_string(group_name, "Name", displayed)
                    keyfile.set_string(group_name, "Exec", command)
                    if show:
                        action_list.append(name)
                keyfile.set_string_list("Desktop Entry", key, action_list)
                continue

            value = self.get_value(key)
            if ktype == str:
                if len(value) > 0:
                    keyfile.set_string("Desktop Entry", key, value)
            if ktype == float:
                if value != 0:
                    keyfile.set_double("Desktop Entry", key, value)
            if ktype == bool:
                if value is not False:
                    keyfile.set_boolean("Desktop Entry", key, value)
            if ktype == list:
                value = self.list_str_to_list(value)
                if len(value) > 0:
                    keyfile.set_string_list("Desktop Entry", key, value)

        try:
            if not keyfile.save_to_file(filename):
                return False
        except GLib.Error:
            return False

        return True

    def save_launcher(self, temp=False):  # noqa
        """Save the current launcher details, remove from the current directory
        if it no longer has the required category."""

        if temp:
            filename = tempfile.mkstemp('.desktop', 'menulibre-')[1]
        else:
            # Get the filename to be used.
            original_filename = self.get_value('Filename')
            item_type = self.get_value('Type')
            name = self.get_value('Name')
            filename = util.getSaveFilename(name, original_filename, item_type)
        logger.debug("Saving launcher as \"%s\"" % filename)

        if not temp:
            model, row_data = self.treeview.get_selected_row_data()
            item_type = row_data[MenuEditor.COL_TYPE]

            model, parent_data = self.treeview.get_parent_row_data()

            # Make sure required categories are in place - this is useful for
            # when a user moves a launcher from its original location to a new
            # directory - without the category associated with the new
            # directory (and no force-include), the launcher would not
            # otherwise show
            if parent_data is not None:
                # Parent was found, take its categories.
                required_categories = util.getRequiredCategories(
                    parent_data[MenuEditor.COL_FILENAME])
            else:
                # Parent was not found, this is a toplevel category
                required_categories = util.getRequiredCategories(None)
            current_categories = self.get_value('Categories').split(';')
            all_categories = current_categories
            for category in required_categories:

                # Only add the 'required category' if the user has not
                # explicitly removed it
                if (category not in all_categories and
                        category not in self.categories_removed):
                    all_categories.append(category)

            self.set_editor_categories(';'.join(all_categories))

            # Cleanup invalid entries and reorder the Categories and Actions
            self.cleanup_categories()
            self.cleanup_actions()

        if not self.write_launcher(filename):
            dlg = Dialogs.SaveErrorDialog(self, filename)
            dlg.run()
            return

        if temp:
            return filename

        # Install the new item in its directory...
        self.treeview.xdg_menu_install(filename)

        # Set the editor to the new filename.
        self.set_value('Filename', filename)

        # Update the selected iter with the new details.
        name = self.get_value('Name')
        comment = self.get_value('Comment')
        executable = self.get_value('Exec')
        categories = self.get_value('Categories')
        icon_name = self.get_value('Icon')
        hidden = self.get_value('Hidden') or self.get_value('NoDisplay')
        self.treeview.update_selected(name, comment, executable, categories,
                                      item_type, icon_name, filename, not hidden)
        self.history.clear()

        # Update all instances
        model, row_data = self.treeview.get_selected_row_data()
        self.treeview.update_launcher_instances(original_filename, row_data)

        self.treeview.update_menus()

        # Check and make sure that the launcher has been added to/removed from
        # directories that its category configuration dictates - this is not
        # deleting the launcher but removing it from various places in the UI
        self.update_launcher_category_dirs()

        if filename.endswith(".directory"):
            processes = getProcessList()
            if "mate-panel" in processes:
                self.menu_restart_infobar.show()


    def update_launcher_categories(self, remove, add):  # noqa
        original_filename = self.get_value('Filename')
        if original_filename is None or not os.path.isfile(original_filename):
            return
        item_type = self.get_value('Type')
        name = self.get_value('Name')
        save_filename = util.getSaveFilename(name, original_filename,
                                             item_type, force_update=True)
        logger.debug("Saving launcher as \"%s\"" % save_filename)

        # Get the original contents
        keyfile = GLib.KeyFile.new()
        keyfile.load_from_file(original_filename, GLib.KeyFileFlags.NONE)

        try:
            categories = keyfile.get_string_list("Desktop Entry", "Categories")
        except GLib.Error:
            categories = None

        if categories is None:
            categories = []

        # Remove the old required categories
        for category in remove:
            if category in categories:
                categories.remove(category)

        # Add the new required categories
        for category in add:
            if category not in categories:
                categories.append(category)

        # Remove empty categories
        for category in categories:
            if category.strip() == "":
                try:
                    categories.remove(category)
                except: # noqa
                    pass

        categories.sort()

        # Commit the changes to a new file
        keyfile.set_string_list("Desktop Entry", "Categories", categories)
        keyfile.save_to_file(save_filename)

        # Set the editor to the new filename.
        self.set_editor_filename(save_filename)

        # Update all instances
        model, row_data = self.treeview.get_selected_row_data()
        row_data[MenuEditor.COL_CATEGORIES] = ';'.join(categories)
        row_data[MenuEditor.COL_FILENAME] = save_filename
        self.treeview.update_launcher_instances(original_filename, row_data)

    def update_launcher_category_dirs(self):  # noqa
        """Make sure launcher is present or absent from in all top-level
        directories that its categories dictate."""

        # Prior to menulibre being restarted, addition of a category does not
        # result in the launcher being added to or removed from the relevant
        # top-level directories - making sure this happens

        # Fetching model and launcher information - removing empty category
        # at end of category split
        # Note that a user can remove all categories now if they want, which
        # would naturally remove the launcher from all top-level directories -
        # alacarte doesn't save any categories by default with a new launcher,
        # however to reach this point, any required categories (minus those the
        # user has explicitly deleted) will be added, so this shouldn't be a
        # problem
        model, row_data = self.treeview.get_selected_row_data()
        if row_data[MenuEditor.COL_CATEGORIES]:
            categories = row_data[MenuEditor.COL_CATEGORIES].split(';')[:-1]
        else:
            categories = []
        filename = row_data[MenuEditor.COL_FILENAME]

        required_category_directories = set()

        # Obtaining a dictionary of iters to launcher instances in top-level
        # directories
        launcher_instances = self.treeview._get_launcher_instances(filename)
        launchers_in_top_level_dirs = {}
        for instance in launcher_instances:

            # Make sure the launcher isn't top-level and is in a directory.
            # Must pass a model otherwise it gets the current selection iter
            # regardless...
            _, parent = self.treeview.get_parent(model, instance)
            if (parent is not None and
                    model[parent][MenuEditor.COL_TYPE] == MenuItemTypes.DIRECTORY):

                # Any direct parents are required directories.
                required_category_directories.add(model[parent][MenuEditor.COL_NAME])

                # Adding if the directory returned is top level
                _, parent_parent = self.treeview.get_parent(model, parent)
                if parent_parent is None:
                    launchers_in_top_level_dirs[model[parent][MenuEditor.COL_NAME]] = instance

        # Obtaining a lookup of top-level directories -> iters
        top_level_dirs = {}
        for row in model:
            if row[MenuEditor.COL_TYPE] == MenuItemTypes.DIRECTORY:
                top_level_dirs[row[MenuEditor.COL_NAME]] = model.get_iter(row.path)

        # Looping through all set categories - category specified is at maximum
        # detail level, this needs to be converted to the parent group name,
        # and this needs to be converted into the directory name as it would
        # appear in the menu
        for category in categories:
            if category not in category_lookup.keys():
                continue

            category_group = category_lookup[category]
            directory_name = util.getDirectoryNameFromCategory(category_group)

            # Adding to directories the launcher should be in
            if directory_name not in launchers_in_top_level_dirs:
                if directory_name in top_level_dirs.keys():
                    treeiter = self.treeview.add_child(
                        row_data, top_level_dirs[directory_name], model, False)
                    launchers_in_top_level_dirs[directory_name] = treeiter

            # Building set of required category directories to detect
            # superfluous ones later
            if directory_name not in required_category_directories:
                required_category_directories.add(directory_name)

        # Removing launcher from directories it should no longer be in
        superfluous_dirs = (set(launchers_in_top_level_dirs.keys())
                            - required_category_directories)
        _, parent_data = self.treeview.get_parent_row_data()

        for directory_name in superfluous_dirs:

            # Removing selected launcher from the UI if it is in the current
            # directory, otherwise just from the model
            if parent_data is not None and directory_name == parent_data[MenuEditor.COL_NAME]:
                self.treeview.remove_selected(True)

            else:
                self.treeview.remove_iter(
                    model, launchers_in_top_level_dirs[directory_name])

    def delete_separator(self):
        """Remove a separator row from the treeview, update the menu files."""
        self.treeview.remove_selected()

    def delete_launcher(self):
        """Delete the selected launcher."""
        self.treeview.remove_selected()
        self.history.clear()

    def restore_launcher(self):
        """Revert the current launcher."""
        values = self.history.restore()

        # Clear the history
        self.history.clear()

        # Block updates
        self.history.block()

        for key in list(values.keys()):
            self.set_value(key, values[key], store=True)

        # Unblock updates
        self.history.unblock()

# Callbacks
    def on_add_launcher_cb(self, widget):
        """Add Launcher callback function."""
        self.add_launcher()

    def on_add_directory_cb(self, widget):
        """Add Directory callback function."""
        self.add_directory()

    def on_add_separator_cb(self, widget):
        """Add Separator callback function."""
        self.add_separator()

    def on_save_launcher_cb(self, widget, builder):
        """Save Launcher callback function."""
        self.on_NameComment_apply(None, 'Name', builder)
        self.on_NameComment_apply(None, 'Comment', builder)
        self.save_launcher()

    def on_undo_cb(self, widget):
        """Undo callback function."""
        key, value = self.history.undo()
        self.history.block()
        self.set_value(key, value)
        self.history.unblock()

    def on_redo_cb(self, widget):
        """Redo callback function."""
        key, value = self.history.redo()
        self.history.block()
        self.set_value(key, value)
        self.history.unblock()

    def on_revert_cb(self, widget):
        """Revert callback function."""
        dialog = Dialogs.RevertDialog(self)
        if dialog.run() == Gtk.ResponseType.OK:
            self.restore_launcher()
        dialog.destroy()

    def find_in_path(self, command):
        if os.path.exists(os.path.abspath(command)):
            return os.path.abspath(command)
        for path in os.environ["PATH"].split(os.pathsep):
            if os.path.exists(os.path.join(path, command)):
                return os.path.join(path, command)
        return False

    def find_command_in_string(self, command):
        for piece in shlex.split(command):
            if "=" not in piece:
                return piece
        return False

    def on_execute_cb(self, widget, builder):
        """Execute callback function."""
        self.on_NameComment_apply(None, 'Name', builder)
        self.on_NameComment_apply(None, 'Comment', builder)
        filename = self.save_launcher(True)

        entry = MenulibreXdg.MenulibreDesktopEntry(filename)
        command = self.find_command_in_string(entry["Exec"])

        if self.find_in_path(command):
            subprocess.Popen(["xdg-open", filename])
            GObject.timeout_add(2000, self.on_execute_timeout, filename)
        else:
            os.remove(filename)
            dlg = Dialogs.NotFoundInPathDialog(self, command)
            dlg.run()

    def on_execute_timeout(self, filename):
        os.remove(filename)

    def on_delete_cb(self, widget):
        """Delete callback function."""
        model, row_data = self.treeview.get_selected_row_data()
        name = row_data[MenuEditor.COL_NAME]
        item_type = row_data[MenuEditor.COL_TYPE]

        # Prepare the strings
        if item_type == MenuItemTypes.SEPARATOR:
            # Translators: Confirmation dialog to delete the selected
            # separator.
            question = _("Are you sure you want to delete this separator?")
            delete_func = self.delete_separator
        else:
            # Translators: Confirmation dialog to delete the selected launcher.
            question = _("Are you sure you want to delete \"%s\"?") % name
            delete_func = self.delete_launcher

        dialog = Dialogs.DeleteDialog(self, question)

        # Run
        if dialog.run() == Gtk.ResponseType.OK:
            delete_func()

        dialog.destroy()

    def on_quit_cb(self, widget):
        """Quit callback function.  Send the quit signal to the parent
        GtkApplication instance."""
        self.emit('quit', True)

    def on_help_cb(self, widget):
        """Help callback function.  Send the help signal to the parent
        GtkApplication instance."""
        self.emit('help', True)

    def on_about_cb(self, widget):
        """About callback function.  Send the about signal to the parent
        GtkApplication instance."""
        self.emit('about', True)

    def on_bad_desktop_files_infobar_response(self, infobar, response_id):
        """Bad desktop files infobar callback function to request the bad
        desktop files report if desired."""

        # Dealing with request for details
        if response_id == Gtk.ResponseType.YES:
            self.bad_desktop_files_report_dialog()

        # All response types should result in the infobar being hidden
        infobar.hide()

    def bad_desktop_files_report_dialog(self):
        """Generate and display details of bad desktop files, or report
        successful parsing."""

        log_dialog = MenulibreLog.LogDialog(self)

        # Building up a list of all known failures associated with the bad
        # desktop files
        for desktop_file in self.bad_desktop_files:
            log_dialog.add_item(desktop_file,
                                util.validate_desktop_file(desktop_file))

        log_dialog.show()


class Application(Gtk.Application):
    """Menulibre GtkApplication"""

    def __init__(self):
        """Initialize the GtkApplication."""
        Gtk.Application.__init__(self)
        self.use_headerbar = False
        self.use_toolbar = False

        self.settings_file = os.path.expanduser("~/.config/menulibre.cfg")

    def set_use_headerbar(self, preference):
        try:
            settings = GLib.KeyFile.new()
            settings.set_boolean("menulibre", "UseHeaderbar", preference)
            settings.save_to_file(self.settings_file)
        except: # noqa
            pass

    def get_use_headerbar(self):
        if not os.path.exists(self.settings_file):
            return None
        try:
            settings = GLib.KeyFile.new()
            settings.load_from_file(self.settings_file, GLib.KeyFileFlags.NONE)
            return settings.get_boolean("menulibre", "UseHeaderbar")
        except: # noqa
            return None

    def do_activate(self):
        """Handle GtkApplication do_activate."""
        if self.use_toolbar:
            headerbar = False
            self.set_use_headerbar(False)
        elif self.use_headerbar:
            headerbar = True
            self.set_use_headerbar(True)
        elif self.get_use_headerbar() is not None:
            headerbar = self.get_use_headerbar()
        elif current_desktop in ["budgie", "gnome", "pantheon"]:
            headerbar = True
        else:
            headerbar = False

        self.win = MenulibreWindow(self, headerbar)
        self.win.show()

        self.win.connect('about', self.about_cb)
        self.win.connect('help', self.help_cb)
        self.win.connect('quit', self.quit_cb)

    def do_startup(self):
        """Handle GtkApplication do_startup."""
        Gtk.Application.do_startup(self)

        # 'Sections' without labels result in a separator separating functional
        # groups of menu items
        self.menu = Gio.Menu()
        section_1_menu = Gio.Menu()
        # Translators: Menu item to open the Parsing Errors dialog.
        section_1_menu.append(_("Parsing Error Log"),
                              "app.bad_files")
        self.menu.append_section(None, section_1_menu)

        section_2_menu = Gio.Menu()
        section_2_menu.append(_("Help"), "app.help")
        section_2_menu.append(_("About"), "app.about")
        section_2_menu.append(_("Quit"), "app.quit")
        self.menu.append_section(None, section_2_menu)

        self.set_app_menu(self.menu)

        # Bad desktop files detection on demand
        bad_files_action = Gio.SimpleAction.new("bad_files", None)
        bad_files_action.connect("activate", self.bad_files_cb)
        self.add_action(bad_files_action)

        help_action = Gio.SimpleAction.new("help", None)
        help_action.connect("activate", self.help_cb)
        self.add_action(help_action)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.about_cb)
        self.add_action(about_action)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.quit_cb)
        self.add_action(quit_action)

    def bad_files_cb(self, widget, data=None):
        """Bad desktop files detection callback function."""

        # Determining paths of bad desktop files GMenu can't load, on demand
        # This state is normally tracked with the MenulibreWindow, so not
        # keeping it in this application object. By the time this is called,
        # self.win is valid
        self.win.bad_desktop_files = util.determine_bad_desktop_files()
        self.win.bad_desktop_files_report_dialog()

    def help_cb(self, widget, data=None):
        """Help callback function."""
        Dialogs.HelpDialog(self.win)

    def about_cb(self, widget, data=None):
        """About callback function.  Display the AboutDialog."""
        dialog = Dialogs.AboutDialog(self.win)
        dialog.show()

    def quit_cb(self, widget, data=None):
        """Signal handler for closing the MenulibreWindow."""
        self.quit()
