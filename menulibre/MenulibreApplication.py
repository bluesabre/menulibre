#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2015 Sean Davis <smd.seandavis@gmail.com>
#   Copyright (C) 2016 OmegaPhil <omegaphil@startmail.com>
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
import sys
from locale import gettext as _

from gi.repository import Gio, GObject, Gtk, Gdk, GdkPixbuf

from . import MenulibreStackSwitcher, MenulibreIconSelection
from . import MenulibreTreeview, MenulibreHistory, Dialogs
from . import MenulibreXdg, util
from .util import MenuItemTypes, check_keypress, getBasename
import menulibre_lib

import logging
logger = logging.getLogger('menulibre')

session = os.getenv("DESKTOP_SESSION")
root = os.getuid() == 0

category_descriptions = {
    # Standard Items
    'AudioVideo': _('Multimedia'),
    'Development': _('Development'),
    'Education': _('Education'),
    'Game': _('Games'),
    'Graphics': _('Graphics'),
    'Network': _('Internet'),
    'Office': _('Office'),
    'Settings': _('Settings'),
    'System': _('System'),
    'Utility': _('Accessories'),
    'WINE': _('WINE'),
    # Desktop Environment
    'DesktopSettings': _('Desktop configuration'),
    'PersonalSettings': _('User configuration'),
    'HardwareSettings': _('Hardware configuration'),
    # GNOME Specific
    'GNOME': _('GNOME application'),
    'GTK': _('GTK+ application'),
    'X-GNOME-PersonalSettings': _('GNOME user configuration'),
    'X-GNOME-HardwareSettings': _('GNOME hardware configuration'),
    'X-GNOME-SystemSettings': _('GNOME system configuration'),
    'X-GNOME-Settings-Panel': _('GNOME system configuration'),
    # Xfce Specific
    'XFCE': _('Xfce menu item'),
    'X-XFCE': _('Xfce menu item'),
    'X-Xfce-Toplevel': _('Xfce toplevel menu item'),
    'X-XFCE-PersonalSettings': _('Xfce user configuration'),
    'X-XFCE-HardwareSettings': _('Xfce hardware configuration'),
    'X-XFCE-SettingsDialog': _('Xfce system configuration'),
    'X-XFCE-SystemSettings': _('Xfce system configuration'),
}

category_groups = {
    'Utility': (
        'Accessibility', 'Archiving', 'Calculator', 'Clock',
        'Compression', 'FileTools', 'TextEditor', 'TextTools'
    ),
    'Development': (
        'Building', 'Debugger', 'IDE', 'GUIDesigner', 'Profiling',
        'RevisionControl', 'Translation', 'WebDevelopment'
    ),
    'Education': (
        'Art', 'ArtificialIntelligence', 'Astronomy', 'Biology',
        'Chemistry', 'ComputerScience', 'Construction',
        'DataVisualization', 'Economy', 'Electricity', 'Geography',
        'Geology', 'Geoscience', 'History', 'Humanities',
        'ImageProcessing', 'Languages', 'Literature', 'Maps', 'Math',
        'MedicalSoftware', 'Music', 'NumericalAnalysis',
        'ParallelComputing', 'Physics', 'Robotics', 'Spirituality',
        'Sports'
    ),
    'Game': (
        'ActionGame', 'AdventureGame', 'ArcadeGame', 'BoardGame',
        'BlocksGame', 'CardGame', 'Emulator', 'KidsGame', 'LogicGame',
        'RolePlaying', 'Shooter', 'Simulation', 'SportsGame',
        'StrategyGame'
    ),
    'Graphics': (
        '2DGraphics', '3DGraphics', 'OCR', 'Photography', 'Publishing',
        'RasterGraphics', 'Scanning', 'VectorGraphics', 'Viewer'
    ),
    'Network': (
        'Chat', 'Dialup', 'Feed', 'FileTransfer', 'HamRadio',
        'InstantMessaging', 'IRCClient', 'Monitor', 'News', 'P2P',
        'RemoteAccess', 'Telephony', 'TelephonyTools', 'WebBrowser',
        'WebDevelopment'
    ),
    'AudioVideo': (
        'AudioVideoEditing', 'DiscBurning', 'Midi', 'Mixer', 'Player',
        'Recorder', 'Sequencer', 'Tuner', 'TV'
    ),
    'Office': (
        'Calendar', 'ContactManagement', 'Database', 'Dictionary',
        'Chart', 'Email', 'Finance', 'FlowChart', 'PDA', 'Photography',
        'ProjectManagement', 'Presentation', 'Publishing',
        'Spreadsheet', 'WordProcessor'
    ),
    _('Other'): (
        'Amusement', 'ConsoleOnly', 'Core', 'Documentation',
        'Electronics', 'Engineering', 'GNOME', 'GTK', 'Java', 'KDE',
        'Motif', 'Qt', 'XFCE'
    ),
    'Settings': (
        'Accessibility', 'DesktopSettings', 'HardwareSettings',
        'PackageManager', 'Printing', 'Security'
    ),
    'System': (
        'Emulator', 'FileManager', 'Filesystem', 'FileTools', 'Monitor',
        'Security', 'TerminalEmulator'
    )
}

