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
import shlex
import sys

import subprocess
import tempfile

from locale import gettext as _

from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gio, GLib, GObject, Gtk, Gdk, GdkPixbuf

from . import MenulibreTreeview, MenulibreHistory, Dialogs
from . import MenulibreXdg, util, ParsingErrorsDialog
from . import MenuEditor
from .ApplicationEditor import ApplicationEditor
from .Toolbar import Toolbar
from .Headerbar import Headerbar

from .util import MenuItemTypes, check_keypress, getRelativeName, getRelatedKeys
from .util import escapeText, getCurrentDesktop, getProcessList, getDefaultMenuPrefix
import menulibre_lib

import logging

logger = logging.getLogger('menulibre')

session = os.getenv("DESKTOP_SESSION", "")
root = os.getuid() == 0

current_desktop = getCurrentDesktop()

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


class MenulibreWindow(Gtk.ApplicationWindow):
    """The Menulibre application window."""

    __gsignals__ = {
        'about': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,
                  (GObject.TYPE_BOOLEAN,)),
        'help': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,
                 (GObject.TYPE_BOOLEAN,)),
        'quit': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,
                 (GObject.TYPE_BOOLEAN,)),
        'action-enabled': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE,
                 (GObject.TYPE_STRING, GObject.TYPE_BOOLEAN,)),
    }

    def __init__(self, app, headerbar_pref=True):
        """Initialize the Menulibre application."""
        self.root_lockout()

        self.action_items = dict()

        # Set up History
        self.history = MenulibreHistory.History()
        self.history.connect('undo-changed', self.on_undo_changed)
        self.history.connect('redo-changed', self.on_redo_changed)
        self.history.connect('revert-changed', self.on_revert_changed)

        # Steal the window contents for the GtkApplication.
        self.configure_application_window(app)

        self.values = dict()

        # Set up the actions and toolbar
        self.configure_application_actions()

        add_menu = self.get_add_menu()

        self.search_box = Gtk.SearchEntry.new()
        self.search_box.set_placeholder_text(_("Search"))
        self.search_box.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, "edit-find-symbolic")
        self.search_box.connect('icon-press', self.on_search_cleared)

        self.use_headerbar = headerbar_pref
        if headerbar_pref:
            self.configure_headerbar(add_menu)
        else:
            self.configure_application_toolbar(add_menu)

        # Configure events for the headerbar or toolbar (they have the same setup)
        self.connect_toolbar()

        self.configure_css()

        # Set up the application browser
        self.configure_application_treeview()

        # Determining paths of bad desktop files GMenu can't load - if some are
        # detected, alerting user via InfoBar
        self.bad_desktop_files = util.determine_bad_desktop_files()
        if self.bad_desktop_files:
            self.configure_application_bad_desktop_files_infobar()

        self.configure_menu_restart_infobar()

        self.show_all()

    def connect_toolbar(self):
        self.insert_action_item('add_button', self.add_button)

        self.save_button.connect("clicked", self.activate_action_cb, 'save_launcher')
        self.save_button.set_sensitive(False)
        self.insert_action_item('save_launcher', self.save_button)

        self.undo_button.connect("clicked", self.activate_action_cb, 'undo')
        self.undo_button.set_sensitive(False)
        self.insert_action_item('undo', self.undo_button)

        self.redo_button.connect("clicked", self.activate_action_cb, 'redo')
        self.redo_button.set_sensitive(False)
        self.insert_action_item('redo', self.redo_button)

        self.revert_button.connect("clicked", self.activate_action_cb, 'revert')
        self.revert_button.set_sensitive(False)
        self.insert_action_item('revert', self.revert_button)

        self.execute_button.connect("clicked", self.activate_action_cb, 'execute')
        self.insert_action_item('execute', self.execute_button)

        self.delete_button.connect("clicked", self.activate_action_cb, 'delete')
        self.delete_button.set_sensitive(False)
        self.insert_action_item('delete', self.delete_button)

    def insert_action_item(self, key, widget):
        if key not in self.action_items.keys():
            self.action_items[key] = []
        self.action_items[key].append(widget)

    def get_add_menu(self):
        menu = Gio.Menu.new()

        menu_items = {
            'app.add_launcher': _("Add _Launcher"),
            'app.add_directory': _("Add _Directory"),
            'app.add_separator': _("Add _Separator")
        }

        for action_name, label in menu_items.items():
            menu.append(label, action_name)

        return menu

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

    def configure_application_window(self, app):
        window_title = "MenuLibre"

        # Initialize the GtkApplicationWindow.
        Gtk.Window.__init__(self, title=window_title, application=app)
        self.set_wmclass(window_title, "MenuLibre")

        # Restore the window properties.
        self.set_title("MenuLibre")
        self.set_icon_name("menulibre")
        self.set_default_size(-1, 500)
        self.set_size_request(-1, 640)

        # Reparent the widgets.
        box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.add(box)

        self.toolbar_container = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        box.pack_start(self.toolbar_container, False, False, 0)

        self.infobar_container = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        box.pack_start(self.infobar_container, False, False, 0)

        self.panes = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        box.pack_start(self.panes, True, True, 0)

        # Connect any window-specific events.
        self.connect('key-press-event', self.on_window_keypress_event)
        self.connect('delete-event', self.on_window_delete_event)

    def configure_css(self):
        css = """
        #MenulibreSidebarToolbar {
            border-left-width: 0;
            border-right-width: 0;
            border-bottom-width: 0;
            border-radius: 0;
        }
        #MenulibreSidebarScroll.frame {
            border-left-width: 0;
            border-right-width: 0;
        }
        """
        style_provider = Gtk.CssProvider.new()
        style_provider.load_from_data(bytes(css.encode()))

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def configure_headerbar(self, add_menu):
        # Configure the Add, Save, Undo, Redo, Revert, Delete widgets.
        headerbar = Headerbar()

        self.add_button = headerbar.add_menu_button("list-add-symbolic", _("Add..."), add_menu)
        self.save_button = headerbar.add_button("document-save-symbolic", _("Save Launcher"))

        self.undo_button, self.redo_button = headerbar.add_buttons([
            ["edit-undo-symbolic", _("Undo")],
            ["edit-redo-symbolic", _("Redo")],
        ])

        self.revert_button = headerbar.add_button("document-revert-symbolic", _("Revert"))
        self.execute_button = headerbar.add_button("media-playback-start-symbolic", _("Test Launcher"))
        self.delete_button = headerbar.add_button("edit-delete-symbolic", _("Delete..."))

        headerbar.add_search(self.search_box)

        self.set_titlebar(headerbar)
        headerbar.show_all()

    def configure_application_actions(self):
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
                                              self.on_save_launcher_cb)
        self.actions['undo'].connect('activate', self.on_undo_cb)
        self.actions['redo'].connect('activate', self.on_redo_cb)
        self.actions['revert'].connect('activate', self.on_revert_cb)
        self.actions['execute'].connect('activate', self.on_execute_cb)
        self.actions['delete'].connect('activate', self.on_delete_cb)
        self.actions['quit'].connect('activate', self.on_quit_cb)
        self.actions['help'].connect('activate', self.on_help_cb)
        self.actions['about'].connect('activate', self.on_about_cb)

    def configure_application_bad_desktop_files_infobar(self):
        """Configure InfoBar to alert user to bad desktop files."""
        self.infobar = Gtk.InfoBar.new()
        self.infobar.set_message_type(Gtk.MessageType.WARNING)
        self.infobar.set_no_show_all(True)
        self.infobar_container.add(self.infobar)

        content = self.infobar.get_content_area()

        label = Gtk.Label.new(_("Invalid desktop files detected! Please see details."))
        label.show()
        content.add(label)

        self.infobar.add_button(_('Details'), Gtk.ResponseType.YES)

        self.infobar.show()

        # Hook up events
        self.infobar.set_show_close_button(True)
        self.infobar.set_default_response(Gtk.ResponseType.CLOSE)

        self.infobar.connect('response',
                             self.on_bad_desktop_files_infobar_response)

    def configure_menu_restart_infobar(self):
        self.menu_restart_infobar = Gtk.InfoBar.new()
        self.menu_restart_infobar.set_message_type(Gtk.MessageType.WARNING)
        self.menu_restart_infobar.set_no_show_all(True)
        self.infobar_container.add(self.menu_restart_infobar)

        content = self.menu_restart_infobar.get_content_area()

        label = Gtk.Label.new(_("Your applications menu may need to be restarted."))
        label.show()
        content.add(label)

        self.menu_restart_infobar.add_button(_("Restart menu..."), Gtk.ResponseType.ACCEPT)

        self.menu_restart_infobar.set_show_close_button(True)
        self.menu_restart_infobar.set_default_response(Gtk.ResponseType.CLOSE)

        self.menu_restart_infobar.connect('response',
                             self.on_menu_restart_infobar_response)

    def on_menu_restart_infobar_response(self, infobar, response_id):
        if response_id == Gtk.ResponseType.CLOSE:
            infobar.hide()
        elif response_id == Gtk.ResponseType.ACCEPT:
            self.on_menu_restart_button_activate(infobar)

    def configure_application_toolbar(self, add_menu):
        """Configure the application toolbar."""
        toolbar = Toolbar()
        self.toolbar_container.add(toolbar)

        self.add_button = toolbar.add_menu_button("list-add", _("Add..."), add_menu)

        toolbar.add_separator()

        self.save_button = toolbar.add_button("document-save", _("Save"))

        toolbar.add_separator()

        self.undo_button = toolbar.add_button("edit-undo", _("Undo"))
        self.redo_button = toolbar.add_button("edit-redo", _("Redo"))

        toolbar.add_separator()

        self.revert_button = toolbar.add_button("document-revert", _("Revert"))

        toolbar.add_separator()

        self.execute_button = toolbar.add_button("system-run", _("Test Launcher"))

        toolbar.add_separator()

        self.delete_button = toolbar.add_button("edit-delete", _("Delete..."))

        separator = toolbar.add_separator()
        separator.set_draw(False)
        separator.set_expand(True)

        toolbar.add_search(self.search_box)

        toolbar.show_all()

    def configure_application_treeview(self):
        """Configure the menu-browsing GtkTreeView."""
        self.treeview = MenulibreTreeview.Treeview(self)
        if not self.treeview.loaded:
            self.menu_load_failure()

        self.panes.add(self.treeview)

        self.editor = ApplicationEditor()
        self.panes.add(self.editor)

        self.treeview.set_search_entry(self.search_box)
        self.search_box.connect('changed', self.on_app_search_changed, True)
        self.treeview.set_can_select_function(self.get_can_select)
        self.treeview.connect("cursor-changed",
                              self.on_apps_browser_cursor_changed)
        self.treeview.connect("add-directory-enabled",
                              self.on_apps_browser_add_directory_enabled)
        self.treeview.connect("requires-menu-reload",
                              self.on_apps_browser_requires_menu_reload)
        self.treeview.reset_cursor()

        self.editor.connect("value-changed", self.on_smart_widget_changed)

    def get_can_select(self):
        if self.save_button.get_sensitive():
            dialog = Dialogs.SaveOnLeaveDialog(self, self.use_headerbar)

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

    def activate_action_cb(self, widget, action_name):
        """Activate the specified GtkAction."""
        self.actions[action_name].activate()

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
        self.emit('action-enabled', 'save_launcher', enabled)

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

