#!/usr/bin/python3
import locale
import os
import re
from locale import gettext as _

from gi.repository import Gio, GObject, Gtk, Pango, Gdk

from . import MenuEditor, MenulibreXdg
from .enums import MenuItemTypes

from xml.sax.saxutils import escape

locale.textdomain('menulibre')

def check_keypress(event, keys):
    if 'Control' in keys:
        if not bool(event.get_state() & Gdk.ModifierType.CONTROL_MASK):
            return False
    if 'Alt' in keys:
        if not bool(event.get_state() & Gdk.ModifierType.MOD1_MASK):
            return False
    if 'Shift' in keys:
        if not bool(event.get_state() & Gdk.ModifierType.SHIFT_MASK):
            return False
    if 'Super' in keys:
        if not bool(event.get_state() & Gdk.ModifierType.SUPER_MASK):
            return False
            
    if Gdk.keyval_name(event.get_keyval()[1]).lower() not in keys:
        return False
        
    return True
            

session = os.getenv("DESKTOP_SESSION")

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


class MenulibreWindow(Gtk.ApplicationWindow):
    ui_file = 'data/ui/MenulibreWindow.glade'

    __gsignals__ = {
        'about': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,
                  (GObject.TYPE_BOOLEAN,)),
        'help': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,
                 (GObject.TYPE_BOOLEAN,)),
        'quit': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,
                 (GObject.TYPE_BOOLEAN,))
    }

    def __init__(self, app):
        # Initialize the GtkBuilder to get our widgets from Glade.
        builder = Gtk.Builder()
        builder.add_from_file(self.ui_file)

        # Set up the application window, steal the window contents for the GtkApplication.
        self.configure_application_window(builder, app)
        
        self.values = dict()

        # Set up the actions, menubar, and toolbar
        self.configure_application_actions(builder)
        self.configure_application_menubar(builder)
        self.configure_application_toolbar(builder)

        # Set up the application editor
        self.configure_application_editor(builder)
        
        # Set up the applicaton browser
        self.configure_application_treeview(builder)

        self.history_undo = list()
        self.history_redo = list()
        
    def configure_application_window(self, builder, app):
        # Glade is unable to create a GtkApplication, so we have to reparent
        # the window contents to our new window. Here we get the contents.
        window = builder.get_object('menulibre_window')
        window_title = window.get_title()
        window_icon = window.get_icon_name()
        window_contents = window.get_children()[0]
        size_request = window.get_size_request()

        # Initialize the GtkApplicationWindow.
        Gtk.Window.__init__(self, title=window_title, application=app)
        self.set_wmclass(_("MenuLibre"), _("MenuLibre"))
        self.set_title(window_title)
        self.set_icon_name(window_icon)
        self.set_size_request(size_request[0], size_request[1])
        window_contents.reparent(self)
        
        self.connect('key-press-event', self.on_window_keypress_event)
        
    def configure_application_actions(self, builder):
        self.actions = {}

        # Add Launcher
        self.actions['add_launcher'] = Gtk.Action(  
                                            'add_launcher', 
                                            _('_Add Launcher...'),
                                            _('Add Launcher...'),
                                            Gtk.STOCK_NEW)
                                            
        # Save Launcher action and related widgets
        self.actions['save_launcher'] = Gtk.Action(
                                            'save_launcher', 
                                            _('_Save'),
                                            _('Save'),
                                            Gtk.STOCK_SAVE)

        # Undo action and related widgets
        self.actions['undo'] = Gtk.Action(  'undo', 
                                            _('_Undo'),
                                            _('Undo'),
                                            Gtk.STOCK_UNDO)
                                            
        # Redo action and related widgets
        self.actions['redo'] = Gtk.Action(  'redo', 
                                            _('_Redo'),
                                            _('Redo'),
                                            Gtk.STOCK_REDO)

        # Revert action and related widgets
        self.actions['revert'] = Gtk.Action('revert', 
                                            _('_Revert'),
                                            _('Revert'),
                                            Gtk.STOCK_REVERT_TO_SAVED)
                                            
        # Quit action and related widgets
        self.actions['quit'] = Gtk.Action(  'quit', 
                                            _('_Quit'),
                                            _('Quit'),
                                            Gtk.STOCK_QUIT)
                                            
        # Help action and related widgets
        self.actions['help'] = Gtk.Action(  'help', 
                                            _('_Contents'),
                                            _('Help'),
                                            Gtk.STOCK_HELP)
                                            
        # About action and related widgets
        self.actions['about'] = Gtk.Action( 'about', 
                                            _('_About'),
                                            _('About'),
                                            Gtk.STOCK_ABOUT)
                                            
        self.actions['add_launcher'].connect('activate', 
                                            self.on_add_launcher_cb)
        self.actions['save_launcher'].connect('activate', 
                                            self.on_save_launcher_cb)
        self.actions['undo'].connect('activate', 
                                            self.on_undo_cb)
        self.actions['redo'].connect('activate', 
                                            self.on_redo_cb)
        self.actions['revert'].connect('activate', 
                                            self.on_revert_cb)
        self.actions['quit'].connect('activate', 
                                            self.on_quit_cb)
        self.actions['help'].connect('activate', 
                                            self.on_help_cb)
        self.actions['about'].connect('activate', 
                                            self.on_about_cb)
                                            
    def configure_application_menubar(self, builder):
        # Configure Global Menu and AppMenu
        self.app_menu_button = None
        if session not in ['gnome', 'ubuntu', 'ubuntu-2d']:
            # Create the AppMenu button on the rightside of the toolbar
            self.app_menu_button = Gtk.MenuButton()
            self.app_menu_button.set_size_request(32, 32)

            # Use the classic "cog" image for the button.
            image = Gtk.Image.new_from_icon_name("emblem-system-symbolic",
                                                 Gtk.IconSize.MENU)
            self.app_menu_button.set_image(image)
            self.app_menu_button.show()

            # Pack the AppMenu button.
            placeholder = builder.get_object('app_menu_holder')
            placeholder.add(self.app_menu_button)

        builder.get_object('menubar').set_visible(session in ['ubuntu',
                                                              'ubuntu-2d'])
                                                              
        for action_name in ['add_launcher', 'save_launcher', 'undo', 'redo', 
                            'revert', 'quit', 'help', 'about']:
            widget = builder.get_object("menubar_%s" % action_name)
            widget.set_related_action(self.actions[action_name])
            widget.set_use_action_appearance(True)
            
    def activate_action_cb(self, widget, action_name):
        self.actions[action_name].activate()
            
    def configure_application_toolbar(self, builder):
        self.delete_button = builder.get_object('toolbar_delete')
        
        for action_name in ['add_launcher', 'save_launcher', 'undo', 'redo', 
                            'revert']:
            widget = builder.get_object("toolbar_%s" % action_name)
            widget.connect("clicked", self.activate_action_cb, action_name)
        
        self.search_box = builder.get_object('toolbar_search')
        self.search_box.connect('changed', self.on_search_changed)
        self.search_box.connect('icon-press', self.on_search_cleared)
        
    def configure_application_treeview(self, builder):
        self.treestore = MenuEditor.get_treestore()
        
        self.treeview = builder.get_object('classic_view_treeview')

        col = Gtk.TreeViewColumn("Item")
        col_cell_text = Gtk.CellRendererText()
        col_cell_text.set_property("ellipsize", Pango.EllipsizeMode.END)
        col_cell_img = Gtk.CellRendererPixbuf()
        col_cell_img.set_property("stock-size", Gtk.IconSize.LARGE_TOOLBAR)
        col.pack_start(col_cell_img, False)
        col.pack_start(col_cell_text, True)
        col.add_attribute(col_cell_text, "markup", 0)
        col.set_cell_data_func(col_cell_img, self.icon_name_func, None)
        self.treeview.set_tooltip_column(1)

        # Allow filtering/searching results
        self.treefilter = self.treestore.filter_new()
        self.treefilter.set_visible_func(self.treeview_match_func)
        self.treeview.set_search_column(0)
        self.treeview.set_search_entry(self.search_box)

        self.treeview.append_column(col)
        self.treeview.set_model(self.treefilter)

        self.treeview.connect("cursor-changed",
                                self.on_treeview_cursor_changed, None)
        self.treeview.connect("key-press-event",
                                self.on_treeview_key_press_event, None)

        move_up = builder.get_object('classic_view_move_up')
        move_up.connect('clicked', self.move_iter, (self.treeview, -1))
        move_down = builder.get_object('classic_view_move_down')
        move_down.connect('clicked', self.move_iter, (self.treeview, 1))

        self.treeview.show_all()
        self.treeview.grab_focus()
        
        path = Gtk.TreePath.new_from_string("0")
        self.treeview.set_cursor(path)
        
    def configure_application_editor(self, builder):
        # Settings Notebook, advanced configuration, fancy notebook
        self.settings_notebook = builder.get_object('settings_notebook')
        buttons = ['categories_button', 'quicklists_button', 'advanced_button']
        for i in range(len(buttons)):
            button = builder.get_object(buttons[i])
            button.connect("clicked", self.on_settings_group_changed, i)
            button.activate()
        
        self.editor = builder.get_object('application_editor')

        self.widgets = dict()
        
        # Pack the Icon GtkButton and GtkImage widgets
        self.widgets['Icon'] = (
            builder.get_object('button_Icon'),
            builder.get_object('image_Icon'))
            
        # Pack the Name GtkButton, GtkLabel, and GtkEntry widgets
        self.widgets['Name'] = (
            builder.get_object('button_Name'),
            builder.get_object('label_Name'),
            builder.get_object('entry_Name'))
            
        # Pack the Comment GtkButton, GtkLabel, and GtkEntry widgets
        self.widgets['Comment'] = (
            builder.get_object('button_Comment'),
            builder.get_object('label_Comment'),
            builder.get_object('entry_Comment'))

        self.widgets['Filename'] = builder.get_object('label_Filename')
        self.widgets['Exec'] = builder.get_object('entry_Exec')
        self.widgets['Path'] = builder.get_object('entry_Path')
        self.widgets['Terminal'] = builder.get_object('switch_Terminal')
        self.widgets['StartupNotify'] = builder.get_object('switch_StartupNotify')
        self.widgets['NoDisplay'] = builder.get_object('switch_NoDisplay')
        self.widgets['GenericName'] = builder.get_object('entry_GenericName')
        self.widgets['TryExec'] = builder.get_object('entry_TryExec')
        self.widgets['OnlyShowIn'] = builder.get_object('entry_OnlyShowIn')
        self.widgets['NotShowIn'] = builder.get_object('entry_NotShowIn')
        self.widgets['MimeType'] = builder.get_object('entry_Mimetype')
        self.widgets['Keywords'] = builder.get_object('entry_Keywords')
        self.widgets['StartupWMClass'] = builder.get_object('entry_StartupWMClass')
        self.widgets['Hidden'] = builder.get_object('entry_Hidden')
        self.widgets['DBusActivatable'] = builder.get_object('entry_DBusActivatable')
        self.categories_treeview = builder.get_object('categories_treeview')
        self.actions_treeview = builder.get_object('actions_treeview')

        self.directory_hide_widgets = []
        for widget_name in ['details_frame', 'settings_frame',
                            'terminal_label', 'switch_Terminal',
                            'notify_label', 'switch_StartupNotify']:
            self.directory_hide_widgets.append(builder.get_object(widget_name))
            
    def on_window_keypress_event(self, widget, event, user_data=None):
        if check_keypress(event, ['Control', 'f']):
            self.search_box.grab_focus()
            return True
        if check_keypress(event, ['Control', 's']):
            print ("Save")
        return False
            

    def on_settings_group_changed(self, widget, user_data=None):
        if widget.get_active():
            self.settings_notebook.set_current_page(user_data)
            
    def get_treeview_selected_expanded(self, treeview):
        sel = treeview.get_selection()
        model, treeiter = sel.get_selected()
        row = model[treeiter]
        return treeview.row_expanded(row.path)
            
    def set_treeview_selected_expanded(self, treeview, expanded=True):
        sel = treeview.get_selection()
        model, treeiter = sel.get_selected()
        row = model[treeiter]
        if expanded:
            treeview.expand_row(row.path, False)
        else:
            treeview.collapse_row(row.path)
            
    def toggle_treeview_selected_expanded(self, treeview):
        expanded = self.get_treeview_selected_expanded(treeview)
        self.set_treeview_selected_expanded(treeview, not expanded)

    def on_treeview_key_press_event(self, widget, event, user_data=None):
        if check_keypress(event, ['right']):
            self.set_treeview_selected_expanded(widget, True)
            return True
        elif check_keypress(event, ['left']):
            self.set_treeview_selected_expanded(widget, False)
            return True
        elif check_keypress(event, ['space']):
            self.toggle_treeview_selected_expanded(widget)
            return True
        elif check_keypress(event, ['return']):
            print ("Activate")
            return True
        return False
        

    def on_treeview_cursor_changed(self, widget, selection):
        sel = widget.get_selection()
        if sel:
            treestore, treeiter = sel.get_selected()
            if not treestore:
                return
            if not treeiter:
                return
                
            for key in ['Exec', 'Path', 'Terminal', 'StartupNotify',
                        'NoDisplay', 'GenericName', 'TryExec',
                        'OnlyShowIn', 'NotShowIn', 'MimeType',
                        'Keywords', 'StartupWMClass', 'Categories']:
                        self.set_value(key, None)
            self.set_editor_actions(None)
            self.set_editor_image(None)
                
            item_type = treestore[treeiter][2]
            if item_type == MenuItemTypes.SEPARATOR:
                self.editor.hide()
                self.set_value('Name', _("Separator"))
                self.set_value('Comment', "")
                self.set_value('Filename', None)
                self.set_value('Type', 'Separator')
            else:
                self.editor.show()

                displayed_name = treestore[treeiter][0]
                comment = treestore[treeiter][1]
                filename = treestore[treeiter][5]
                self.set_editor_image(treestore[treeiter][3], treestore[treeiter][4])
                self.set_value('Name', displayed_name)
                self.set_value('Comment', comment)
                self.set_value('Filename', filename)

                if item_type == MenuItemTypes.APPLICATION:
                    self.editor.show_all()
                    entry = MenulibreXdg.MenulibreDesktopEntry(filename)
                    for key in ['Exec', 'Path', 'Terminal', 'StartupNotify',
                                'NoDisplay', 'GenericName', 'TryExec',
                                'OnlyShowIn', 'NotShowIn', 'MimeType',
                                'Keywords', 'StartupWMClass', 'Categories']:
                        self.set_value(key, entry[key])
                    self.set_editor_actions(entry.get_actions())
                    self.set_value('Type', 'Application')
                else:
                    self.set_value('Type', 'Directory')
                    for widget in self.directory_hide_widgets:
                        widget.hide()

    def icon_name_func(self, col, renderer, treestore, treeiter, user_data):
        renderer.set_property("gicon", treestore[treeiter][3])
        pass
        
    def treeview_match(self, model, treeiter, query):
        name, comment, item_type, icon, pixbuf, desktop = model[treeiter][:]
        
        if item_type == MenuItemTypes.SEPARATOR:
            return False

        if not name:
            name = ""
        if not comment:
            comment = ""

        self.treeview.expand_all()
        
        if query in name.lower():
            return True
            
        if query in comment.lower():
            return True
            
        if item_type == MenuItemTypes.DIRECTORY:
            return self.treeview_match_directory(query, model, treeiter)

        return False
        
    def treeview_match_directory(self, query, model, treeiter):
        # Iterate through iter children, return True if any match and this should display.
        
        for child_i in range(model.iter_n_children(treeiter)):
            child = model.iter_nth_child(treeiter, child_i)
            if self.treeview_match(model, child, query):
                return True
                
        return False
        
    def treeview_match_func(self, model, treeiter, data=None):
        query = str(self.search_box.get_text().lower())
        
        if query == "":
            return True
            
        return self.treeview_match(model, treeiter, query)
        
    def on_search_changed(self, widget, user_data=None):
        query = widget.get_text()
        
        if len(query) == 0:
            widget.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, None)
            
        else:
            widget.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, 'edit-clear-symbolic')
            self.treeview.expand_all()

        self.treefilter.refilter()
            
    def on_search_cleared(self, widget, event, user_data=None):
        widget.set_text("")

    def set_editor_image(self, gicon, icon_name=None):
        button, image = self.widgets['Icon']
        if gicon:
            image.set_from_gicon(
                gicon, image.get_preferred_height()[0])
        else:
            image.set_from_icon_name(
                "application-default-icon", 48)
        self.values['icon-name'] = icon_name

    def set_editor_filename(self, filename):
        # Since the filename has changed, check if it is now writable...
        if filename is None or os.access(filename, os.W_OK):
            self.delete_button.set_sensitive(True)
            self.delete_button.set_tooltip_text("")
        else:
            self.delete_button.set_sensitive(False)
            self.delete_button.set_tooltip_text(
                _("You do not have permission to delete this file."))

        if filename is None:
            filename = ""
            
        widget = self.widgets['Filename']

        widget.set_label("<small><i>%s</i></small>" % filename)
        widget.set_tooltip_text(filename)
        
    def get_editor_categories(self):
        model = self.categories_treeview.get_model()
        categories = ""
        for row in model:
            categories = "%s%s;" % (categories, row[0])
        return categories

    def set_editor_categories(self, entries_string):
        if not entries_string:
            entries_string = ""
        entries = entries_string.split(';')
        entries.sort()
        model = self.categories_treeview.get_model()
        model.clear()
        for entry in entries:
            entry = entry.strip()
            if len(entry) > 0:
                try:
                    description = category_descriptions[entry]
                except KeyError:
                    description = re.sub('(?!^)([A-Z]+)', r' \1', entry)
                model.append([entry, description])
                
    def get_editor_actions(self):
        # Must be returned as a string
        model = self.actions_treeview.get_model()
        actions = "\nActions="
        groups = "\n"
        if len(model) == 0:
            return None
        for row in model:
            show, name, displayed, executable = row[:]
            if show:
                actions = "%s%s;" % (actions, name)
            group = "[Desktop Action %s]\n" \
                    "Name=%s\n" \
                    "Exec=%s\n" \
                    "OnlyShowIn=Unity\n" % (name, displayed, executable)
            groups = "%s\n%s" % (groups, group)
        return actions + groups

    def set_editor_actions(self, action_groups):
        model = self.actions_treeview.get_model()
        model.clear()
        if not action_groups:
            return
        for name, displayed, command, show in action_groups:
            model.append([show, name, displayed, command])
            
    def set_value(self, key, value):
        if key in ['Name', 'Comment']:
            if not value:
                value = ""
            button, label, entry = self.widgets[key]
            if key == 'Name':
                format = "<big><b>%s</b></big>" % (value)
            else:
                format = "%s" % (value)
            tooltip = "%s <i>(Click to modify.)</i>" % (value)
            
            button.set_tooltip_markup(tooltip)
            entry.set_text(value)
            label.set_label(format)
        elif key == 'Filename':
            self.set_editor_filename(value)
        elif key == 'Categories':
            self.set_editor_categories(value)
        elif key == 'Type':
            self.values['Type'] = value
        else:
            widget = self.widgets[key]
            
            if isinstance(widget, Gtk.Button):
                if not value:
                    value = ""
                widget.set_label(value)
            elif isinstance(widget, Gtk.Label):
                if not value:
                    value = ""
                widget.set_label(value)
            elif isinstance(widget, Gtk.Entry):
                if not value:
                    value = ""
                widget.set_text(value)
            elif isinstance(widget, Gtk.Switch):
                if not value:
                    value = False
                widget.set_active(value)
            else:
                print("Unknown widget: %s" % key)
                
    def get_value(self, key):
        if key in ['Name', 'Comment']:
            button, label, entry = self.widgets[key]
            return entry.get_text()
        elif key == 'Icon':
            return self.values['icon-name']
        elif key == 'Type':
            return self.values[key]
        elif key == 'Categories':
            return self.get_editor_categories()
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

    def move_iter(self, widget, user_data):
        """Move the currently selected row up or down. If the neighboring row
        is expanded, make the selected row a child of the neighbor row.

        Keyword arguments:
        widget -- the triggering GtkWidget
        user_data -- list-packed parameters:
            treeview -- the GtkTreeview being modified
            relative_position -- 1 or -1, determines moving up or down

        """
        # Unpack the user data
        treeview, relative_position = user_data

        # Get the current selected row
        model = treeview.get_model()
        sel = treeview.get_selection().get_selected()
        if sel:
            selected_iter = sel[1]
            selected_type = model[selected_iter][2]

            # Move the row up if relative_position < 0
            if relative_position < 0:
                sibling = model.iter_previous(selected_iter)
            else:
                sibling = model.iter_next(selected_iter)

            if sibling:
                path = model.get_path(sibling)
                # If the selected row is not a directory and
                # the neighboring row is expanded, prepend/append to it.
                if selected_type != MenuItemTypes.DIRECTORY and \
                        treeview.row_expanded(path):
                    self.move_iter_down(treeview, selected_iter,
                                        sibling, relative_position)
                else:
                    # Otherwise, just move down/up
                    if relative_position < 0:
                        model.move_before(selected_iter, sibling)
                    else:
                        model.move_after(selected_iter, sibling)
            else:
                # If there is no neighboring row, move up a level.
                self.move_iter_up(treeview, selected_iter,
                                      relative_position)

    def move_iter_up(self, treeview, treeiter, relative_position):
        """Move the specified iter up one level."""
        model = treeview.get_model()
        sibling = model.iter_parent(treeiter)
        if sibling is not None:
            parent = model.iter_parent(sibling)
            row_data = model[treeiter][:]
            if relative_position < 0:
                new_iter = model.insert_before(parent,
                                               sibling,
                                               row_data)
            else:
                new_iter = model.insert_after(parent,
                                              sibling,
                                              row_data)
            model.remove(treeiter)
            path = model.get_path(new_iter)
            treeview.set_cursor(path)

    def move_iter_down(self, treeview, treeiter, parent_iter,
                             relative_position):
        """Move the specified iter down one level."""
        model = treeview.get_model()
        row_data = model[treeiter][:]
        if relative_position < 0:
            n_children = model.iter_n_children(parent_iter)
            sibling = model.iter_nth_child(parent_iter, n_children - 1)
            new_iter = model.insert_after(parent_iter, sibling, row_data)
        else:
            sibling = model.iter_nth_child(parent_iter, 0)
            new_iter = model.insert_before(parent_iter, sibling, row_data)
        model.remove(treeiter)
        path = model.get_path(new_iter)
        treeview.set_cursor(path)

    def on_add_launcher_cb(self, widget):
        print ('add launcher')

    def on_save_launcher_cb(self, widget):
        print ('[Desktop Entry]')
        print ('Version=1.0')
        for prop in ['Type', 'Name', 'GenericName', 'Comment', 'Icon', 'TryExec', 'Exec', 'Path', 'NoDisplay', 'Hidden', 'OnlyShowIn', 'NotShowIn', 'Categories', 'Keywords', 'MimeType', 'StartupWMClass', 'StartupNotify', 'Terminal', 'DBusActivatable']:
            value = self.get_value(prop)
            if value in [True, False]:
                value = str(value).lower()
            if value:
                print ('%s=%s' % (prop, value))
        actions = self.get_editor_actions()
        if actions:
            print (actions)

    def on_undo_cb(self, widget):
        print ('undo')

    def on_redo_cb(self, widget):
        print ('redo')

    def on_revert_cb(self, widget):
        print ('revert')

    def on_quit_cb(self, widget):
        # Emit the quit signal so the GtkApplication can handle it.
        self.emit('quit', True)

    def on_help_cb(self, widget):
        # Emit the help signal so the GtkApplication can handle it.
        self.emit('help', True)

    def on_about_cb(self, widget):
        # Emit the about signal so the GtkApplication can handle it.
        self.emit('about', True)