# Add support for X-Xfce-Toplevel items for XFCE environments.
if util.getDefaultMenuPrefix() == 'xfce-':
    category_groups['Xfce'] = ('X-Xfce-Toplevel',)

# Create a reverse-lookup
category_lookup = dict()
for key in list(category_groups.keys()):
    for item in category_groups[key]:
        category_lookup[item] = key


def lookup_category_description(spec_name):
    """Return a valid description string for a spec entry."""
    #if spec_name.startswith("menulibre-"):
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

    def __init__(self, app):
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

        # Set up the actions, menubar, and toolbar
        self.configure_application_actions(builder)
        self.configure_application_menubar(builder)
        self.configure_application_toolbar(builder)

        self.configure_headerbar(builder)
        self.configure_css()

        # Set up the application editor
        self.configure_application_editor(builder)

        # Set up the applicaton browser
        self.configure_application_treeview(builder)

    def root_lockout(self):
        if root:
            dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.ERROR,
                                        Gtk.ButtonsType.CLOSE,
                                        _("MenuLibre cannot be run as root."))
            dialog.format_secondary_markup(_("Please see the <a href='https://wiki.smdavis.us/doku.php?id=menulibre_faq'>online documentation</a> for more information."))
            dialog.run()
            sys.exit(1)

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
        self.set_wmclass(_("MenuLibre"), _("MenuLibre"))

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
        headerbar = Gtk.HeaderBar.new()
        headerbar.set_show_close_button(True)
        headerbar.set_title(_("MenuLibre"))
        headerbar.set_custom_title(Gtk.Label.new())

        # Add Launcher/Directory/Separator
        button = Gtk.MenuButton()
        self.action_items['add_button'] = [button]
        image = Gtk.Image.new_from_icon_name("list-add-symbolic",
                                             Gtk.IconSize.MENU)
        button.set_image(image)

        popup = builder.get_object('add_popup_menu')
        button.set_popup(popup)

        headerbar.pack_start(button)

        self.save_button.reparent(headerbar)

        builder.get_object("history_buttons").reparent(headerbar)

        self.revert_button.reparent(headerbar)
        self.delete_button.reparent(headerbar)

        headerbar.pack_end(self.search_box)

        builder.get_object("toolbar").destroy()

        self.set_titlebar(headerbar)
        headerbar.show_all()

    def configure_application_actions(self, builder):
        """Configure the GtkActions that are used in the Menulibre
        application."""
        self.actions = {}

        # Add Launcher
        self.actions['add_launcher'] = Gtk.Action(
                                            name='add_launcher',
                                            label=_('Add _Launcher...'),
                                            tooltip=_('Add Launcher...'),
                                            stock_id=Gtk.STOCK_NEW)

        # Add Directory
        self.actions['add_directory'] = Gtk.Action(
                                            name='add_directory',
                                            label=_('Add _Directory...'),
                                            tooltip=_('Add Directory...'),
                                            stock_id=Gtk.STOCK_NEW)

        # Add Separator
        self.actions['add_separator'] = Gtk.Action(
                                            name='add_separator',
                                            label=_('_Add Separator...'),
                                            tooltip=_('Add Separator...'),
                                            stock_id=Gtk.STOCK_NEW)

        # Save Launcher
        self.actions['save_launcher'] = Gtk.Action(
                                            name='save_launcher',
                                            label=_('_Save'),
                                            tooltip=_('Save'),
                                            stock_id=Gtk.STOCK_SAVE)

        # Undo
        self.actions['undo'] = Gtk.Action(
                                            name='undo',
                                            label=_('_Undo'),
                                            tooltip=_('Undo'),
                                            stock_id=Gtk.STOCK_UNDO)

        # Redo
        self.actions['redo'] = Gtk.Action(
                                            name='redo',
                                            label=_('_Redo'),
                                            tooltip=_('Redo'),
                                            stock_id=Gtk.STOCK_REDO)

        # Revert
        self.actions['revert'] = Gtk.Action(
                                            name='revert',
                                            label=_('_Revert'),
                                            tooltip=_('Revert'),
                                            stock_id=Gtk.STOCK_REVERT_TO_SAVED)

        # Delete
        self.actions['delete'] = Gtk.Action(
                                            name='delete',
                                            label=_('_Delete'),
                                            tooltip=_('Delete'),
                                            stock_id=Gtk.STOCK_DELETE)

        # Quit
        self.actions['quit'] = Gtk.Action(
                                            name='quit',
                                            label=_('_Quit'),
                                            tooltip=_('Quit'),
                                            stock_id=Gtk.STOCK_QUIT)

        # Help
        self.actions['help'] = Gtk.Action(
                                            name='help',
                                            label=_('_Contents'),
                                            tooltip=_('Help'),
                                            stock_id=Gtk.STOCK_HELP)

        # About
        self.actions['about'] = Gtk.Action(
                                            name='about',
                                            label=_('_About'),
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
                                            self.on_save_launcher_cb, builder)
        self.actions['undo'].connect('activate',
                                            self.on_undo_cb)
        self.actions['redo'].connect('activate',
                                            self.on_redo_cb)
        self.actions['revert'].connect('activate',
                                            self.on_revert_cb)
        self.actions['delete'].connect('activate',
                                            self.on_delete_cb)
        self.actions['quit'].connect('activate',
                                            self.on_quit_cb)
        self.actions['help'].connect('activate',
                                            self.on_help_cb)
        self.actions['about'].connect('activate',
                                            self.on_about_cb)

    def configure_application_menubar(self, builder):
        """Configure the application GlobalMenu (in Unity) and AppMenu."""
        self.app_menu_button = None
        placeholder = builder.get_object('app_menu_holder')

        # Show the menubar if using a Unity session.
        if session in ['ubuntu', 'ubuntu-2d']:
            builder.get_object('menubar').set_visible(True)

            # Connect the menubar events.
            for action_name in ['add_launcher', 'save_launcher', 'undo',
                                'redo', 'revert', 'quit', 'help', 'about']:
                widget = builder.get_object("menubar_%s" % action_name)
                widget.set_related_action(self.actions[action_name])
                widget.set_use_action_appearance(True)

    def configure_application_toolbar(self, builder):
        """Configure the application toolbar."""
        # Configure the Add, Save, Undo, Redo, Revert, Delete widgets.
        for action_name in ['save_launcher', 'undo', 'redo',
                            'revert', 'delete']:
            widget = builder.get_object("toolbar_%s" % action_name)
            widget.connect("clicked", self.activate_action_cb, action_name)

        self.action_items = dict()

        for action_name in ['add_launcher', 'add_directory', 'add_separator']:
            self.action_items[action_name] = []
            widget = builder.get_object('menubar_%s' % action_name)
            widget.connect('activate', self.activate_action_cb, action_name)
            self.action_items[action_name].append(widget)
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

        # Configure the search widget.
        self.search_box = builder.get_object('toolbar_search')
        self.search_box.connect('icon-press', self.on_search_cleared)

    def configure_application_treeview(self, builder):
        """Configure the menu-browsing GtkTreeView."""
        self.treeview = MenulibreTreeview.Treeview(self, builder)
        treeview = self.treeview.get_treeview()
        treeview.set_search_entry(self.search_box)
        self.search_box.connect('changed', self.on_app_search_changed,
                                           treeview, True)
        self.treeview.set_can_select_function(self.get_can_select)
        self.treeview.connect("cursor-changed",
                             self.on_apps_browser_cursor_changed, builder)
        self.treeview.connect("add-directory-enabled",
                             self.on_apps_browser_add_directory_enabled, builder)
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
        self.switcher.add_child(builder.get_object('categories'),
                                'categories', _('Categories'))
        self.switcher.add_child(builder.get_object('actions'),
                                'actions', _('Actions'))
        self.switcher.add_child(builder.get_object('advanced'),
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
            'Hidden': builder.get_object('entry_Hidden'),
            'DBusActivatable': builder.get_object('entry_DBusActivatable')
        }

        # Configure the switches
        for widget_name in ['Terminal', 'StartupNotify', 'NoDisplay']:
            widget = self.widgets[widget_name]
            widget.connect('notify::active', self.on_switch_toggle, widget_name)

        # These widgets are hidden when the selected item is a Directory.
        self.directory_hide_widgets = []
        for widget_name in ['details_frame', 'settings_placeholder',
                            'terminal_label', 'switch_Terminal',
                            'notify_label', 'switch_StartupNotify']:
            self.directory_hide_widgets.append(builder.get_object(widget_name))

        # Configure the Name/Comment widgets.
        for widget_name in ['Name', 'Comment']:
            button = builder.get_object('button_%s' % widget_name)
            cancel = builder.get_object('cancel_%s' % widget_name)
            accept = builder.get_object('apply_%s' % widget_name)
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

        # Commit changes to entries when focusing out.
        for widget_name in ['Exec', 'Path', 'GenericName', 'TryExec',
                            'OnlyShowIn', 'NotShowIn', 'MimeType', 'Keywords',
                            'StartupWMClass', 'Hidden', 'DBusActivatable']:
            self.widgets[widget_name].connect('focus-out-event',
                            self.on_entry_focus_out_event, widget_name)

        # Enable saving on any edit with an Entry.
        for widget_name in ['Exec', 'Path', 'GenericName', 'TryExec',
                            'OnlyShowIn', 'NotShowIn', 'MimeType', 'Keywords',
                            'StartupWMClass', 'Hidden', 'DBusActivatable']:
            self.widgets[widget_name].connect("changed",
                            self.on_entry_changed, widget_name)

        # Configure the Exec/Path widgets.
        for widget_name in ['Exec', 'Path']:
            button = builder.get_object('entry_%s' % widget_name)
            button.connect('icon-press', self.on_ExecPath_clicked,
                                         widget_name, builder)

        # Icon Selector
        self.icon_selector = MenulibreIconSelection.IconSelector(parent=self)

        # Connect the Icon menu.
        menu = builder.get_object("icon_select_menu")
        select_icon_name = builder.get_object("icon_select_by_icon_name")
        select_icon_name.connect("activate",
                                 self.on_IconSelectFromIcons_clicked,
                                 builder)
        select_icon_file = builder.get_object("icon_select_by_filename")
        select_icon_file.connect("activate",
                                 self.on_IconSelectFromFilename_clicked)

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
                                                        -1))
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
        renderer_combo.set_property("placeholder-text", _("Select a category"))
        renderer_combo.connect("edited", self.on_category_combo_changed)

        column_combo = Gtk.TreeViewColumn(_("Category Name"),
                                            renderer_combo, text=0)
        treeview.append_column(column_combo)

        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn(_("Description"),
                                            renderer_text, text=1)
        treeview.append_column(column_text)

        self.categories_treefilter.refilter()

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
            rows = sorted(rows, key=lambda row_data: row_data[key_columns[0]])

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
        icon_name = self.icon_selector.select_by_icon_name()
        if icon_name is not None:
            self.set_value('Icon', icon_name)

    def on_IconSelectFromFilename_clicked(self, widget):
        filename = self.icon_selector.select_by_filename()
        if filename is not None:
            self.set_value('Icon', filename)

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
        self.set_value(widget_name, widget.get_text())

    def on_entry_changed(self, widget, widget_name):
        """Enable saving when an entry has been modified."""
        if not self.history.is_blocked():
            self.actions['save_launcher'].set_sensitive(True)
            self.save_button.set_sensitive(True)