# Categories

    def on_smart_widget_changed(self, widget, key, value):
        self.set_value(key, value, False)

        if key == 'Filename':
            self.set_editor_filename(value)

    def cleanup_actions(self):
        """Cleanup the Actions treeview. Remove any rows where name or command
        have not been set."""
        self.editor.remove_incomplete_actions()

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
            dialog = Dialogs.SaveOnCloseDialog(self, self.use_headerbar)
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


# Applications Treeview
    def on_apps_browser_requires_menu_reload(self, widget, required):
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


    def on_apps_browser_add_directory_enabled(self, widget, enabled):
        """Update the Add Directory menu item when the selected row is
        changed."""
        # Always allow creating sub directories
        enabled = True

        self.actions['add_directory'].set_sensitive(enabled)
        self.emit('action-enabled', 'add_directory', enabled)

    def on_apps_browser_cursor_changed(self, widget, value):  # noqa
        """Update the editor frame when the selected row is changed."""
        missing = False

        # Clear history
        self.history.clear()

        # Hide the Name and Comment editors
        self.editor.cancel()

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
            self.execute_button.set_sensitive(False)

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
                    self.execute_button.set_sensitive(False)

            else:
                # Display a dialog saying this item is missing
                dialog = Dialogs.LauncherRemovedDialog(self, self.use_headerbar)
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

    def on_app_search_changed(self, widget, expand=False):
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
                if name in self.action_items:
                    for widget in self.action_items[name]:
                        widget.set_sensitive(True)
                if name in self.actions:
                    self.actions[name].set_sensitive(True)
                    self.emit('action-enabled', name, True)

            # Enable deletion (LP: #1751616)
            #self.delete_button.set_sensitive(True)
            #self.delete_button.set_tooltip_text(_("Delete..."))

        # If the entry has a query...
        else:
            # Show the clear button.
            widget.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY,
                                           'edit-clear-symbolic')

            self.treeview.set_searchable(True)

            # Disable add functionality
            for name in ['add_launcher', 'add_directory', 'add_separator',
                         'add_button']:
                if name in self.action_items:
                    for widget in self.action_items[name]:
                        widget.set_sensitive(False)
                if name in self.actions:
                    self.actions[name].set_sensitive(False)
                    self.emit('action-enabled', name, False)

            # Rerun the filter.
            self.treeview.search(self.search_box.get_text())

            # Disable deletion (LP: #1751616)
            self.delete_button.set_sensitive(False)
            self.delete_button.set_tooltip_text(_("Delete..."))

    def on_search_cleared(self, widget, event, user_data=None):
        """Generic search cleared callback function."""
        widget.set_text("")

