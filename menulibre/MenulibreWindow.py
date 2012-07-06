# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2012 Sean Davis <smd.seandavis@gmail.com>
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

import os

import gettext
from gettext import gettext as _
gettext.textdomain('menulibre')

from gi.repository import Gtk, Gdk, GdkPixbuf, GObject # pylint: disable=E0611
import logging
logger = logging.getLogger('menulibre')

from menulibre_lib import Window, IconTheme, Applications
from menulibre.AboutMenulibreDialog import AboutMenulibreDialog

icon_theme = IconTheme.CurrentTheme()
IconSize = Gtk.icon_size_lookup(Gtk.IconSize.SMALL_TOOLBAR)

home = os.getenv('HOME')

Gtk.IconSize.UNITY = Gtk.icon_size_register('UNITY', 128, 128)

# See menulibre_lib.Window.py for more details about how this class works
class MenulibreWindow(Window):
    __gtype_name__ = "MenulibreWindow"
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(MenulibreWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutMenulibreDialog

		self.sudo = os.getuid() == 0
		self.apps = Applications.get_applications()
        self.categories = { 'AudioVideo': ['Multimedia', 'applications-multimedia', -7, []],
                            'Development': ['Development', 'applications-development', -2, []],
                            'Education': ['Education', 'applications-education', -3, []],
                            'Game': ['Games', 'applications-games', -4, []],
                            'Graphics': ['Graphics', 'applications-graphics', -5, []],
                            'Network': ['Internet', 'applications-internet', -6, []],
                            'Office': ['Office', 'applications-office', -8, []],
                            'Other': ['Other', 'applications-other', -9, []],
                            'Settings': ['Settings', 'preferences-desktop', -10, []],
                            'System': ['System', 'applications-system', -11, []],
                            'Utility': ['Accessories', 'applications-accessories', -1, []],
                            'WINE': ['WINE', 'wine', -12, []]}
        
        #self.icon_cache = dict()
        self.undo_stack = []
        self.redo_stack = []

        self.show_wine = os.path.isdir('/usr/share/wine')

		# Locks
        self.lock_breadcrumb = False
        self.iconview_single = False
        self.update_pending = False
        self.quicklist_modified = False
        self.editor_changed = False
        self.in_history = False
        
        # Variables
        self.quicklist_format = None
        self.last_editor = ''
        self.last_height = 0
        self.last_width = 0
        self.catselection_hover = {'x': 0, 'y': 0, 'path': None}
        self.appselection_hover = {'x': 0, 'y': 0, 'path': None}
        
        self.get_interface()
        self.load_category_into_iconview(None)
        self.set_focus(self.catselection_iconview)
        self.catselection_iconview.select_path(Gtk.TreePath.new_from_string('0'))
        
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        
    def get_interface(self):
        """Load all of the interface elements into memory so that we can
        access and interact with them."""
      # MenuLibre Window (Gtk.Window)
        # -- Toolbar (Gtk.Toolbar) -- #
        self.toolbar = self.builder.get_object('toolbar')
        context = self.toolbar.get_style_context()
        context.add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        self.toolbar_addnew = self.builder.get_object('toolbar_addnew')
        self.toolbar_save = self.builder.get_object('toolbar_save')
        self.toolbar_undo = self.builder.get_object('toolbar_undo')
        self.toolbar_redo = self.builder.get_object('toolbar_redo')
        self.toolbar_revert = self.builder.get_object('toolbar_revert')
        
        # -- Search Bar (Gtk.Entry) -- #
        self.entry_search = self.builder.get_object('entry_search')
        
        # -- Breadcrumbs (Gtk.Box) -- #
        self.breadcrumbs = self.builder.get_object('breadcrumbs')
        self.breadcrumb_home = self.builder.get_object('breadcrumb_home')
        self.breadcrumb_category = self.builder.get_object('breadcrumb_category')
        self.breadcrumb_category_image = self.builder.get_object('breadcrumb_category_image')
        self.breadcrumb_category_label = self.builder.get_object('breadcrumb_category_label')
        self.breadcrumb_application = self.builder.get_object('breadcrumb_application')
        self.breadcrumb_application_image = self.builder.get_object('breadcrumb_application_image')
        self.breadcrumb_application_label = self.builder.get_object('breadcrumb_application_label')
        
        # -- Application Selection (Gtk.IconView) -- #
        self.catselection = self.builder.get_object('catselection_scrolled')
        self.catselection_iconview = self.builder.get_object('catselection_iconview')
        self.catselection_iconview.add_events(Gdk.EventType.MOTION_NOTIFY)
        self.catselection_iconview.connect('button-press-event', self.on_catselection_button_press_event)
        self.appselection = self.builder.get_object('appselection_scrolled')
        self.appselection_iconview = self.builder.get_object('appselection_iconview')
        self.appselection_iconview.add_events(Gdk.EventType.MOTION_NOTIFY)
        self.appselection_iconview.connect('button-press-event', self.on_appselection_button_press_event)
        self.appselection_search_fail = self.builder.get_object('appselection_search_fail')
        self.appselection_search_all_button = self.builder.get_object('appselection_search_all_button')
        
        # -- Launcher Settings (Gtk.Notebook) -- #
        self.appsettings_notebook = self.builder.get_object('appsettings_notebook')
        self.appsettings_general = self.builder.get_object('appsettings_general')
        self.appsettings_quicklists = self.builder.get_object('appsettings_quicklists')
        self.appsettings_editor = self.builder.get_object('appsettings_editor')
        
        self.statusbar = self.builder.get_object('statusbar_label')
        
        # -- General Settings (Notebook Page 0) -- #
        self.label_generalsettings = self.builder.get_object('label_generalsettings')
        self.general_icon_button = self.builder.get_object('general_icon_button')
        self.general_icon_image = self.builder.get_object('general_icon_image')
        self.general_name_button = self.builder.get_object('general_name_button')
        self.general_name_label = self.builder.get_object('general_name_label')
        self.general_name_modify_box = self.builder.get_object('general_name_modify_box')
        self.general_name_entry = self.builder.get_object('general_name_modify_entry')
        self.general_comment_button = self.builder.get_object('general_comment_button')
        self.general_comment_label = self.builder.get_object('general_comment_label')
        self.general_comment_modify_box = self.builder.get_object('general_comment_modify_box')
        self.general_comment_entry = self.builder.get_object('general_comment_modify_entry')
        self.general_command_entry = self.builder.get_object('general_command_entry')
        self.general_path_entry = self.builder.get_object('general_path_entry')
        self.general_terminal_switch = self.builder.get_object('general_terminal_switch')
        self.general_terminal_switch.connect('notify::active', self.on_general_terminal_switch_toggled)
        self.general_startupnotify_switch = self.builder.get_object('general_startupnotify_switch')
        self.general_startupnotify_switch.connect('notify::active', self.on_general_startupnotify_switch_toggled)
        self.general_nodisplay_switch = self.builder.get_object('general_nodisplay_switch')
        self.general_nodisplay_switch.connect('notify::active', self.on_general_nodisplay_switch_toggled)
        self.general_filename_label = self.builder.get_object('general_filename_label')
        
        # Categories
        self.categories_expander = self.builder.get_object('categories_expander')
        self.categories_accessories = self.builder.get_object('categories_accessories')
        self.categories_development = self.builder.get_object('categories_development')
        self.categories_education = self.builder.get_object('categories_education')
        self.categories_games = self.builder.get_object('categories_games')
        self.categories_graphics = self.builder.get_object('categories_graphics')
        self.categories_internet = self.builder.get_object('categories_internet')
        self.categories_multimedia = self.builder.get_object('categories_multimedia')
        self.categories_office = self.builder.get_object('categories_office')
        self.categories_settings = self.builder.get_object('categories_settings')
        self.categories_system = self.builder.get_object('categories_system')
        self.categories_wine = self.builder.get_object('categories_wine')
        self.categories_wine.set_visible(self.show_wine)
        
        # -- Quicklists (Notebook Page 1) -- #
        self.quicklists_treeview = self.builder.get_object('quicklists_treeview')
        self.quicklists_add = self.builder.get_object('quicklists_add')
        self.quicklists_remove = self.builder.get_object('quicklists_remove')
        self.quicklists_move_up = self.builder.get_object('quicklists_move_up')
        self.quicklists_move_down = self.builder.get_object('quicklists_move_down')
        
        cell_toggle = Gtk.CellRendererToggle()
        cell_toggle.connect("toggled", self.on_quicklist_toggled)
        tvcolumn = Gtk.TreeViewColumn(_("Show"), cell_toggle, active=0)
        self.quicklists_treeview.append_column(tvcolumn)
        
        tvcolumn = Gtk.TreeViewColumn('Shortcut Name')
        text_render_name = Gtk.CellRendererText()
        text_render_name.set_property('editable', True)
        text_render_name.connect('edited', self.shortcut_edited_cb, (self.quicklists_treeview, 1))
        tvcolumn.pack_start(text_render_name, True)
        tvcolumn.add_attribute(text_render_name, 'text', 1)
        self.quicklists_treeview.append_column(tvcolumn)
        
        tvcolumn = Gtk.TreeViewColumn('Displayed Name')
        text_render_name = Gtk.CellRendererText()
        text_render_name.set_property('editable', True)
        text_render_name.connect('edited', self.edited_cb, (self.quicklists_treeview, 2))
        tvcolumn.pack_start(text_render_name, True)
        tvcolumn.add_attribute(text_render_name, 'text', 2)
        self.quicklists_treeview.append_column(tvcolumn)
        
        tvcolumn = Gtk.TreeViewColumn('Command')
        text_render_command = Gtk.CellRendererText()
        text_render_command.set_property('editable', True)
        text_render_command.connect('edited', self.edited_cb, (self.quicklists_treeview, 3))
        tvcolumn.pack_start(text_render_command, True)
        tvcolumn.add_attribute(text_render_command, 'text', 3)
        self.quicklists_treeview.append_column(tvcolumn)
        
        # -- Editor (Notebook Page 2) -- #
        self.editor_textview = self.builder.get_object('editor_textview')
        buffer = self.editor_textview.get_buffer()
        buffer.connect('changed', self.on_editor_buffer_changed)
        
      # Icon Selection Dialog 1 (Select and Preview)
        self.iconselection_dialog = self.builder.get_object('iconselection_dialog1')
        self.iconselection_radio_theme = self.builder.get_object('iconselection_radio_theme')
        self.iconselection_radio_image = self.builder.get_object('iconselection_radio_image')
        self.iconselection_theme = self.builder.get_object('iconselection_theme')
        self.iconselection_theme_entry = self.builder.get_object('iconselection_theme_entry')
        self.iconselection_theme_browse = self.builder.get_object('iconselection_theme_browse')
        self.iconselection_image = self.builder.get_object('iconselection_image')
        self.preview128 = self.builder.get_object('preview128')
        self.preview48 = self.builder.get_object('preview48')
        self.preview32 = self.builder.get_object('preview32')
        self.preview24 = self.builder.get_object('preview24')
        self.preview16 = self.builder.get_object('preview16')
        self.set_preview_from_name('image-missing')
    
      # Icon Selection Dialog 2 (All Icons)
        self.iconselection_dialog_all = self.builder.get_object('iconselection_dialog2')
        self.iconselection_search = self.builder.get_object('iconselection_dialog2_search')
        self.iconselection_treeview = self.builder.get_object('iconselection_treeview')
        
        self.iconselection_treeview.append_column(Gtk.TreeViewColumn(_('Image'),
                Gtk.CellRendererPixbuf(), pixbuf=0))
        self.iconselection_treeview.append_column(Gtk.TreeViewColumn(_('Name'), 
                Gtk.CellRendererText(), text=1))

                
  # Events
    def on_menulibre_window_key_press_event(self, widget, event):
        """Enables some high-quality keyboard navigation."""
        keyname = Gdk.keyval_name(event.keyval)
        if keyname == 'BackSpace' and not self.entry_search.has_focus():
            if self.breadcrumb_category.get_active():
                self.breadcrumb_home.activate()
            elif self.breadcrumb_application.get_active() and self.appsettings_notebook.has_focus():
                self.breadcrumb_category.activate()
        
    def on_window_check_resize(self, widget, something):
        """Adjust IconView icons when the window is resized."""
        allocation = widget.get_allocation()
        height = allocation.height
        width = allocation.width
        if height != self.last_height or width != self.last_width:
            try:
                cat = self.catselection_iconview.get_model()
                model = Gtk.ListStore(GdkPixbuf.Pixbuf, str, int)
                self.catselection_iconview.set_model(model)
                for i in cat:
                    img = i[0]
                    string = i[1]
                    id = i[2]
                    model.append([img, string, id])
                    
                del cat
            except TypeError:
                pass
                
            try:
                app = self.appselection_iconview.get_model()
                model = Gtk.ListStore(GdkPixbuf.Pixbuf, str, int)
                self.appselection_iconview.set_model(model)
                for i in app:
                    img = i[0]
                    string = i[1]
                    id = i[2]
                    model.append([img, string, id])
                    
                del app
            except TypeError:
                pass
                
            self.last_height = height
            self.last_width = width
   
    def on_toolbar_addnew_clicked(self, button):
        """When the Add New toolbar icon is clicked, go to the
        application editor and New Launcher details."""
        self.appsettings_notebook.set_current_page(0)
        self.set_position(Gtk.WindowPosition.NONE)
        if self.iconview_single:
            self.iconview_single = False
            return
        self.iconview_single = True
        self.lock_breadcrumb = True

        self.in_history = True
        del self.undo_stack[:]
        del self.redo_stack[:]
        self.set_undo_enabled(False)
        self.set_redo_enabled(False)
        
        self.new_launcher()
        
        self.in_history = False
        
        self.lock_breadcrumb = False
    
    def on_toolbar_save_clicked(self, button):
        """When the Save toolbar icon is clicked, save the desktop file.
        If modifying a system entry while not sudo-powered, create a new
        launcher in /home/USERNAME/.local/share/applications."""
        filename = self.get_application_filename()
        text = self.get_application_text()
        try:
            openfile = open(filename, 'w')
            openfile.write(text)
        except IOError:
            filename = os.path.split(filename)[1]
            filename = os.path.join( home, '.local', 'share', 'applications', filename )
            if not os.path.isdir( os.path.join( home, '.local', 'share', 'applications') ):
                filepath = home
                for path in ['.local', 'share', 'applications']:
                    try:
                        filepath = os.path.join(filepath, path)
                        os.mkdir(filepath)
                    except OSError:
                        pass
            openfile = open(filename, 'w')
            openfile.write(text)
            self.set_application_filename(filename)
            appid = len(self.apps)
            newapp = Applications.Application(filename)
            newapp.set_id(appid)
            self.apps[appid] = newapp
        openfile.close()
        del self.undo_stack[:]
        del self.redo_stack[:]
        self.set_undo_enabled(False)
        self.set_redo_enabled(False)
        self.set_save_enabled(False)
        self.set_revert_enabled(False)
    
    def on_toolbar_undo_clicked(self, button):
		"""When the Undo toolbar icon is clicked, undo the last done
		action."""
        self.undo()
    
    def on_toolbar_redo_clicked(self, button):
		"""When the Redo toolbar icon is clicked, redo the last undone
		action."""
        self.redo()
    
    def on_toolbar_revert_clicked(self, button):
		"""When the Revert toolbar icon is clicked, restore the launcher
		to the last saved state."""
        data = self.undo_stack[0]
        del self.undo_stack[:]
        del self.redo_stack[:]
        self.set_application_text( data )
        self.set_undo_enabled(False)
        self.set_redo_enabled(False)
        self.set_save_enabled(False)
        self.set_revert_enabled(False)
        
    def on_entry_search_activate(self, widget):
        """When ENTER is pressed in the search entry, set the focus on
        the AppSelection IconView."""
        if len(widget.get_text()) > 0:
            self.breadcrumb_application.activate()
            self.appselection_iconview.select_path(Gtk.TreePath.new_from_string('0'))
            self.appselection_iconview.grab_focus()
    
    def on_entry_search_changed(self, widget):
		"""When text is entered into the search entry, run a query and
		display the results."""
        text = widget.get_text()
        self.set_position(Gtk.WindowPosition.NONE)
        
        if text == '':
            if self.last_cat == None:
                self.breadcrumb_category.set_visible(False)
            self.show_catselection()
            self.breadcrumb_category.set_visible(False)
            self.breadcrumb_application.set_visible(False)
            widget.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, None)
            self.load_category_into_iconview(self.last_cat)
            self.last_cat = None
        else:
            self.breadcrumb_application.set_visible(False)
            category = None
            self.last_cat = None
            if self.breadcrumb_category.get_active():
                search_type = self.entry_search.get_placeholder_text().replace('Search ', '')
                for cat in self.categories:
                    if self.categories[cat][0] == search_type:
                        self.last_cat = category = cat
            widget.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, 'gtk-clear')
            self.show_search_results(text, category)
            
    def on_entry_search_icon_press(self, widget, button, event):
		"""When the clear icon is pressed in the search widget, clear
		the search query and return to the last location."""
        if button == Gtk.EntryIconPosition.SECONDARY:
            self.entry_search.set_text('')
    
    def on_breadcrumb_home_clicked(self, button):
		"""When the Home breadcrumb is clicked, change to the Home 
		page."""
        if not self.lock_breadcrumb:
            self.entry_search.set_placeholder_text('Search Applications')
            self.lock_breadcrumb = True
            self.breadcrumb_application.set_active(False)
            self.breadcrumb_category.set_active(False) 
            self.lock_breadcrumb = False
            self.show_catselection()
            self.on_catselection_iconview_selection_changed()
            self.set_focus(self.catselection_iconview)
            if len(self.catselection_iconview.get_selected_items()) == 0:
                self.catselection_iconview.select_path(Gtk.TreePath.new_from_string("0"))
        
    def on_breadcrumb_category_clicked(self, button):
		"""When the Category breadcrumb is clicked, change to the 
		category view page."""
        if not self.lock_breadcrumb:
            label = self.breadcrumb_category_label.get_label()
            self.entry_search.set_placeholder_text('Search %s' % label)
            self.lock_breadcrumb = True
            self.breadcrumb_application.set_active(False)
            self.breadcrumb_home.set_active(False)
            self.lock_breadcrumb = False
            self.show_appselection()
            self.on_appselection_iconview_selection_changed()
            if not self.entry_search.has_focus():
                self.set_focus(self.appselection_iconview)
            if len(self.appselection_iconview.get_selected_items()) == 0:
                self.appselection_iconview.select_path(Gtk.TreePath.new_from_string("0"))
            
    def on_breadcrumb_application_clicked(self, button):
		"""When the Application breadcrumb is clicked, change to the
		launcher editor page."""
        if not self.lock_breadcrumb:
            self.entry_search.set_placeholder_text('Search Applications')
            self.lock_breadcrumb = True
            self.appsettings_notebook.show()
            self.appselection.hide()
            self.appselection_search_fail.hide()
            self.breadcrumb_category.set_active(False)
            self.breadcrumb_home.set_active(False)
            self.lock_breadcrumb = False
            self.show_appsettings()
            self.statusbar.set_label(self.get_application_filename())
            self.set_focus(self.appsettings_notebook)
            
    def on_catselection_iconview_motion_notify_event(self, widget, event):
        """Implementation of on-hover event for IconView."""
        path = self.catselection_iconview.get_path_at_pos(int(event.x), int(event.y))
        if path != None:
            self.catselection_iconview.select_path(path)
                        
    def on_catselection_button_press_event(self, widget, event):
        """Enables single-click in the category selection view."""
        self.iconview_single = False
        path = self.catselection_iconview.get_path_at_pos(event.x, event.y)
        self.on_catselection_iconview_item_activated(widget, path)
            
    def on_catselection_iconview_item_activated(self, widget, index):
		"""When an item is activated in the Category Selection view, 
		load the category's applications in the category view."""
        self.set_position(Gtk.WindowPosition.NONE)
        if self.iconview_single:
            self.iconview_single = False
            return
        self.iconview_single = True
        self.lock_breadcrumb = True
        try:
            model = widget.get_model()
            selection_id = model[index][2]
            if selection_id == -9001:
                self.load_category_into_iconview('')
            else:
                for cat in self.categories:
                    if selection_id == self.categories[cat][2]:
                        self.load_category_into_iconview(cat)
            self.show_appselection()
        except:
            pass
        self.lock_breadcrumb = False
        self.set_focus(self.appselection_iconview)
        
    def on_appselection_iconview_motion_notify_event(self, widget, event):
        """Implementation of on-hover event for IconView."""
        path = self.appselection_iconview.get_path_at_pos(int(event.x), int(event.y))
        if path != None:
            self.appselection_iconview.select_path(path)
        
    def on_appselection_button_press_event(self, widget, event):
        """Enables single-click in the application selection view."""
        self.iconview_single = False
        path = self.appselection_iconview.get_path_at_pos(event.x, event.y)
        self.on_appselection_iconview_item_activated(widget, path)
        
    def on_appselection_iconview_item_activated(self, widget, index):
		"""When an item is activated in the Application Selection view,
		load the application into the launcher editor view."""
        self.appsettings_notebook.set_current_page(0)
        self.set_position(Gtk.WindowPosition.NONE)
        if self.iconview_single:
            self.iconview_single = False
            return
        self.iconview_single = True
        self.lock_breadcrumb = True
        try:
            model = widget.get_model()
            selection_id = model[index][2]

            self.in_history = True
            del self.undo_stack[:]
            del self.redo_stack[:]
            self.set_undo_enabled(False)
            self.set_redo_enabled(False)
            
            if selection_id == 1337:
                self.new_launcher()
            else:
                self.set_categories_expanded(False)
                self.set_breadcrumb_application(selection_id)
                app = self.apps[selection_id]
                
                # General Settings
                self.set_application_icon( app.get_icon()[1], Gtk.IconSize.DIALOG )
                self.set_application_name( app.get_name() )
                self.set_application_comment( app.get_comment() )
                self.set_application_command( app.get_exec() )
                self.set_application_path( app.get_path() )
                self.set_application_terminal( app.get_terminal() )
                self.set_application_startupnotify( app.get_startupnotify() )
                self.set_application_hidden( app.get_hidden() )
                self.set_application_categories( app.get_categories() )
                self.set_application_filename( app.get_filename() )
                
                # Quicklists
                self.quicklist_format = app.get_quicklist_format()
                self.set_application_quicklists( app.get_actions() )
                
                # Editor
                self.set_application_text( app.get_original() )
                self.show_appsettings()
                self.in_history = False
                self.last_editor = app.get_original()
        except (IndexError, TypeError):
            pass
        self.lock_breadcrumb = False
        self.set_focus(self.appsettings_notebook)
        
    def on_catselection_iconview_selection_changed(self, widget=None):
		"""When an item is selected in the category selection view, 
		change the statusbar to the category name."""
		widget = self.catselection_iconview
        try:
            model = widget.get_model()
            index = int(widget.get_selected_items()[0].to_string())
            label =  model[index][1]
            self.statusbar.set_label(label)
        except (IndexError, TypeError):
            self.statusbar.set_label('')
        
    def on_appselection_iconview_selection_changed(self, widget=None):
		"""When an item is selected in the application selection view, 
		change the statusbar to the application comment."""
		widget = self.appselection_iconview
        try:
            model = widget.get_model()
            index = int(widget.get_selected_items()[0].to_string())
            label =  model[index][3]
            self.statusbar.set_label(label)
        except (IndexError, TypeError):
            self.statusbar.set_label('')
    
    def on_appselection_search_all_button_clicked(self, button):
		"""When an item cannot be found and the Search All button is
		available and clicked, search with no filters."""
        pass 
    
    def on_appsettings_notebook_switch_page(self, notebook, page, pageno):
		"""When the notebook page is changed, reset the text editor
		cursor to the top."""
        buffer = self.editor_textview.get_buffer()
        buffer.place_cursor( buffer.get_start_iter() )
    
    def on_general_icon_button_clicked(self, button):
		"""When the Application Icon button is clicked, show the icon
		selection dialog."""
        self.iconselection_dialog.show_all()
        self.iconselection_dialog.run()
        self.iconselection_dialog.hide()
    
    def on_general_name_button_clicked(self, button):
		"""When the Application Name button is clicked, reveal the name
		editor."""
        self.show_general_name_editor()
        
    def on_general_name_modify_entry_activate(self, widget):
		"""When the Application Name entry is activated, accept the 
		changes."""
        self.general_name_modify_accept()
        
    def on_general_name_modify_entry_key_press_event(self, widget, event):
		"""If the user presses the ESCAPE key while in the name entry, 
		reject the changes."""
        if Gdk.keyval_name(event.get_keyval()[1]) == 'Escape':
            self.general_name_modify_reject()
    
    def on_general_name_modify_cancel_clicked(self, button):
		"""If the user clicks the entry cancel button, reject the 
		changes."""
        self.general_name_modify_reject()
    
    def on_general_name_modify_confirm_clicked(self, button):
		"""If the user clicks the entry OK button, accept the changes."""
        self.general_name_modify_accept()
    
    def on_general_comment_button_clicked(self, button):
		"""When the Application Comment button is clicked, reveal the 
		comment editor."""
        self.show_general_comment_editor()
        
    def on_general_comment_modify_entry_activate(self, widget):
		"""When the Application Comment entry is activated, accept the 
		changes."""
        self.general_comment_modify_accept()
        
    def on_general_comment_modify_entry_key_press_event(self, widget, event):
		"""If the user presses the ESCAPE key while in the comment
		entry, reject the changes."""
        if Gdk.keyval_name(event.get_keyval()[1]) == 'Escape':
            self.general_comment_modify_reject()
    
    def on_general_comment_modify_cancel_clicked(self, button):
		"""If the user clicks the entry cancel button, reject the 
		changes."""
        self.general_comment_modify_reject()
    
    def on_general_comment_modify_confirm_clicked(self, button):
		"""If the user clicks the entry OK button, accept the changes."""
        self.general_comment_modify_accept()
        
    def on_general_command_entry_changed(self, widget):
		"""Update the editor when the Command entry is changed."""
        self.update_editor()
    
    def on_general_command_browse_clicked(self, button):
		"""Show a file chooser dialog when the Command browse button
		is clicked, and set the Command entry to the selected file."""
        dialog = Gtk.FileChooserDialog("Select an executable", self, 0, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
        dialog.show()
        response = dialog.run()
        dialog.hide()
        if response == Gtk.ResponseType.OK:
            self.set_application_command( dialog.get_filename() )
    
    def on_general_path_entry_changed(self, widget):
		"""Update the editor when the Path entry is changed."""
        self.update_editor()
    
    def on_general_path_browse_clicked(self, button):
		"""Show a folder chooser dialog when the Path browse button is 
		clicked, and set the Path entry to the selected folder."""
        dialog = Gtk.FileChooserDialog("Select an executable", self, Gtk.FileChooserAction.SELECT_FOLDER, buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
        dialog.show()
        response = dialog.run()
        dialog.hide()
        if response == Gtk.ResponseType.OK:
            self.set_application_path( dialog.get_filename() )
    
    def on_general_terminal_switch_toggled(self, widget, state):
		"""Update the editor when the Terminal switch is toggled."""
        self.update_editor()
    
    def on_general_startupnotify_switch_toggled(self, widget, state):
		"""Update the editor when the StartupNotify switch is toggled."""
        self.update_editor()
        
    def on_general_nodisplay_switch_toggled(self, widget, state):
		"""Update the editor with the NoDisplay switch is toggled."""
        self.update_editor()
            
    def on_quicklists_treeview_cursor_changed(self, widget):
		"""Required to update the editor when modified, as opposed to
		cursor changed."""
        if self.quicklist_modified:
            self.update_editor()
        self.quicklist_modified = False
    
    def on_quicklist_toggled(self, widget, path):
		"""When a quicklist item is toggled, enable the toggle and then
		update the editor."""
        model = self.quicklists_treeview.get_model()
        model[path][0] = not model[path][0]
        self.update_editor()

    def on_quicklist_add_clicked(self, button):
		"""When the Quicklist Add button is clicked, add a new, unique
		quicklist item."""
        self.quicklist_modified = True
        quicklists = self.get_application_quicklists()
        listmodel = self.quicklists_treeview.get_model()
        if len(listmodel) == 0:
            self.quicklist_format = 'actions'
        shortcut_name = self.get_quicklist_unique_shortcut_name(quicklists, 'NewShortcut', 0)
        
        listmodel.append([False, shortcut_name, 'New Shortcut', ''])
        self.quicklists_treeview.set_cursor_on_cell( Gtk.TreePath.new_from_string( str(len(listmodel)-1) ), None, None, False )
    
    def on_quicklist_remove_clicked(self, button):
		"""When the Quicklist Remove button is clicked, remove the 
		currently selected quicklist item."""
        if len(self.quicklists_treeview.get_model()) > 0:
            self.quicklist_modified = True
            tree_sel = self.quicklists_treeview.get_selection()
            (treestore, treeiter) = tree_sel.get_selected()
            treestore.remove(treeiter)
    
    def on_quicklist_move_up_clicked(self, button):
		"""When the Quicklist Move Up button is clicked, move the 
		currently selected quicklist item up in the treeview."""
        if len(self.quicklists_treeview.get_model()) > 0:
            self.quicklist_modified = True
            tree_sel = self.quicklists_treeview.get_selection()
            (treestore, treeiter) = tree_sel.get_selected()
            path = treestore.get_path(treeiter)
            if int(str(path)) > 0:
                up = treestore.iter_previous(treeiter)
                enabled = treestore.get_value(treeiter, 0)
                shortcut_name = treestore.get_value(treeiter, 1)
                displayed_name = treestore.get_value(treeiter, 2)
                command = treestore.get_value(treeiter, 3)
                treestore.remove(treeiter)
                treestore.insert_before(up, [enabled, shortcut_name, displayed_name, command])
                self.quicklists_treeview.set_cursor_on_cell( Gtk.TreePath.new_from_string( str(int(str(path))-1) ), None, None, False )
    
    def on_quicklist_move_down_clicked(self, button):
		"""When the Quicklist Move Down button is clicked, move the 
		currently selected quicklist item down in the treeview."""
        if len(self.quicklists_treeview.get_model()) > 0:
            self.quicklist_modified = True
            tree_sel = self.quicklists_treeview.get_selection()
            (treestore, treeiter) = tree_sel.get_selected()
            path = treestore.get_path(treeiter)
            if int(str(path)) < len(treestore)-1:
                down = treestore.iter_next(treeiter)
                enabled = treestore.get_value(treeiter, 0)
                shortcut_name = treestore.get_value(treeiter, 1)
                displayed_name = treestore.get_value(treeiter, 2)
                command = treestore.get_value(treeiter, 3)
                treestore.remove(treeiter)
                treestore.insert_after(down, [enabled, shortcut_name, displayed_name, command])
                self.quicklists_treeview.set_cursor_on_cell( Gtk.TreePath.new_from_string( str(int(str(path))+1) ), None, None, False )
    
    def on_iconselection_radio_theme_toggled(self, radio_button):
		"""When the theme radio button is toggled, toggle the theme 
		selection button as well."""
        self.iconselection_theme.set_sensitive( radio_button.get_active() )
        if radio_button.get_active():
            self.set_preview_from_name(self.iconselection_theme_entry.get_text())
    
    def on_iconselection_radio_image_toggled(self, radio_button):
		"""When the image radio button is toggled, toggle the image
		selection button as well."""
        self.iconselection_image.set_sensitive( radio_button.get_active() )
        if radio_button.get_active():
            self.set_preview_from_filename( self.iconselection_image.get_filename() )
        
    def on_iconselection_theme_entry_changed(self, widget):
		"""When the theme entry is modified, set the preview to the new
		icon."""
        self.set_preview_from_name( self.iconselection_theme_entry.get_text() )
    
    def on_iconselection_theme_browse_clicked(self, button):
		"""When the theme browse button is clicked, display the icon 
		selection dialog, and set the icon from the selected icon."""
        self.iconselection_dialog_all.show_all()
        task = self.load_iconselection_icons()
        GObject.idle_add(task.next)
        self.iconselection_dialog_all.run()
        self.iconselection_dialog_all.hide()
        liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
        self.iconselection_treeview.set_model(liststore)
    
    def on_iconselection_image_file_set(self, widget):
        """When the an image is selected from the icon selection dialog,
        set the icon image entry to its filename."""
        filename = widget.get_filename()
        self.set_preview_from_filename(filename)
    
    def on_iconselection_dialog1_response(self, widget, response):
        """When OK is pressed in the primary icon selection dialog, 
        set the application icon to the newly selected image."""
        if response == 1:
            if self.iconselection_radio_theme.get_active():
                name = self.iconselection_theme_entry.get_text()
                self.set_application_icon(name, Gtk.IconSize.DIALOG)
            elif self.iconselection_radio_image.get_active():
                filename = self.iconselection_image.get_filename()
                self.set_application_icon(filename, Gtk.IconSize.DIALOG)
            self.update_editor()
    
    def on_iconselection_dialog2_response(self, widget, response):
        """When OK is pressed in the secondary icon selection dialog, 
        set the selected icon entry to the new icon name."""
        if response == 1:
            tree_sel = self.iconselection_treeview.get_selection()
            (treestore, treeiter) = tree_sel.get_selected()
            name = treestore[treeiter][1]
            self.iconselection_theme_entry.set_text(name)
    
    def on_iconselection_dialog2_search_icon_press(self, widget, pos, more):
        """When the clear icon is pressed in the icon selection search,
        clear the search terms."""
        self.iconselection_search.set_text('')
    
    def on_iconselection_dialog2_search_changed(self, widget):
        """When the icon selection search terms are modified, update
        the search filter and display matching results."""
        if widget.get_text() == '':
            widget.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, None)
        else:
            widget.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, 'gtk-clear')
        self.iconselection_filter.refilter()
        
    def iconselection_filter_func(self, model, iter, user_data):
        """Filter function rules for the icon selection search."""
        return self.iconselection_search.get_text() in model[iter][1]
        
    # Categories
    def on_categories_accessories_toggled(self, widget):
        """Update the editor when a category is toggled."""
        self.update_editor()
        
    def on_categories_development_toggled(self, widget):
        """Update the editor when a category is toggled."""
        self.update_editor()
        
    def on_categories_education_toggled(self, widget):
        """Update the editor when a category is toggled."""
        self.update_editor()
        
    def on_categories_games_toggled(self, widget):
        """Update the editor when a category is toggled."""
        self.update_editor()
        
    def on_categories_graphics_toggled(self, widget):
        """Update the editor when a category is toggled."""
        self.update_editor()
        
    def on_categories_internet_toggled(self, widget):
        """Update the editor when a category is toggled."""
        self.update_editor()
        
    def on_categories_multimedia_toggled(self, widget):
        """Update the editor when a category is toggled."""
        self.update_editor()
        
    def on_categories_office_toggled(self, widget):
        """Update the editor when a category is toggled."""
        self.update_editor()
        
    def on_categories_settings_toggled(self, widget):
        """Update the editor when a category is toggled."""
        self.update_editor()
        
    def on_categories_system_toggled(self, widget):
        """Update the editor when a category is toggled."""
        self.update_editor()
        
    def on_categories_wine_toggled(self, widget):
        """Update the editor when a category is toggled."""
        self.update_editor()
    # -- End Events -------------------------------------------------- #
    
  # Helper Functions
    def set_undo_enabled(self, enabled):
        """Toggle undo functionality enabled."""
        self.toolbar_undo.set_sensitive(enabled)
        
    def get_undo_enabled(self):
        """Return undo functionality enabled."""
        return self.toolbar_undo.get_sensitive()
        
    def set_redo_enabled(self, enabled):
        """Toggle redo functionality enabled."""
        self.toolbar_redo.set_sensitive(enabled)
        
    def get_redo_enabled(self):
        """Return redo functionality enabled."""
        return self.toolbar_redo.get_sensitive()
        
    def set_save_enabled(self, enabled):
        """Toggle save functionality enabled."""
        self.toolbar_save.set_sensitive(enabled)
        
    def get_save_enabled(self):
        """Return save functionality enabled."""
        return self.toolbar_save.get_sensitive()
    
    def set_revert_enabled(self, enabled):
        """Toggle revert functionality enabled."""
        self.toolbar_revert.set_sensitive(enabled)
        
    def get_revert_enabled(self):
        """Return revert functionality enabled."""
        return self.toolbar_revert.get_sensitive()
  
    def set_application_icon(self, icon_name, size):
        """Set the application icon."""
        if icon_name == None:
            icon_name = 'application-default-icon'
        if os.path.isfile( icon_name ):
            self.general_icon_image.set_from_pixbuf( icon_theme.get_theme_GdkPixbuf(icon_name, size) )
            self.image_filename = icon_name
            self.iconselection_image.set_filename(icon_name)
            self.iconselection_radio_image.set_active(True)
        else:
            self.general_icon_image.set_from_icon_name( icon_name, size )
            self.iconselection_radio_theme.set_active(True)
            self.iconselection_theme_entry.set_text( icon_name )
    
    def get_application_icon(self):
        """Return the application icon name."""
        icon_name = self.general_icon_image.get_icon_name()
        if icon_name[0]: 
            return icon_name[0]
        elif self.iconselection_radio_image.get_active():
            return self.iconselection_image.get_filename()
        else:
            return self.image_filename
  
    def set_application_name(self, name):    
        """Set the application name label and entry."""
        if name == None:
            name = ''
        name = name.replace('&', '&amp;')
        self.general_name_label.set_markup( '<big><b>%s</b></big>' % name )
        self.general_name_entry.set_text( name )
        self.breadcrumb_application_label.set_label(name)
    
    def get_application_name(self):
        """Return the application name extracted from the button label."""
        return self.general_name_label.get_label()[8:-10].replace('&amp;', '&')
    
    def set_application_comment(self, comment):
        """Set the application comment label and entry."""
        if comment == None:
            comment = ''
        comment = comment.replace('&', '&amp;')
        self.general_comment_label.set_markup( '<i>%s</i>' % comment )
        self.general_comment_entry.set_text( comment )
    
    def get_application_comment(self):
        """Return the application comment extracted from the button 
        label."""
        return self.general_comment_label.get_label()[3:-4]
    
    def set_application_command(self, command):
        """Set the application command entry."""
        if command == None:
            command = ''
        self.general_command_entry.set_text( command )
    
    def get_application_command(self):
        """Return the application command."""
        return self.general_command_entry.get_text()
    
    def set_application_path(self, path):
        """Set the application working directory."""
        if path == None:
            path = ''
        self.general_path_entry.set_text(path)
    
    def get_application_path(self):
        """Return the application working directory."""
        return self.general_path_entry.get_text()
    
    def set_application_terminal(self, terminal):
        """Set whether the application runs in a terminal."""
        if terminal == None:
            terminal = False
        self.general_terminal_switch.set_active(terminal)
        
    def get_application_terminal(self):
        """Return whether the application runs in a terminal."""
        return self.general_terminal_switch.get_active()
    
    def set_application_startupnotify(self, startupnotify):
        """Set the application Use startup notification switch."""
        if startupnotify == None:
            startupnotify = False
        self.general_startupnotify_switch.set_active( startupnotify )
    
    def get_application_startupnotify(self):
        """Return whether the application should notify on startup."""
        return self.general_startupnotify_switch.get_active()
        
    def set_application_hidden(self, hidden):
        """Set whether the application is hidden in the menus."""
        self.general_nodisplay_switch.set_active( hidden )
        
    def get_application_hidden(self):
        """Return whether the application is hidden in the menus."""
        return self.general_nodisplay_switch.get_active()
    
    def set_application_filename(self, filename):
        """Set the application filename."""
        self.general_filename_label.set_markup('<small>%s</small>' % filename)
        self.statusbar.set_label(filename)
        
    def get_application_filename(self):
        """Return the application filename."""
        label = self.general_filename_label.get_label()
        return label.rstrip('</small>').lstrip('<small>')
        
    def set_application_categories(self, categories):
        """Set the application categories from a list of category 
        names."""
        self.categories_accessories.set_active( 'Utility' in categories )
        self.categories_development.set_active( 'Development' in categories )
        self.categories_education.set_active( 'Education' in categories )
        self.categories_games.set_active( 'Game' in categories )
        self.categories_graphics.set_active( 'Graphics' in categories )
        self.categories_internet.set_active( 'Network' in categories )
        self.categories_multimedia.set_active( 'AudioVideo' in categories )
        self.categories_office.set_active( 'Office' in categories )
        self.categories_settings.set_active( 'Settings' in categories )
        self.categories_system.set_active( 'System' in categories )
        for cat in categories:
            if 'wine' in cat.lower():
                self.categories_wine.set_active( True )
                return
        self.categories_wine.set_active(False)
            
    def get_application_categories(self):
        """Return a list of the application categories."""
        categories = []
        if self.categories_accessories.get_active():
            categories.append('Utility')
        if self.categories_development.get_active():
            categories.append('Development')
        if self.categories_education.get_active():
            categories.append('Education')
        if self.categories_games.get_active():
            categories.append('Game')
        if self.categories_graphics.get_active():
            categories.append('Graphics')
        if self.categories_internet.get_active():
            categories.append('Network')
        if self.categories_multimedia.get_active():
            categories.append('AudioVideo')
        if self.categories_office.get_active():
            categories.append('Office')
        if self.categories_settings.get_active():
            categories.append('Settings')
        if self.categories_system.get_active():
            categories.append('System')
        if self.categories_wine.get_active():
            categories.append('Wine')
        return categories
    
    def set_application_quicklists(self, quicklists):
        """Set the application quicklists treeview."""
        listmodel = Gtk.ListStore(bool, str, str, str)
        lists = []
        try:
            for key in quicklists.keys():
                shortcut_name = key
                displayed_name = quicklists[key]['name']
                enabled = quicklists[key]['enabled']
                command = quicklists[key]['command']
                order = quicklists[key]['order']
                lists.append( [enabled, shortcut_name, displayed_name, command, order] )
            lists = sorted(lists, key=lambda quicklist: quicklist[4])
            for group in lists:
                listmodel.append( group[:4] )
        except (KeyError, TypeError, AttributeError):
            pass
        self.quicklists_treeview.set_model(listmodel)
    
    def get_application_quicklists(self):
        """Return the application quicklists."""
        model = self.quicklists_treeview.get_model()
        quicklists = []
        try:
            iter = model.get_iter_first()
            while iter != None:
                enabled = model.get_value(iter, 0)
                shortcut_name = model.get_value(iter, 1)
                displayed_name = model.get_value(iter, 2)
                command = model.get_value(iter, 3)
                quicklists.append( [enabled, shortcut_name, displayed_name, command] )
                iter = model.iter_next(iter)
        except AttributeError:
            pass
        return quicklists
    
    def set_application_text(self, text):
        """Set the application text editor."""
        self.editor_textview.get_buffer().set_text(text)
    
    def get_application_text(self):
        """Return the text that is contained in the application text
        editor buffer."""
        buffer = self.editor_textview.get_buffer()
        return buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)

    def set_preview_from_name(self, name):
        """Set the Icon preview from an icon name."""
        if name == None or len(name) == 0:
            self.set_preview_from_stock('application-default-icon')
        else:
            self.preview128.set_from_icon_name( name, Gtk.IconSize.UNITY )
            self.preview48.set_from_icon_name( name, Gtk.IconSize.DIALOG )
            self.preview32.set_from_icon_name( name, Gtk.IconSize.DND )
            self.preview24.set_from_icon_name( name, Gtk.IconSize.LARGE_TOOLBAR )
            self.preview16.set_from_icon_name( name, Gtk.IconSize.MENU )
            
    def set_preview_from_filename(self, filename):
        """Set the Icon preview from a filename."""
        if filename == None:
            self.set_preview_from_stock('application-default-icon')
        else:
            self.preview128.set_from_pixbuf( icon_theme.get_theme_GdkPixbuf(filename, Gtk.IconSize.UNITY) )
            self.preview48.set_from_pixbuf( icon_theme.get_theme_GdkPixbuf(filename, Gtk.IconSize.DIALOG) )
            self.preview32.set_from_pixbuf( icon_theme.get_theme_GdkPixbuf(filename, Gtk.IconSize.DND) )
            self.preview24.set_from_pixbuf( icon_theme.get_theme_GdkPixbuf(filename, Gtk.IconSize.LARGE_TOOLBAR) )
            self.preview16.set_from_pixbuf( icon_theme.get_theme_GdkPixbuf(filename, Gtk.IconSize.MENU) )
        
    # -- End Helper Functions ---------------------------------------- #
    
    def general_name_modify_accept(self):
        """Accept the changes to the application name, and set the
        various labels according to the new data."""
        name = self.general_name_entry.get_text()
        self.set_application_name( name )
        if self.get_application_filename() == 'New Application':
            filename = name.replace(' ', '').replace('&', '').lower()
            filename += '.desktop'
            if self.sudo:
                filename = os.path.join( '/usr', 'share', 'applications', filename )
            else:
                filename = os.path.join( home, '.local', 'share', 'applications', filename )
            if os.path.exists(filename):
                counter = 0
                while os.path.exists(filename.replace('.desktop', str(counter)+'.desktop')):
                    counter += 1
                filename = filename.replace('.desktop', str(counter)+'.desktop')
            self.set_application_filename( filename )
        self.hide_general_name_editor()
        self.update_editor()
    
    def general_name_modify_reject(self):
        """Reject the changes to the application name, and maintain
        the current labels."""
        self.hide_general_name_editor()
        self.general_name_entry.set_text(self.get_application_name())
    
    def general_comment_modify_accept(self):
        """Accept the changes to the application comment, and set the
        various labels according to the new data."""
        self.set_application_comment( self.general_comment_entry.get_text())
        self.hide_general_comment_editor()
        self.update_editor()
    
    def general_comment_modify_reject(self):
        """Reject the changes to the application comment, and maintain
        the current labels."""
        self.hide_general_comment_editor()
        self.general_comment_entry.set_text( self.get_application_comment() )
        
    def clear_catselection_iconview(self):
        """Remove all items from the category selection and return a new
        Gtk.ListStore."""
        liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str, int)
        self.catselection_iconview.set_model(liststore)
        self.catselection_iconview.set_pixbuf_column(0)
        self.catselection_iconview.set_markup_column(1)
        return liststore
        
    def clear_appselection_iconview(self):
        """Remove all items from the application selection and return a 
        new Gtk.ListStore."""
        liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str, int, str)
        self.appselection_iconview.set_model(liststore)
        self.appselection_iconview.set_pixbuf_column(0)
        self.appselection_iconview.set_markup_column(1)
        return liststore
        
    def show_catselection(self):
        """Show the category selection, and hide other views."""
        self.appsettings_notebook.hide()
        self.appselection_search_fail.hide()
        self.appselection.hide()
        self.catselection.show()
        self.on_catselection_iconview_selection_changed()
    
    def show_appselection(self):
        """Show the application selection, and hide other views."""
        self.appsettings_notebook.hide()
        self.appselection_search_fail.hide()
        self.catselection.hide()
        self.appselection.show()
        self.on_appselection_iconview_selection_changed()
        
    def show_appsettings(self):
        """Show the application launcher editor, and hide other views."""
        self.appselection_search_fail.hide()
        self.appselection.hide()
        self.catselection.hide()
        self.appsettings_notebook.show()
        self.statusbar.set_label( self.get_application_filename() )
        
    def show_selection_fail(self):
        """Show the selection search failure view, and hide other views."""
        self.appselection.hide()
        self.appsettings_notebook.hide()
        self.catselection.hide()
        self.appselection_search_fail.show()
        
    def show_general_name_editor(self):
        """Show the application name editor."""
        self.general_name_button.set_visible(False)
        self.general_name_modify_box.set_visible(True)
        self.set_focus( self.general_name_entry )
        
    def hide_general_name_editor(self):
        """Hide the application name editor."""
        self.general_name_modify_box.set_visible(False)
        self.general_name_button.set_visible(True)
        self.set_focus( self.general_name_button )
        
    def show_general_comment_editor(self):
        """Show the application comment editor."""
        self.general_comment_button.set_visible(False)
        self.general_comment_modify_box.set_visible(True)
        self.set_focus( self.general_comment_entry )
        
    def hide_general_comment_editor(self):
        """Hide the application comment editor."""
        self.general_comment_modify_box.set_visible(False)
        self.general_comment_button.set_visible(True)
        self.set_focus( self.general_comment_button )
        
    def set_categories_expanded(self, expanded):
        """Toggle visibility of the category checkboxes."""
        self.categories_expander.set_expanded(expanded)

    def load_category_into_iconview(self, category=None):
        """Load the icon view for categories or applications."""
        if category == None:
            # Home View
            model = self.clear_catselection_iconview()
            self.entry_search.set_placeholder_text('Search Applications')
            image = icon_theme.get_theme_GdkPixbuf('applications-other', Gtk.IconSize.DIALOG)
            model.append([image, 'All Applications', -9001])
            categories = self.categories.values()
            categories = sorted(categories, key=lambda category: category[0].lower())
            for category in categories:
                label, image, category_id, apps = category
                if label == 'WINE' and not self.show_wine:
                    return
                image = icon_theme.get_theme_GdkPixbuf(image, Gtk.IconSize.DIALOG)
                model.append([image, label, category_id])
            
        else:
            # Load specific category applications (Category View)
            model = self.clear_appselection_iconview()
            if category == '':
                self.set_breadcrumb_category('all')
            else:
                self.set_breadcrumb_category(self.categories[category])
                label = self.breadcrumb_category_label.get_label()
                self.entry_search.set_placeholder_text('Search %s' % label)
            icon = self.get_icon_pixbuf( 'gtk-add', Gtk.IconSize.DIALOG)
            model.append( [icon, 'Add Launcher', 1337, 'Add a new application launcher'] )
            apps = sorted(self.apps.values(), key=lambda app: app.get_name().lower())
            for app in apps:
                show_app = False
                if category.lower() == 'wine':
                    for cat in app.get_categories():
                        if 'wine' in cat.lower():
                            show_app = True
                if category in app.get_categories() or category == '':
                    show_app = True
                if show_app:
                    icon = self.get_icon_pixbuf( app.get_icon(), Gtk.IconSize.DIALOG )
                    name = app.get_name().replace('&', '&amp;')
                    appid = app.get_id()
                    comment = app.get_comment()
                    hidden = app.get_hidden()
                    if hidden:
                        name = '<i>%s</i>' % name
                    model.append( [icon, name, appid, comment] )            
                    
    def set_breadcrumb_category(self, category):
        """Set the breadcrumb category."""
        if category == 'all':
            name = "All Applications"
            icon = 'gtk-about'
        else:
            name, icon, catid, apps = category
        if self.breadcrumb_category_label.get_label() != name:
            self.breadcrumb_application.hide()
        pixbuf = icon_theme.get_theme_GdkPixbuf(icon, Gtk.IconSize.BUTTON)
        self.breadcrumb_category_image.set_from_pixbuf(pixbuf)
        self.breadcrumb_category_label.set_label(name)
        self.breadcrumb_category.show_all()
        self.breadcrumb_home.set_active(False)
        self.breadcrumb_application.set_active(False)
        self.breadcrumb_category.set_active(True)
        
    def set_breadcrumb_application(self, app_id):
        """Set the application breadcrumb to the application with ID 
        app_id."""
        if app_id == 1337:
            name = 'New Menu Item'
            icon = 'gtk-add'
            self.breadcrumb_application_image.set_from_stock(icon, Gtk.IconSize.BUTTON)
        else:
            app = self.apps[app_id]
            name = app.get_name()
            icon = app.get_icon()
            pixbuf = icon_theme.get_theme_GdkPixbuf(icon, Gtk.IconSize.BUTTON)
            self.breadcrumb_application_image.set_from_pixbuf(pixbuf)
        self.breadcrumb_application_label.set_label(name)
        self.breadcrumb_application.show_all()
        self.breadcrumb_home.set_active(False)
        self.breadcrumb_category.set_active(False)
        self.breadcrumb_application.set_active(True)

    def load_iconselection_icons(self):
        """Loads icons into the icon selection"""
        liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
        self.iconselection_filter = liststore.filter_new()
        self.iconselection_filter.set_visible_func(self.iconselection_filter_func)
        self.iconselection_treeview.set_model(self.iconselection_filter)
        while Gtk.events_pending(): Gtk.main_iteration()
        icons = icon_theme.get_all_icons(Gtk.IconSize.LARGE_TOOLBAR).keys()
        icons = sorted(icons, key=lambda icon: icon.lower())
        for icon in icons:
            if 'action' not in icon and icon[:8] != 'process-' and icon[-8:] != '-spinner':
                liststore.append( [icon_theme.get_theme_GdkPixbuf(icon, Gtk.IconSize.LARGE_TOOLBAR), icon] )
            yield True
        yield False

    def get_icon_pixbuf(self, icon_name, IconSize):
		"""Return a Pixbuf for icon_name at size IconSize."""
        pixbuf = icon_theme.get_theme_GdkPixbuf( icon_name, IconSize )
        if pixbuf:
            return pixbuf
        
        try:
            icon = icon_theme.load_icon(icon_name, Gtk.icon_size_lookup(IconSize)[1], 0)
            return icon
        except:
            if 'applications-' in icon_name:
                try:
                    name = icon_name.replace('applications-', 'xfce-')
                    icon = icon_theme.load_icon(name, Gtk.icon_size_lookup(IconSize)[1], 0)
                    return icon
                except:
                    pass
        if icon_name != 'gtk-missing-image':
            return self.get_icon_pixbuf('gtk-missing-image', IconSize)
        else:
            return None
            
    def shortcut_edited_cb(self, cell, path, new_text, user_data):
        """Quicklist treeview ShortcutName edited callback function."""
        treeview, column = user_data
        liststore = treeview.get_model()
        new_text = new_text.replace(' ', '').replace('&', '')
        quicklists = self.get_application_quicklists()
        new_text = self.get_quicklist_unique_shortcut_name(quicklists, new_text, 0)
        liststore[path][column] = new_text
        self.update_editor()

    def edited_cb(self, cell, path, new_text, user_data):
        """Quicklist treeview cell edited callback function."""
        treeview, column = user_data
        liststore = treeview.get_model()
        liststore[path][column] = new_text
        self.update_editor()
    
    def update_editor(self, editor_updated=False):
		"""Update the editor and settings (call the threaded update)."""
        task = self.threaded_update_editor(editor_updated)
        if task != None:
            GObject.idle_add(task.next)
    
    def get_data_from_editor(self):
		"""Return the launcher settings from the editor text."""
        text = self.get_application_text()
        return Applications.read_desktop_file(self.get_application_filename(), text)
        
    def threaded_update_editor(self, editor_updated):
		"""Update the editor and settings on a GObject thread."""
        if not self.update_pending:
            while Gtk.events_pending(): Gtk.main_iteration()
            # When the editor is updated, update all the fields, 
            # switches, and checkboxes in the launcher settings.
            if editor_updated:
                self.update_pending = True
                if not self.in_history:
                    self.undo_stack.append(self.last_editor)
                    self.set_undo_enabled(True)
                    del self.redo_stack[:]
                    self.set_redo_enabled(False)
                data = self.get_data_from_editor()
                self.set_application_icon( data['icon'], Gtk.IconSize.DIALOG )
                self.set_application_name( data['name'] )
                self.set_application_comment( data['comment'] )
                self.set_application_command( data['command'] )
                self.set_application_path( data['path'] )
                self.set_application_terminal( data['terminal'] )
                self.set_application_startupnotify( data['startupnotify'] )
                self.set_application_hidden( data['hidden'] )
                self.set_application_categories( data['categories'] )
                self.set_application_quicklists( data['quicklists'] )
                
                self.update_pending = False
            # When the launcher settings are modified, update the editor
            # appropriately.
            else:
                self.update_pending = True
                if not self.in_history:
                    self.undo_stack.append(self.get_application_text())
                    self.set_undo_enabled(True)
                    del self.redo_stack[:]
                    self.set_redo_enabled(False)
                icon = self.get_application_icon()
                name = self.get_application_name()
                comment = self.get_application_comment()
                command = self.get_application_command()
                path = self.get_application_path()
                terminal = str(self.get_application_terminal()).lower()
                startupnotify = str(self.get_application_startupnotify()).lower()
                hidden = str(self.get_application_hidden()).lower()
                categories = self.get_application_categories()
                #filename = self.get_application_filename()
                quicklists_action, quicklist_string = self.get_quicklist_strings()
                #self.update_pending = False
                icon_set = False
                name_set = False
                comment_set = False
                command_set = False
                path_set = False
                terminal_set = False
                startupnotify_set = False
                hidden_set = False
                categories_set = False
                actions_set = False
                
                buffer = self.editor_textview.get_buffer()
                text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
                text_lines = text.split('\n')
                newlines = []
                for line in text_lines:
                    try:
                        if line[:5] == 'Icon=':
                            if not icon_set:
                                newlines.append(line[:5] + icon)
                                icon_set = True
                            else: newlines.append(line)
                        elif line[:5] == 'Name=':
                            if not name_set:
                                newlines.append(line[:5] + name)
                                name_set = True
                            else: newlines.append(line)
                        elif line[:8] == 'Comment=':
                            if not comment_set:
                                newlines.append(line[:8] + comment)
                                comment_set = True
                            else: newlines.append(line)
                        elif line[:5] == 'Exec=':
                            if not command_set:
                                newlines.append(line[:5] + command)
                                command_set = True
                            else: newlines.append(line)
                        elif line[:8] == 'TryExec=':
                            newlines.append(line[:8] + command.split(' ')[0])
                        elif line[:5] == 'Path=':
                            if not path_set:
                                newlines.append(line[:5] + path)
                                path_set = True
                            else: newlines.append(line)
                        elif line[:9] == 'Terminal=':
                            if not terminal_set:
                                newlines.append(line[:9] + terminal)
                                terminal_set = True
                            else: newlines.append(line)
                        elif line[:14] == 'StartupNotify=':
                            if not startupnotify_set:
                                newlines.append(line[:14] + startupnotify)
                                startupnotify_set = True
                            else: newlines.append(line)
                        elif line[:10] == 'NoDisplay=':
                            if not hidden_set:
                                newlines.append(line[:10] + hidden)
                                hidden_set = True
                            else:
                                newlines.append(line)
                        elif line[:11] == 'Categories=':
                            if not categories_set:
                                newlines.append(line[:11] + ';'.join(categories))
                                categories_set = True
                            else:
                                newlines.append(line)
                        elif line[:8] == 'Actions=' or 'X-Ayatana-Desktop-Shortcuts' in line:
                            newlines.append(quicklists_action)
                        elif line[0] == '[' and line != '[Desktop Entry]':
                            newlines.append(quicklist_string)
                            newlines.append('\n')
                            actions_set = True
                            break
                        else: newlines.append(line)
                    except IndexError:
                        newlines.append(line)
                text = '\n'.join(newlines)
                # check for missing tags
                if not comment_set:
                    text = text.replace('\nName=%s\n' % name, '\nName=%s\nComment=%s\n' % (name, comment), 1)
                if not icon_set:
                    text = text.replace('\nComment=%s\n' % comment, '\nComment=%s\nIcon=%s\n' % (comment, icon), 1)
                if not command_set:
                    text = text.replace('\nIcon=%s\n' % icon, '\nIcon=%s\nExec=%s\n' % (icon, command), 1)
                if not path_set:
                    text = text.replace('\nExec=%s\n' % command, '\nExec=%s\nPath=%s\n' % (command, path), 1)
                if not terminal_set:
                    text = text.replace('\nPath=%s\n' % path, '\nPath=%s\nTerminal=%s\n' % (path, terminal), 1)
                if not hidden_set:
                    text = text.replace('\nTerminal=%s\n' % terminal, '\nTerminal=%s\nNoDisplay=%s\n' % (terminal, hidden), 1)
                if not startupnotify_set:
                    text = text.replace('\nTerminal=%s\n' % terminal, '\nTerminal=%s\nStartupNotify=%s\n' % (terminal, startupnotify), 1)
                if not categories_set:
                    text = text.replace('\nStartupNotify=%s\n' % startupnotify, '\nStartupNotify=%s\nCategories=%s\n' % (startupnotify, ';'.join(categories)), 1)
                if not actions_set and len(quicklist_string) > 0:
                    text += '\n' + quicklists_action + '\n' + quicklist_string
                text = text.replace('\n\n\n', '\n\n')
                buffer.set_text(text)
                self.update_pending = False
            self.last_editor = self.get_application_text()
            if len(self.undo_stack) == 0:
                self.set_save_enabled(False)
                self.set_revert_enabled(False)
            else:
                self.set_save_enabled(True)
                self.set_revert_enabled(True)
                
    def on_editor_buffer_changed(self, buffer):
		"""Update the launcher entry fields when the editor is 
		modified."""
        self.update_editor(True)

    def get_quicklist_strings(self):
		"""Return the application quicklist format string and quicklist
		entry games."""
        quicklists = self.get_application_quicklists()
        format = self.quicklist_format
        actions = ''
        quicklist_string = ''
        try:
            format = format.lower()
            if format == 'actions':
                actions = 'Actions='
                for quicklist in quicklists:
                    enabled, shortcut_name, displayed_name, command = quicklist
                    string = """
[Desktop Action %s]
Name=%s
Exec=%s
OnlyShowIn=Unity;
""" % (shortcut_name, displayed_name, command)
                    quicklist_string += string
                    if enabled:
                        actions += '%s;' % shortcut_name
            elif format == 'x-ayatana-desktop-shortcuts':
                actions = 'X-Ayatana-Desktop-Shortcuts='
                for quicklist in quicklists:
                    enabled, shortcut_name, displayed_name, command = quicklist
                    string = """
[%s Shortcut Group]
Name=%s
Exec=%s
OnlyShowIn=Unity;
""" % (shortcut_name, displayed_name, command)
                    quicklist_string += string
                    if enabled:
                        actions += '%s;' % shortcut_name
            quicklist_string = quicklist_string.rstrip()
        except AttributeError:
            pass
                    
        return (actions, quicklist_string)
    
    def undo(self):
		"""Undo the last done action in history."""
        self.in_history = True
        current = self.get_application_text()
        self.redo_stack.append(current)
        self.set_redo_enabled(True)
        undo_text = self.undo_stack.pop()
        if len(self.undo_stack) == 0:
            self.set_undo_enabled(False)
        self.set_application_text(undo_text)
        self.in_history = False
        
    def redo(self):
		"""Redo the last undone action in history."""
        self.in_history = True
        current = self.get_application_text()
        self.undo_stack.append(current)
        self.set_undo_enabled(True)
        redo_text = self.redo_stack.pop()
        if len(self.redo_stack) == 0:
            self.set_redo_enabled(False)
        self.set_application_text(redo_text)
        self.in_history = False
        
    def new_launcher(self):
		"""Show the application editor with details for a new 
		application."""
        self.set_breadcrumb_application(1337)
        self.breadcrumb_category.set_visible(False)
        
        # General Settings
        self.set_application_icon( 'application-default-icon', Gtk.IconSize.DIALOG )
        self.set_application_name( 'New Menu Item' )
        self.set_application_comment( 'A small descriptive blurb about this application.' )
        self.set_application_command( '' )
        self.set_application_path( '' )
        self.set_application_terminal( False )
        self.set_application_startupnotify( False )
        self.set_application_hidden( False )
        self.set_application_categories( [] )
        self.set_application_filename( 'New Application' )
        
        # Quicklists
        self.set_application_quicklists( None )
        
        launcher = """
[Desktop Entry]
Name=New Menu Item
Comment=A small descriptive blurb about this application.
Categories=
Exec=
Icon=application-default-icon
Terminal=false
Type=Application
Actions=
        """
        
        # Editor
        self.set_application_text( launcher )
        self.show_appsettings()
        self.in_history = False
        self.last_editor = launcher
        
        self.set_categories_expanded(True)


    def show_search_results(self, query, category=None):
		"""Show search results for the query in the application 
		browser."""
        self.set_position(Gtk.WindowPosition.NONE)
        if category == None:
            self.last_cat = None
        model = self.clear_appselection_iconview()
        name = "Search Results"
        icon = "gtk-find"
        self.breadcrumb_category_image.set_from_stock(icon, Gtk.IconSize.BUTTON)
        self.breadcrumb_category_label.set_label(name)
        self.breadcrumb_category.show_all()
        self.breadcrumb_home.set_active(False)
        self.breadcrumb_application.set_active(False)
        self.breadcrumb_category.set_active(True)
        apps = sorted(self.apps.values(), key=lambda app: app.get_name().lower())
        counter = 0
        for app in apps:
            show_icon = True
            if category != None:
                if category in app.get_categories():
                    pass
                else:
                    show_icon = False
            if show_icon and query.lower() in app.get_name().lower():
                counter += 1
                icon = self.get_icon_pixbuf( app.get_icon(), Gtk.IconSize.DIALOG )
                name = app.get_name().replace('&', '&amp;')
                appid = app.get_id()
                comment = app.get_comment()
                model.append( [icon, name, appid, comment] )
        if counter == 0:
            self.show_selection_fail()
        else:
            self.show_appselection()

    def get_quicklist_unique_shortcut_name(self, quicklists, base_name, counter):
		"""Return a unique shortcut for the quicklists using the 
		base_name and counters."""
        if counter == 0:
            for quicklist in quicklists:
                if quicklist[1] == base_name:
                    return self.get_quicklist_unique_shortcut_name(quicklists, base_name, counter+1)
            return base_name
        else:
            for quicklist in quicklists:
                if quicklist[1] == base_name + str(counter):
                    return self.get_quicklist_unique_shortcut_name(quicklists, base_name, counter+1)
            return base_name + str(counter)
