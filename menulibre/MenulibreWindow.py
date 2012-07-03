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

from menulibre_lib import Window, IconTheme, Applications, history
from menulibre.AboutMenulibreDialog import AboutMenulibreDialog
from menulibre.PreferencesMenulibreDialog import PreferencesMenulibreDialog

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
        self.PreferencesDialog = PreferencesMenulibreDialog
        
        self.show_wine = os.path.isdir('/usr/share/wine')

        # Code for other initialization actions should be added here.
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
        self.get_interface()
        self.icon_cache = dict()

        self.ignore_undo = False
        

        self.apps = Applications.get_applications()
        
        

        self.iconview_filename = None

        #self.show_applications()
        self.lock_breadcrumb = False
        self.category = None
        self.lock_application = False
        self.iconview_single = False
        
        self.update_pending = False
        self.ignore_updates = False
        
        self.quicklist_format = None
        
        self.load_category_into_iconview(None)

        self.quicklist_modified = False

        self.editor_changed = False
        self.in_history = False
        self.last_editor = ''
        
        if os.getuid() == 0: 
            self.sudo = True
        else:
            self.sudo = False
        
        
        
        self.undo_stack = []
        self.redo_stack = []
        
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
        self.appselection = self.builder.get_object('appselection_scrolled')
        self.appselection_iconview = self.builder.get_object('appselection_iconview')
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
        text_render_name.connect('edited', self.edited_cb, (self.quicklists_treeview, 1))
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
        buffer.connect('changed', self.set_editor_line)
        
      # Icon Selection Dialog 1 (Select and Preview)
        self.iconselection_dialog = self.builder.get_object('iconselection_dialog1')
        self.iconselection_radio_stock = self.builder.get_object('iconselection_radio_stock')
        self.iconselection_radio_theme = self.builder.get_object('iconselection_radio_theme')
        self.iconselection_radio_image = self.builder.get_object('iconselection_radio_image')
        self.iconselection_stock = self.builder.get_object('iconselection_stock')
        self.iconselection_theme = self.builder.get_object('iconselection_theme')
        self.iconselection_theme_entry = self.builder.get_object('iconselection_theme_entry')
        self.iconselection_theme_browse = self.builder.get_object('iconselection_theme_browse')
        self.iconselection_image = self.builder.get_object('iconselection_image')
        self.preview128 = self.builder.get_object('preview128')
        self.preview48 = self.builder.get_object('preview48')
        self.preview32 = self.builder.get_object('preview32')
        self.preview24 = self.builder.get_object('preview24')
        self.preview16 = self.builder.get_object('preview16')
        self.set_preview_from_stock('gtk-missing-image')
                
        combobox_liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
        self.iconselection_stock.set_model(combobox_liststore)

        cell_pixbuf = Gtk.CellRendererPixbuf()
        self.iconselection_stock.pack_start(cell_pixbuf, True)
        self.iconselection_stock.add_attribute(cell_pixbuf, 'pixbuf', 0)

        cell_text = Gtk.CellRendererText()
        self.iconselection_stock.pack_start(cell_text, False)
        self.iconselection_stock.add_attribute(cell_text, 'text', 1)
        
        stocks = Gtk.stock_list_ids()
        stocks = sorted(stocks, key=lambda stock: stock.lower())
        for stockicon in stocks:
            try:
                icon = self.iconselection_stock.render_icon(stockicon, Gtk.IconSize.MENU)
                combobox_liststore.append([icon, stockicon])
            except AttributeError:
                pass
    
      # Icon Selection Dialog 2 (All Icons)
        self.iconselection_dialog_all = self.builder.get_object('iconselection_dialog2')
        self.iconselection_search = self.builder.get_object('iconselection_dialog2_search')
        self.iconselection_iconview = self.builder.get_object('iconselection_dialog2_iconview')
        
  # Events        
    def on_toolbar_addnew_clicked(self, button):
        
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
    
    def on_toolbar_undo_clicked(self, button):
        self.undo()
    
    def on_toolbar_redo_clicked(self, button):
        self.redo()
    
    def on_toolbar_revert_clicked(self, button):
        data = self.undo_stack[0]
        del self.undo_stack[:]
        del self.redo_stack[:]
        self.set_application_text( data )
        self.set_undo_enabled(False)
        self.set_redo_enabled(False)
        #self.set_save_enabled(False)
        self.set_revert_enabled(False)
    
    def on_entry_search_changed(self, widget):
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
            category = None
            self.last_cat = None
            if self.breadcrumb_category.get_active():
                search_type = self.entry_search.get_placeholder_text().replace('Search ', '')
                for cat in self.categories:
                    if self.categories[cat][0] == search_type:
                        self.last_cat = category = cat
            widget.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, 'gtk-clear')
            self.show_search_results(text, category)
            
    def show_search_results(self, query, category=None):
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
                icon = self.get_icon_pixbuf( app.get_icon()[1], Gtk.IconSize.DIALOG )
                name = app.get_name()
                appid = app.get_id()
                comment = app.get_comment()
                model.append( [icon, name, appid, comment] )
        if counter == 0:
            self.show_selection_fail()
        else:
            self.show_appselection()
    
    def on_entry_search_icon_press(self, widget, button, event):
        if button == Gtk.EntryIconPosition.SECONDARY:
            self.entry_search.set_text('')
    
    def on_breadcrumb_home_clicked(self, button):
        if not self.lock_breadcrumb:
            self.entry_search.set_placeholder_text('Search Applications')
            self.lock_breadcrumb = True
            self.breadcrumb_application.set_active(False)
            self.breadcrumb_category.set_active(False) 
            self.lock_breadcrumb = False
            self.show_catselection()
        
    def on_breadcrumb_category_clicked(self, button):
        if not self.lock_breadcrumb:
            label = self.breadcrumb_category_label.get_label()
            self.entry_search.set_placeholder_text('Search %s' % label)
            self.lock_breadcrumb = True
            self.breadcrumb_application.set_active(False)
            self.breadcrumb_home.set_active(False)
            self.lock_breadcrumb = False
            self.show_appselection()
            
    def on_breadcrumb_application_clicked(self, button):
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
            
    def on_catselection_iconview_item_activated(self, widget, index):
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
        
    
    def on_appselection_iconview_item_activated(self, widget, index):
        self.appsettings_notebook.set_current_page(0)
        self.set_position(Gtk.WindowPosition.NONE)
        if self.iconview_single:
            self.iconview_single = False
            return
        self.iconview_single = True
        self.lock_breadcrumb = True
        try:
            model = widget.get_model()
            #label = model[index][1]
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
        except IndexError:
            pass
        self.lock_breadcrumb = False
        
    def on_catselection_iconview_selection_changed(self, widget):
        try:
            model = widget.get_model()
            index = int(widget.get_selected_items()[0].to_string())
            label =  model[index][1]
            self.statusbar.set_label(label)
        except IndexError:
            self.statusbar.set_label('')
        
    def on_appselection_iconview_selection_changed(self, widget):
        try:
            model = widget.get_model()
            index = int(widget.get_selected_items()[0].to_string())
            label =  model[index][3]
            self.statusbar.set_label(label)
        except IndexError:
            self.statusbar.set_label('')
    
    def on_appselection_search_all_button_clicked(self, button):
        pass 
    
    def on_appsettings_notebook_switch_page(self, notebook, page, pageno):
        buffer = self.editor_textview.get_buffer()
        buffer.place_cursor( buffer.get_start_iter() )
    
    def on_general_icon_button_clicked(self, button):
        self.iconselection_dialog.show_all()
        self.iconselection_dialog.run()
        self.iconselection_dialog.hide()
    
    def on_general_name_button_clicked(self, button):
        self.show_general_name_editor()
        
    def on_general_name_modify_entry_activate(self, widget):
        self.general_name_modify_accept()
        
    def on_general_name_modify_entry_key_press_event(self, widget, event):
        if Gdk.keyval_name(event.get_keyval()[1]) == 'Escape':
            self.general_name_modify_reject()
    
    def on_general_name_modify_cancel_clicked(self, button):
        self.general_name_modify_reject()
    
    def on_general_name_modify_confirm_clicked(self, button):
        self.general_name_modify_accept()
    
    def on_general_comment_button_clicked(self, button):
        self.show_general_comment_editor()
        
    def on_general_comment_modify_entry_activate(self, widget):
        self.general_comment_modify_accept()
        
    def on_general_comment_modify_entry_key_press_event(self, widget, event):
        if Gdk.keyval_name(event.get_keyval()[1]) == 'Escape':
            self.general_comment_modify_reject()
    
    def on_general_comment_modify_cancel_clicked(self, button):
        self.general_comment_modify_reject()
    
    def on_general_comment_modify_confirm_clicked(self, button):
        self.general_comment_modify_accept()
        
    def on_general_command_entry_changed(self, widget):
        self.update_editor()
    
    def on_general_command_browse_clicked(self, button):
        dialog = Gtk.FileChooserDialog("Select an executable", self, 0, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
        dialog.show()
        response = dialog.run()
        dialog.hide()
        if response == Gtk.ResponseType.OK:
            self.set_application_command( dialog.get_filename() )
    
    def on_general_path_entry_changed(self, widget):
        self.update_editor()
    
    def on_general_path_browse_clicked(self, button):
        dialog = Gtk.FileChooserDialog("Select an executable", self, Gtk.FileChooserAction.SELECT_FOLDER, buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
        dialog.show()
        response = dialog.run()
        dialog.hide()
        if response == Gtk.ResponseType.OK:
            self.set_application_path( dialog.get_filename() )
    
    def on_general_terminal_switch_toggled(self, widget, state):
        self.update_editor()
    
    def on_general_startupnotify_switch_toggled(self, widget, state):
        self.update_editor()
        
    def on_general_nodisplay_switch_toggled(self, widget, state):
        self.update_editor()
    
    def on_quicklist_toggled(self, widget, path):
        model = self.quicklists_treeview.get_model()
        model[path][0] = not model[path][0]
        self.update_editor()
        
    def get_quicklist_unique_shortcut_name(self, quicklists, base_name, counter):
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
            
    def on_quicklists_treeview_cursor_changed(self, widget):
        if self.quicklist_modified:
            self.update_editor()
        self.quicklist_modified = False
    
    def on_quicklist_add_clicked(self, button):
        self.quicklist_modified = True
        quicklists = self.get_application_quicklists()
        listmodel = self.quicklists_treeview.get_model()
        if len(listmodel) == 0:
            self.quicklist_format = 'actions'
        shortcut_name = self.get_quicklist_unique_shortcut_name(quicklists, 'NewShortcut', 0)
        
        listmodel.append([False, shortcut_name, 'New Shortcut', ''])
        self.quicklists_treeview.set_cursor_on_cell( Gtk.TreePath.new_from_string( str(len(listmodel)-1) ), None, None, False )
    
    def on_quicklist_remove_clicked(self, button):
        if len(self.quicklists_treeview.get_model()) > 0:
            self.quicklist_modified = True
            tree_sel = self.quicklists_treeview.get_selection()
            (treestore, treeiter) = tree_sel.get_selected()
            treestore.remove(treeiter)
    
    def on_quicklist_move_up_clicked(self, button):
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
    
    def on_iconselection_radio_stock_toggled(self, radio_button):
        self.iconselection_stock.set_sensitive( radio_button.get_active() )
        if radio_button.get_active():
            model = self.iconselection_stock.get_model()
            active = self.iconselection_stock.get_active()
            if active < 0:
                self.set_preview_from_stock('gtk-missing-image')
            else:
                stockicon = model[active][1]
                self.set_preview_from_stock(stockicon)
    
    def on_iconselection_radio_theme_toggled(self, radio_button):
        self.iconselection_theme.set_sensitive( radio_button.get_active() )
        if radio_button.get_active():
            self.set_preview_from_name(self.iconselection_theme_entry.get_text())
    
    def on_iconselection_radio_image_toggled(self, radio_button):
        self.iconselection_image.set_sensitive( radio_button.get_active() )
        if radio_button.get_active():
            self.set_preview_from_filename( self.iconselection_image.get_filename() )
    
    def on_iconselection_stock_changed(self, combobox):
        model = combobox.get_model()
        active = combobox.get_active()
        if active < 0:
            return None
        stockicon = model[active][1]
        self.set_preview_from_stock(stockicon)
        
    def on_iconselection_theme_entry_changed(self, widget):
        self.set_preview_from_name( self.iconselection_theme_entry.get_text() )
    
    def on_iconselection_theme_browse_clicked(self, button):
        self.iconselection_dialog_all.show_all()
        task = self.load_iconselection_icons()
        GObject.idle_add(task.next)
        self.iconselection_dialog_all.run()
        self.iconselection_dialog_all.hide()
        liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
        self.iconselection_iconview.set_model(liststore)
    
    def on_iconselection_image_file_set(self, widget):
        filename = widget.get_filename()
        self.set_preview_from_filename(filename)
    
    def on_iconselection_dialog1_response(self, widget, response):
        if response == 1:
            if self.iconselection_radio_stock.get_active():
                model = self.iconselection_stock.get_model()
                active = self.iconselection_stock.get_active()
                if active < 0:
                    return None
                stockicon = model[active][1]
                self.set_application_icon(stockicon, Gtk.IconSize.DIALOG)
            elif self.iconselection_radio_theme.get_active():
                name = self.iconselection_theme_entry.get_text()
                self.set_application_icon(name, Gtk.IconSize.DIALOG)
            elif self.iconselection_radio_image.get_active():
                filename = self.iconselection_image.get_filename()
                self.set_application_icon(filename, Gtk.IconSize.DIALOG)
            self.update_editor()
    
    def on_iconselection_dialog2_response(self, widget, response):
        if response == 1:
            path = self.iconselection_iconview.get_selected_items()[0]
            index = int(path.to_string())
            model = self.iconselection_iconview.get_model()
            name = model[index][1]
            self.iconselection_theme_entry.set_text(name)
    
    def on_iconselection_dialog2_search_icon_press(self, widget):
        pass
    
    def on_iconselection_dialog2_search_changed(self, widget):
        pass
        
    # Categories
    def on_categories_accessories_toggled(self, widget):
        self.update_editor()
        
    def on_categories_development_toggled(self, widget):
        self.update_editor()
        
    def on_categories_education_toggled(self, widget):
        self.update_editor()
        
    def on_categories_games_toggled(self, widget):
        self.update_editor()
        
    def on_categories_graphics_toggled(self, widget):
        self.update_editor()
        
    def on_categories_internet_toggled(self, widget):
        self.update_editor()
        
    def on_categories_multimedia_toggled(self, widget):
        self.update_editor()
        
    def on_categories_office_toggled(self, widget):
        self.update_editor()
        
    def on_categories_settings_toggled(self, widget):
        self.update_editor()
        
    def on_categories_system_toggled(self, widget):
        self.update_editor()
        
    def on_categories_wine_toggled(self, widget):
        self.update_editor()
    # -- End Events -------------------------------------------------- #
    
  # Helper Functions
    def set_undo_enabled(self, enabled):
        self.toolbar_undo.set_sensitive(enabled)
        
    def get_undo_enabled(self):
        return self.toolbar_undo.get_sensitive()
        
    def set_redo_enabled(self, enabled):
        self.toolbar_redo.set_sensitive(enabled)
        
    def get_redo_enabled(self):
        return self.toolbar_redo.get_sensitive()
        
    def set_save_enabled(self, enabled):
        self.toolbar_save.set_sensitive(enabled)
        
    def get_save_enabled(self):
        return self.toolbar_save.get_sensitive()
    
    def set_revert_enabled(self, enabled):
        self.toolbar_revert.set_sensitive(enabled)
        
    def get_revert_enabled(self):
        return self.toolbar_revert.get_sensitive()
  
    def set_application_icon(self, icon_name, size):
        """Set the application icon."""
        if icon_name == None:
            icon_name = 'gtk-missing-image'
        elif icon_name in Applications.stock_icons:
            self.general_icon_image.set_from_stock( icon_name, size )
            
            self.iconselection_radio_stock.set_active(True)
            #self.iconselection_stock.set_sensitive(True)
            model = self.iconselection_stock.get_model()
            for i in range(len(model)):
                if model[i][1] == icon_name:
                    self.iconselection_stock.set_active(i)
                    break
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
        icon_name = self.general_icon_image.get_icon_name()
        if icon_name[0]: 
            return icon_name[0]
        icon_name = self.general_icon_image.get_stock()
        if icon_name[0]:
            return icon_name[0]
        if self.iconselection_radio_image.get_active():
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
        return self.general_name_label.get_label()[8:-10].replace('&amp;', '&')
    
    def set_application_comment(self, comment):
        """Set the application comment label and entry."""
        if comment == None:
            comment = ''
        self.general_comment_label.set_markup( '<i>%s</i>' % comment )
        self.general_comment_entry.set_text( comment )
    
    def get_application_comment(self):
        return self.general_comment_label.get_label()[3:-4]
    
    def set_application_command(self, command):
        """Set the application command entry."""
        if command == None:
            command = ''
        self.general_command_entry.set_text( command )
    
    def get_application_command(self):
        return self.general_command_entry.get_text()
    
    def set_application_path(self, path):
        if path == None:
            path = ''
        self.general_path_entry.set_text(path)
    
    def get_application_path(self):
        return self.general_path_entry.get_text()
    
    def set_application_terminal(self, terminal):
        if terminal == None:
            terminal = False
        self.general_terminal_switch.set_active(terminal)
        
    def get_application_terminal(self):
        return self.general_terminal_switch.get_active()
    
    def set_application_startupnotify(self, startupnotify):
        """Set the application Use startup notification switch."""
        if startupnotify == None:
            startupnotify = False
        self.general_startupnotify_switch.set_active( startupnotify )
    
    def get_application_startupnotify(self):
        return self.general_startupnotify_switch.get_active()
        
    def set_application_hidden(self, hidden):
        self.general_nodisplay_switch.set_active( hidden )
        
    def get_application_hidden(self):
        return self.general_nodisplay_switch.get_active()
    
    def set_application_filename(self, filename):
        self.general_filename_label.set_markup('<small>%s</small>' % filename)
        
    def get_application_filename(self):
        label = self.general_filename_label.get_label()
        return label.rstrip('</small>').lstrip('<small>')
        
    def set_application_categories(self, categories):
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
        self.editor_textview.get_buffer().set_text(text)
    
    def get_application_text(self):
        buffer = self.editor_textview.get_buffer()
        return buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
    
    def revert_changes(self):
        pass
    
    def set_preview_from_stock(self, stockicon):
        if stockicon == None:
            stockicon = 'gtk-missing-image'
        self.preview128.set_from_stock(stockicon, Gtk.IconSize.UNITY)
        self.preview48.set_from_stock(stockicon, Gtk.IconSize.DIALOG)
        self.preview32.set_from_stock(stockicon, Gtk.IconSize.DND)
        self.preview24.set_from_stock(stockicon, Gtk.IconSize.LARGE_TOOLBAR)
        self.preview16.set_from_stock(stockicon, Gtk.IconSize.MENU)

    def set_preview_from_name(self, name):
        if name == None or len(name) == 0:
            self.set_preview_from_stock('gtk-missing-image')
        else:
            self.preview128.set_from_icon_name( name, Gtk.IconSize.UNITY )
            self.preview48.set_from_icon_name( name, Gtk.IconSize.DIALOG )
            self.preview32.set_from_icon_name( name, Gtk.IconSize.DND )
            self.preview24.set_from_icon_name( name, Gtk.IconSize.LARGE_TOOLBAR )
            self.preview16.set_from_icon_name( name, Gtk.IconSize.MENU )
            
    def set_preview_from_filename(self, filename):
        if filename == None:
            self.set_preview_from_stock('gtk-missing-image')
        else:
            self.preview128.set_from_pixbuf( icon_theme.get_theme_GdkPixbuf(filename, Gtk.IconSize.UNITY) )
            self.preview48.set_from_pixbuf( icon_theme.get_theme_GdkPixbuf(filename, Gtk.IconSize.DIALOG) )
            self.preview32.set_from_pixbuf( icon_theme.get_theme_GdkPixbuf(filename, Gtk.IconSize.DND) )
            self.preview24.set_from_pixbuf( icon_theme.get_theme_GdkPixbuf(filename, Gtk.IconSize.LARGE_TOOLBAR) )
            self.preview16.set_from_pixbuf( icon_theme.get_theme_GdkPixbuf(filename, Gtk.IconSize.MENU) )
        
    # -- End Helper Functions ---------------------------------------- #
    
    def general_name_modify_accept(self):
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
        self.hide_general_name_editor()
        self.general_name_entry.set_text(self.get_application_name())
    
    def general_comment_modify_accept(self):
        self.set_application_comment( self.general_comment_entry.get_text())
        self.hide_general_comment_editor()
        self.update_editor()
    
    def general_comment_modify_reject(self):
        self.hide_general_comment_editor()
        self.general_comment_entry.set_text( self.get_application_comment() )
        
    def clear_catselection_iconview(self):
        liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str, int)
        self.catselection_iconview.set_model(liststore)
        self.catselection_iconview.set_pixbuf_column(0)
        self.catselection_iconview.set_text_column(1)
        return liststore
        
    def clear_appselection_iconview(self):
        liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str, int, str)
        self.appselection_iconview.set_model(liststore)
        self.appselection_iconview.set_pixbuf_column(0)
        self.appselection_iconview.set_text_column(1)
        return liststore
        
    def show_catselection(self):
        self.appsettings_notebook.hide()
        self.appselection_search_fail.hide()
        self.appselection.hide()
        self.catselection.show()
    
    def show_appselection(self):
        self.appsettings_notebook.hide()
        self.appselection_search_fail.hide()
        self.catselection.hide()
        self.appselection.show()
        
    def show_appsettings(self):
        self.appselection_search_fail.hide()
        self.appselection.hide()
        self.catselection.hide()
        self.appsettings_notebook.show()
        
    def show_selection_fail(self):
        self.appselection.hide()
        self.appsettings_notebook.hide()
        self.catselection.hide()
        self.appselection_search_fail.show()
        
    def show_general_name_editor(self):
        self.general_name_button.set_visible(False)
        self.general_name_modify_box.set_visible(True)
        self.set_focus( self.general_name_entry )
        
    def hide_general_name_editor(self):
        self.general_name_modify_box.set_visible(False)
        self.general_name_button.set_visible(True)
        self.set_focus( self.general_name_button )
        
    def show_general_comment_editor(self):
        self.general_comment_button.set_visible(False)
        self.general_comment_modify_box.set_visible(True)
        self.set_focus( self.general_comment_entry )
        
    def hide_general_comment_editor(self):
        self.general_comment_modify_box.set_visible(False)
        self.general_comment_button.set_visible(True)
        self.set_focus( self.general_comment_button )
        
    def set_categories_expanded(self, expanded):
        self.categories_expander.set_expanded(expanded)
        
        
    def load_category_into_iconview(self, category=None):
        
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
                    name = app.get_name()
                    appid = app.get_id()
                    comment = app.get_comment()
                    model.append( [icon, name, appid, comment] )
            self.category = category
            
                    
    def set_breadcrumb_category(self, category):
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
        liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
        self.iconselection_iconview.set_model(liststore)
        self.iconselection_iconview.set_pixbuf_column(0)
        self.iconselection_iconview.set_text_column(1)
        while Gtk.events_pending(): Gtk.main_iteration()
        icons = icon_theme.get_all_icons(Gtk.IconSize.DIALOG).keys()
        icons = sorted(icons, key=lambda icon: icon.lower())
        for icon in icons:
            if 'action' not in icon:
                liststore.append( [icon_theme.get_theme_GdkPixbuf(icon, Gtk.IconSize.DIALOG), icon] )
            yield True
        yield False

    def get_icon_pixbuf(self, icon_name, IconSize):
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

    def edited_cb(self, cell, path, new_text, user_data):
        """Quicklist treeview cell edited callback function."""
        quicklists = self.get_application_quicklists()
        treeview, column = user_data
        liststore = treeview.get_model()
        liststore[path][column] = new_text
        self.update_editor()
    
    def update_editor(self, editor_updated=False):
        task = self.threaded_update_editor(editor_updated)
        if task != None:
            GObject.idle_add(task.next)
    
    def get_data_from_editor(self):
        editor_data = {'icon': None, 'name': None, 'comment': None, 
                       'command': None, 'path': None, 'terminal': None, 
                       'startupnotify': None, 'quicklists': dict()}
        
        action_order = 0
        text = self.get_application_text()
        return Applications.read_desktop_file(self.get_application_filename(), text)
        
    def threaded_update_editor(self, editor_updated):
        if not self.update_pending:
            while Gtk.events_pending(): Gtk.main_iteration()
            
            
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
                
    def set_editor_line(self, buffer):
        self.update_editor(True)
        #row = textiter.get_line()
        #self.editor_line = row
        #self.editor_changed = True
        #self.update_editor()

    def get_quicklist_strings(self):
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
        #print self.undo_stack
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
        self.set_breadcrumb_application(1337)
        #app = self.apps[selection_id]
        
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