# Setters and Getters
    def set_editor_filename(self, filename):
        """Set the editor filename."""
        # Since the filename has changed, check if it is now writable...
        if filename is None or os.access(filename, os.W_OK):
            self.delete_button.set_sensitive(True)
            self.delete_button.set_tooltip_text(_("Delete..."))
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
            self.delete_button.set_tooltip_text(_("You cannot delete this file while a search is active."))

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
        else:
            self.editor.set_value(key, value)

    def get_value(self, key):  # noqa
        """Return the value stored for the specified key."""
        return self.editor.get_value(key)

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

        if parent_data is not None and not dir_selected:
            # A parent item has been found, and the current selection is not a
            # directory, so the resulting item will be placed at the current level
            # fetch the parent's categories
            parent_directory = parent_data[MenuEditor.COL_FILENAME]

        elif parent_data is not None and dir_selected:
            # A directory lower than the top-level has been selected - the
            # launcher will be added into it (e.g. as the first item),
            # therefore it essentially has a parent of the current selection
            parent_directory = row_data[MenuEditor.COL_FILENAME]

        else:
            # Parent was not found, this is a toplevel category
            parent_directory = None

        self.editor.clear_categories()
        self.editor.insert_required_categories(parent_directory)

        self.actions['save_launcher'].set_sensitive(True)
        self.emit('action-enabled', 'save_launcher', True)
        self.save_button.set_sensitive(True)

        self.editor.take_focus()

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
        self.emit('action-enabled', 'save_launcher', True)
        self.save_button.set_sensitive(True)

        self.editor.take_focus()

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
                for show, name, displayed, command in \
                        self.editor.get_actions():
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
                parent_directory = parent_data[MenuEditor.COL_FILENAME]
            else:
                # Parent was not found, this is a toplevel category
                parent_directory = None

            self.editor.insert_required_categories(parent_directory)

            # Cleanup invalid entries and reorder the Categories and Actions
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
        self.set_value('Filename', save_filename)

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

    def on_save_launcher_cb(self, widget):
        """Save Launcher callback function."""
        self.editor.commit()
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
        dialog = Dialogs.RevertDialog(self, self.use_headerbar)
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

    def on_execute_cb(self, widget):
        """Execute callback function."""
        self.editor.commit()
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

        dialog = Dialogs.DeleteDialog(self, question, self.use_headerbar)

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

        log_dialog = ParsingErrorsDialog.ParsingErrorsDialog(
            parent=self, use_header_bar=self.use_headerbar
        )

        # Building up a list of all known failures associated with the bad
        # desktop files
        for desktop_file in self.bad_desktop_files:
            log_dialog.add_item(desktop_file,
                                util.validate_desktop_file(desktop_file))

        log_dialog.run()
        log_dialog.destroy()


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

        add_launcher_action = Gio.SimpleAction.new("add_launcher", None)
        add_launcher_action.connect("activate", self.action_cb, "add_launcher")
        self.add_action(add_launcher_action)

        add_directory_action = Gio.SimpleAction.new("add_directory", None)
        add_directory_action.connect("activate", self.action_cb, "add_directory")
        self.add_action(add_directory_action)

        add_separator_action = Gio.SimpleAction.new("add_separator", None)
        add_separator_action.connect("activate", self.action_cb, "add_separator")
        self.add_action(add_separator_action)

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
        dialog = Dialogs.HelpDialog(self.win, self.win.use_headerbar)
        dialog.show()

    def about_cb(self, widget, data=None):
        """About callback function.  Display the AboutDialog."""
        dialog = Dialogs.AboutDialog(self.win, self.win.use_headerbar)
        dialog.show()

    def quit_cb(self, widget, data=None):
        """Signal handler for closing the MenulibreWindow."""
        self.quit()

    def action_cb(self, widget, data=None, action_name=None):
        self.win.activate_action_cb(None, action_name)