# Browse button functionality for Exec and Path widgets.
    def on_ExecPath_clicked(self, entry, icon, event, widget_name, builder):
        """Show the file selection dialog when Exec/Path Browse is clicked."""
        if widget_name == 'Path':
            title=_("Select a working directory...")
            action=Gtk.FileChooserAction.SELECT_FOLDER
        else:
            title = _("Select an executable...")
            action=Gtk.FileChooserAction.OPEN

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

# Applications Treeview
    def on_apps_browser_add_directory_enabled(self, widget, enabled, builder):
        """Update the Add Directory menu item when the selected row is
        changed."""
        if enabled:
            tooltip = None
        else:
            tooltip = _("Cannot add subdirectories to preinstalled"
                        " system paths.")

        self.actions['add_directory'].set_sensitive(enabled)
        for widget in self.action_items['add_directory']:
            widget.set_sensitive(enabled)
            widget.set_tooltip_text(tooltip)

    def on_apps_browser_cursor_changed(self, widget, value, builder):
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
                    'Keywords', 'StartupWMClass', 'Categories',
                    'Hidden', 'DBusActivatable']:
                    self.set_value(key, None)

        # Clear the Actions and Icon.
        self.set_value('Actions', None, store=True)
        self.set_value('Icon', None, store=True)

        model, row_data = self.treeview.get_selected_row_data()
        item_type = row_data[3]

        # If the selected row is a separator, hide the editor.
        if item_type == MenuItemTypes.SEPARATOR:
            self.editor.hide()
            self.set_value('Name', _("Separator"), store=True)
            self.set_value('Comment', "", store=True)
            self.set_value('Filename', None, store=True)
            self.set_value('Type', 'Separator', store=True)

        # Otherwise, show the editor and update the values.
        else:
            filename = self.treeview.get_selected_filename()
            new_launcher = filename is None

            # Check if this file still exists, those tricksy hobbitses...
            if (not new_launcher) and (not os.path.isfile(filename)):
                # If it does not, try to fallback...
                original_filename = filename
                basename = getBasename(filename)
                filename = util.getSystemLauncherPath(basename)
                if filename is not None:
                    row_data[6] = filename
                    self.treeview.update_launcher_instances(filename, row_data)

            if new_launcher or (filename is not None):
                self.editor.show()
                displayed_name = row_data[0]
                comment = row_data[1]

                self.set_value('Icon', row_data[5], store=True)
                self.set_value('Name', displayed_name, store=True)
                self.set_value('Comment', comment, store=True)
                self.set_value('Filename', filename, store=True)

                if item_type == MenuItemTypes.APPLICATION:
                    self.editor.show_all()
                    entry = MenulibreXdg.MenulibreDesktopEntry(filename)
                    for key in ['Exec', 'Path', 'Terminal', 'StartupNotify',
                                'NoDisplay', 'GenericName', 'TryExec',
                                'OnlyShowIn', 'NotShowIn', 'MimeType',
                                'Keywords', 'StartupWMClass', 'Categories',
                                'Hidden', 'DBusActivatable']:
                        self.set_value(key, entry[key], store=True)
                    self.set_value('Actions', entry.get_actions(),
                                                                store=True)
                    self.set_value('Type', 'Application')
                else:
                    self.set_value('Type', 'Directory')
                    for widget in self.directory_hide_widgets:
                        widget.hide()

            else:
                # Display a dialog saying this item is missing
                primary = _("No Longer Installed")
                secondary = _("This launcher has been removed from the "
                              "system.\nSelecting the next available item.")
                dialog = Gtk.MessageDialog(transient_for=self, modal=True,
                                message_type=Gtk.MessageType.INFO,
                                buttons=Gtk.ButtonsType.OK,
                                text=primary)
                dialog.format_secondary_markup(secondary)
                dialog.run()
                dialog.destroy()
                # Mark this item as missing to delete it later.
                missing = True

        # Renable updates to history.
        self.history.unblock()

        # Remove this item if it happens to be gone.
        if missing:
            self.delete_launcher()

    def on_app_search_changed(self, widget, treeview, expand=False):
        """Update search results when query text is modified."""
        query = widget.get_text()
        model = treeview.get_model()

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

    def on_search_cleared(self, widget, event, user_data=None):
        """Generic search cleared callback function."""
        widget.set_text("")