class Application(Gtk.Application):

    def __init__(self):
        Gtk.Application.__init__(self)

    def do_activate(self):
        self.win = MenulibreWindow(self)
        self.win.show_all()

        self.win.connect('about', self.about_cb)
        self.win.connect('help', self.help_cb)
        self.win.connect('quit', self.quit_cb)

        if self.win.app_menu_button:
            self.win.app_menu_button.set_menu_model(self.menu)
            self.win.app_menu_button.show_all()

    def do_startup(self):
        # start the application
        Gtk.Application.do_startup(self)

        self.menu = Gio.Menu()
        self.menu.append(_("Help"), "app.help")
        self.menu.append(_("About"), "app.about")
        self.menu.append(_("Quit"), "app.quit")

        if session == 'gnome':
            # Configure GMenu
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
        print ('help')
        pass

    def about_cb(self, widget, data=None):
        # Create and display the AboutDialog.
        aboutdialog = Gtk.AboutDialog()

        # Credits
        authors = ["Sean Davis"]
        documenters = ["Sean Davis"]

        # Populate the AboutDialog with all the relevant details.
        aboutdialog.set_title(_("About MenuLibre"))
        aboutdialog.set_program_name(_("MenuLibre"))
        aboutdialog.set_logo_icon_name("menulibre")
        aboutdialog.set_copyright(_("Copyright © 2012-2013 Sean Davis"))
        aboutdialog.set_authors(authors)
        aboutdialog.set_documenters(documenters)
        aboutdialog.set_website("https://launchpad.net/menulibre")

        # Connect the signal to destroy the AboutDialog when Close is clicked.
        aboutdialog.connect("response", self.about_close_cb)

        # Show the AboutDialog.
        aboutdialog.show()

    def about_close_cb(self, widget, response):
        widget.destroy()

    def quit_cb(self, widget, data=None):
        """Signal handler for closing the MenulibreWindow."""
        self.quit()