# Setters and Getters
    def set_editor_image(self, icon_name):
        """Set the editor Icon button image."""
        button, image = self.widgets['Icon']

        if icon_name is not None:
            # Load the Icon Theme.
            icon_theme = Gtk.IconTheme.get_default()

            # If the Icon Theme has the icon, set the image to that icon.
            if icon_theme.has_icon(icon_name):
                image.set_from_icon_name(icon_name, 48)
                self.icon_selector.set_icon_name(icon_name)
                return

            # If the icon name is actually a file, render it to the Image.
            elif os.path.isfile(icon_name):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_name)
                size = image.get_preferred_height()[1]
                scaled = pixbuf.scale_simple(size, size,
                                                GdkPixbuf.InterpType.HYPER)
                image.set_from_pixbuf(scaled)
                self.icon_selector.set_filename(icon_name)
                return

        image.set_from_icon_name("application-default-icon", 48)

    def set_editor_filename(self, filename):
        """Set the editor filename."""
        # Since the filename has changed, check if it is now writable...
        if filename is None or os.access(filename, os.W_OK):
            self.delete_button.set_sensitive(True)
            self.delete_button.set_tooltip_text("")
        else:
            self.delete_button.set_sensitive(False)
            self.delete_button.set_tooltip_text(
                _("You do not have permission to delete this file."))

        # If the filename is None, make it blank.
        if filename is None:
            filename = ""

        # Get the filename widget.
        widget = self.widgets['Filename']

        # Set the label and tooltip.
        widget.set_label("<small><i>%s</i></small>" % filename)
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

        # Clear the ThisEntry category list.
        this_index = self.categories_treestore.iter_n_children(None) - 1
        this_entry = self.categories_treestore.iter_nth_child(None, this_index)
        for i in range(self.categories_treestore.iter_n_children(this_entry)):
            child_iter = self.categories_treestore.iter_nth_child(this_entry, 0)
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

        # Return None if there are no actions.
        if len(model) == 0:
            return None

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
        except:
            return None

    def set_inner_value(self, key, value):
        """Set the value stored for key."""
        self.values[key] = value

    def set_value(self, key, value, adjust_widget=True, store=False):
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
                markup = "<big><b>%s</b></big>" % (value)
            else:
                markup = "%s" % (value)
            tooltip = "%s <i>(Click to modify.)</i>" % (value)

            button.set_tooltip_markup(tooltip)
            entry.set_text(value)
            label.set_label(markup)

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

        # Everything else is set by its widget type.
        else:
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
                    self.set_value('Hidden', "")
            else:
                logger.warning(("Unknown widget: %s" % key))

    def get_value(self, key):
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
        name = _("New Launcher")
        comment = ""
        categories = ""
        item_type = MenuItemTypes.APPLICATION
        icon_name = "application-default-icon"
        icon = Gio.ThemedIcon.new(icon_name)
        filename = None
        new_row_data = [name, comment, categories, item_type, icon, icon_name, filename]

        model, parent_data = self.treeview.get_parent_row_data()
        model, row_data = self.treeview.get_selected_row_data()

        # Currently selected item is a directory, take its categories.
        if row_data[3] == MenuItemTypes.DIRECTORY:
            self.treeview.add_child(new_row_data)

        # Currently selected item is not a directory, but has a parent.
        else:
            self.treeview.append(new_row_data)

        # If a parent item was found, use its categories for this launcher.
        if parent_data is not None:
            # Parent was found, take its categories.
            categories = util.getRequiredCategories(parent_data[6])
        else:
            # Parent was not found, this is a toplevel category
            categories = util.getRequiredCategories(None)

        self.set_editor_categories(';'.join(categories))

        self.actions['save_launcher'].set_sensitive(True)
        self.save_button.set_sensitive(True)

    def add_directory(self):
        """Add Directory callback function."""
        name = _("New Directory")
        comment = ""
        categories = ""
        item_type = MenuItemTypes.DIRECTORY
        icon_name = "applications-other"
        icon = Gio.ThemedIcon.new(icon_name)
        filename = None
        row_data = [name, comment, categories, item_type, icon, icon_name, filename, False]

        self.treeview.append(row_data)

        self.actions['save_launcher'].set_sensitive(True)
        self.save_button.set_sensitive(True)

    def add_separator(self):
        """Add Separator callback function."""
        name = "<s>                    </s>"
        tooltip = _("Separator")
        categories = ""
        filename = None
        icon = None
        icon_name = ""
        item_type = MenuItemTypes.SEPARATOR
        filename = None
        row_data = [name, tooltip, categories, item_type, icon, icon_name, filename]

        self.treeview.append(row_data)

        self.save_button.set_sensitive(False)

        self.treeview.update_menus()

    def save_launcher(self):
        """Save the current launcher details."""
        # Get the filename to be used.
        original_filename = self.get_value('Filename')
        item_type = self.get_value('Type')
        name = self.get_value('Name')
        filename = util.getSaveFilename(name, original_filename, item_type)
        logger.debug("Saving launcher as \"%s\"" % filename)

        model, row_data = self.treeview.get_selected_row_data()
        item_type = row_data[3]

        model, parent_data = self.treeview.get_parent_row_data()

        # Make sure required categories are in place.
        if parent_data is not None:
            # Parent was found, take its categories.
            required_categories = util.getRequiredCategories(parent_data[6])
        else:
            # Parent was not found, this is a toplevel category
            required_categories = util.getRequiredCategories(None)
        current_categories = self.get_value('Categories').split(';')
        all_categories = current_categories
        for category in required_categories:
            if category not in all_categories:
                all_categories.append(category)
        self.set_editor_categories(';'.join(all_categories))

        # Cleanup invalid entries and reorder the Categories and Actions
        self.cleanup_categories()
        self.cleanup_actions()

        # Open the file and start writing.
        with open(filename, 'w') as output:
            output.write('[Desktop Entry]\n')
            output.write('Version=1.0\n')
            for prop in ['Type', 'Name', 'GenericName', 'Comment', 'Icon',
                         'TryExec', 'Exec', 'Path', 'NoDisplay', 'Hidden',
                         'OnlyShowIn', 'NotShowIn', 'Categories', 'Keywords',
                         'MimeType', 'StartupWMClass', 'StartupNotify',
                         'Terminal', 'DBusActivatable']:
                value = self.get_value(prop)
                if value in [True, False]:
                    value = str(value).lower()
                if value:
                    output.write('%s=%s\n' % (prop, value))
            actions = self.get_editor_actions_string()
            if actions:
                output.write(actions)

        # Install the new item in its directory...
        self.treeview.xdg_menu_install(filename)

        # Set the editor to the new filename.
        self.set_value('Filename', filename)

        # Update the selected iter with the new details.
        name = self.get_value('Name')
        comment = self.get_value('Comment')
        categories = self.get_value('Categories')
        icon_name = self.get_value('Icon')
        self.treeview.update_selected(name, comment, categories, item_type,
                                     icon_name, filename)
        self.history.clear()

        # Update all instances
        model, row_data = self.treeview.get_selected_row_data()
        self.treeview.update_launcher_instances(original_filename, row_data)

        self.treeview.update_menus()

    def update_launcher_categories(self, remove, add):
        original_filename = self.get_value('Filename')
        if original_filename is None or not os.path.isfile(original_filename):
            return
        item_type = self.get_value('Type')
        name = self.get_value('Name')
        save_filename = util.getSaveFilename(name, original_filename,
                                             item_type, force_update=True)
        logger.debug("Saving launcher as \"%s\"" % save_filename)

        # Get the original contents
        with open(original_filename, 'r') as original:
            contents = original.readlines()

        # Write the new contents
        with open(save_filename, 'w') as new:
            updated_categories = False
            for line in contents:
                # Update the first instance of Categories
                if line.startswith('Categories=') and not updated_categories:
                    # Cleanup the line
                    line = line.strip()

                    # Get the current unmodified values
                    key, value = line.split('=')
                    categories = value.split(';')

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
                            except:
                                pass

                    categories.sort()

                    # Commit the changes
                    value = ';'.join(categories)
                    line = 'Categories=' + value + '\n'
                    updated_categories = True
                new.write(line)

        # Set the editor to the new filename.
        self.set_editor_filename(save_filename)

        # Update all instances
        model, row_data = self.treeview.get_selected_row_data()
        row_data[6] = save_filename
        self.treeview.update_launcher_instances(original_filename, row_data)

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

    def on_delete_cb(self, widget):
        """Delete callback function."""
        model, row_data = self.treeview.get_selected_row_data()
        name = row_data[0]
        item_type = row_data[3]

        # Prepare the strings
        if item_type == MenuItemTypes.SEPARATOR:
            question = _("Are you sure you want to delete this separator?")
            delete_func = self.delete_separator
        else:
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


class Application(Gtk.Application):
    """Menulibre GtkApplication"""

    def __init__(self):
        """Initialize the GtkApplication."""
        Gtk.Application.__init__(self)

    def do_activate(self):
        """Handle GtkApplication do_activate."""
        self.win = MenulibreWindow(self)
        self.win.show()

        self.win.connect('about', self.about_cb)
        self.win.connect('help', self.help_cb)
        self.win.connect('quit', self.quit_cb)

    def do_startup(self):
        """Handle GtkApplication do_startup."""
        Gtk.Application.do_startup(self)

        self.menu = Gio.Menu()
        self.menu.append(_("Help"), "app.help")
        self.menu.append(_("About"), "app.about")
        self.menu.append(_("Quit"), "app.quit")

        self.set_app_menu(self.menu)

        help_action = Gio.SimpleAction.new("help", None)
        help_action.connect("activate", self.help_cb)
        self.add_action(help_action)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.about_cb)
        self.add_action(about_action)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.quit_cb)
        self.add_action(quit_action)

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
