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

Gtk.IconSize.UNITY = Gtk.icon_size_register('UNITY', 128, 128)

# See menulibre_lib.Window.py for more details about how this class works
class MenulibreWindow(Window):
    __gtype_name__ = "MenulibreWindow"
    
    #(TARGET_ENTRY_BOOL, TARGET_ENTRY_NAME, TARGET_ENTRY_COMMAND) = range(3)
    #(COLUMN_BOOL, COLUMN_TEXT_NAME, COLUMN_TEXT_COMMAND) = range(3)
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(MenulibreWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutMenulibreDialog
        self.PreferencesDialog = PreferencesMenulibreDialog
        
        self.history = history.History(self)

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
        
        self.load_category_into_iconview(None)

        self.editor_changed = False
        
    def get_interface(self):
        """Load all of the interface elements into memory so that we can
        access and interact with them."""
      # MenuLibre Window (Gtk.Window)
        # -- Toolbar (Gtk.Toolbar) -- #
        self.toolbar = self.builder.get_object('toolbar')
        context = self.toolbar.get_style_context()
        context.add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        self.toolbar_addnew = self.builder.get_object('toolbar_addnew')
        #self.menu_add = self.builder.get_object('menu_add')
        #self.toolbar_addnew.set_menu(self.menu_add)
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
        self.appselection = self.builder.get_object('appselection_scrolled')
        self.appselection_iconview = self.builder.get_object('appselection_iconview')
        self.appselection_search_fail = self.builder.get_object('appselection_search_fail')
        self.appselection_search_all_button = self.builder.get_object('appselection_search_all_button')
        
        # -- Launcher Settings (Gtk.Notebook) -- #
        self.appsettings_notebook = self.builder.get_object('appsettings_notebook')
        self.appsettings_general = self.builder.get_object('appsettings_general')
        self.appsettings_quicklists = self.builder.get_object('appsettings_quicklists')
        self.appsettings_editor = self.builder.get_object('appsettings_editor')
        
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
        self.general_filename_label = self.builder.get_object('general_filename_label')
        
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
        buffer.connect('mark_set', self.set_editor_line)
        
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
        pass
    
    def on_toolbar_save_clicked(self, button):
        selection = self.treeview_menus.get_selection()
        model, iter = selection.get_selected()
        app_id = model.get_value(iter, 2)
        
        textbuffer = self.textview_editor.get_buffer()
        text = self.save_app_changes(app_id)
        textbuffer.set_text(text)
    
    def on_toolbar_undo_clicked(self, button):
        self.history.Undo()
    
    def on_toolbar_redo_clicked(self, button):
        self.history.Redo()
    
    def on_toolbar_revert_clicked(self, button):
        pass
    
    def on_entry_search_changed(self, widget):
        text = widget.get_text()
        
        if text == '':
            if self.last_cat == None:
                self.breadcrumb_category.set_visible(False)
            self.show_appselection()
            self.breadcrumb_category.set_visible(False)
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
        if category == None:
            self.last_cat = None
        model = self.clear_appselection_iconview()
        name = "Search Results"
        icon = "gtk-find"
        pixbuf = icon_theme.get_theme_GdkPixbuf(icon, Gtk.IconSize.BUTTON)
        self.breadcrumb_category_image.set_from_pixbuf(pixbuf)
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
                model.append( [icon, name, appid] )
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
            self.load_category_into_iconview(None)
            self.breadcrumb_application.set_active(False)
            self.breadcrumb_category.set_active(False) 
            self.lock_breadcrumb = False
            self.show_appselection()
        
    def on_breadcrumb_category_clicked(self, button):
        if not self.lock_breadcrumb:
            label = self.breadcrumb_category_label.get_label()
            self.entry_search.set_placeholder_text('Search %s' % label)
            self.lock_breadcrumb = True
            self.load_category_into_iconview(self.category)
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
        
    
    def on_appselection_iconview_item_activated(self, widget, index):
        if self.iconview_single:
            self.iconview_single = False
            return
        self.iconview_single = True
        self.lock_breadcrumb = True
        try:
            model = widget.get_model()
            #label = model[index][1]
            selection_id = model[index][2]
            if selection_id <= 0:
                if selection_id == -9001:
                    self.load_category_into_iconview('')
                else:
                    for cat in self.categories:
                        if selection_id == self.categories[cat][2]:
                            self.load_category_into_iconview(cat)
                            break
            else:
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
                self.set_application_filename( app.get_filename() )
                
                # Quicklists
                self.set_application_quicklists( app.get_actions() )
                
                # Editor
                self.set_application_text( app.get_original() )
                self.show_appsettings()
        except IndexError:
            pass
        self.lock_breadcrumb = False
    
    def on_application_search_all_button_clicked(self, button):
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
        
    def on_general_name_modify_entry_key_press_event(self, widget, event):
        if Gdk.keyval_name(event.get_keyval()[1]) == 'Escape':
            self.general_name_modify_reject()
    
    def on_general_name_modify_cancel_clicked(self, button):
        self.general_name_modify_reject()
    
    def on_general_name_modify_confirm_clicked(self, button):
        self.general_name_modify_accept()
    
    def on_general_comment_button_clicked(self, button):
        self.show_general_comment_editor()
        
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
        pass
    
    def on_general_path_entry_changed(self, widget):
        self.update_editor()
    
    def on_general_path_browse_clicked(self, button):
        pass
    
    def on_general_terminal_switch_toggled(self, widget, state):
        self.update_editor()
    
    def on_general_startupnotify_switch_toggled(self, widget, state):
        self.update_editor()
    
    def on_quicklist_toggled(self, widget, path):
        model = self.quicklists_treeview.get_model()
        model[path][0] = not model[path][0]
    
    def on_quicklist_add_clicked(self, button):
        #self.on_tracked_entry_changed(None, 'quicklists')
        quicklists = self.get_application_quicklists()
        listmodel = self.quicklists_treeview.get_model()
        listmodel.append([False, 'NewShortcut', 'New Shortcut', ''])
        self.quicklists_treeview.set_cursor_on_cell( Gtk.TreePath.new_from_string( str(len(listmodel)-1) ), None, None, False )
        #self.on_tracked_quicklists_changed(button)
        #self.history.add_event(self.get_path(), self.quicklists_treeview, quicklists, self.get_application_quicklists())
    
    def on_quicklist_remove_clicked(self, button):
        if len(self.quicklists_treeview.get_model()) > 0:
            #self.on_tracked_entry_changed(None, 'quicklists')
            quicklists = self.get_application_quicklists()
            tree_sel = self.quicklists_treeview.get_selection()
            (treestore, treeiter) = tree_sel.get_selected()
            treestore.remove(treeiter)
            #self.on_tracked_quicklists_changed(button)
            #self.history.add_event(self.get_path(), self.quicklists_treeview, quicklists, self.get_application_quicklists())
    
    def on_quicklist_move_up_clicked(self, button):
        if len(self.quicklists_treeview.get_model()) > 0:
            tree_sel = self.quicklists_treeview.get_selection()
            (treestore, treeiter) = tree_sel.get_selected()
            path = treestore.get_path(treeiter)
            if int(str(path)) > 0:
                #self.on_tracked_entry_changed(None, 'quicklists')
                quicklists = self.get_application_quicklists()
                up = treestore.iter_previous(treeiter)
                enabled = treestore.get_value(treeiter, 0)
                shortcut_name = treestore.get_value(treeiter, 1)
                displayed_name = treestore.get_value(treeiter, 2)
                command = treestore.get_value(treeiter, 3)
                
                treestore.remove(treeiter)
                treestore.insert_before(up, [enabled, shortcut_name, displayed_name, command])
                self.quicklists_treeview.set_cursor_on_cell( Gtk.TreePath.new_from_string( str(int(str(path))-1) ), None, None, False )
                #self.on_tracked_quicklists_changed(button)
                #self.history.add_event(self.get_path(), self.quicklists_treeview, quicklists, self.get_application_quicklists())
    
    def on_quicklist_move_down_clicked(self, button):
        if len(self.quicklists_treeview.get_model()) > 0:
            tree_sel = self.quicklists_treeview.get_selection()
            (treestore, treeiter) = tree_sel.get_selected()
            path = treestore.get_path(treeiter)
            if int(str(path)) < len(treestore)-1:
                #self.on_tracked_entry_changed(None, 'quicklists')
                quicklists = self.get_application_quicklists()
                down = treestore.iter_next(treeiter)
                enabled = treestore.get_value(treeiter, 0)
                shortcut_name = treestore.get_value(treeiter, 1)
                displayed_name = treestore.get_value(treeiter, 2)
                command = treestore.get_value(treeiter, 3)
                treestore.remove(treeiter)
                treestore.insert_after(down, [enabled, shortcut_name, displayed_name, command])
                self.quicklists_treeview.set_cursor_on_cell( Gtk.TreePath.new_from_string( str(int(str(path))+1) ), None, None, False )
                #self.on_tracked_quicklists_changed(button)
                #self.history.add_event(self.get_path(), self.quicklists_treeview, quicklists, self.get_application_quicklists())
      
    def on_editor_textview_key_press_event(self, widget, event):
        buffer = self.editor_textview.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        
        line = text.split('\n')[self.editor_line]
        for item in ['Icon=', 'Name=', 'Comment=', 'Exec=', 'TryExec=',
                     'Path=', 'StartupNotify=', 'Terminal=']:
            if item in line:
                self.editor_changed = True
                self.general_command_entry.emit("changed")
    
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
        self.general_name_label.set_markup( '<big><b>%s</b></big>' % name )
        self.general_name_entry.set_text( name )
    
    def get_application_name(self):
        return self.general_name_label.get_label().rstrip('</b></big>').lstrip('<big><b>')
    
    def set_application_comment(self, comment):
        """Set the application comment label and entry."""
        if comment == None:
            comment = ''
        self.general_comment_label.set_markup( '<i>%s</i>' % comment )
        self.general_comment_entry.set_text( comment )
    
    def get_application_comment(self):
        return self.general_comment_label.get_label().rstrip('</i>').lstrip('<i>')
    
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
    
    def set_application_filename(self, filename):
        self.general_filename_label.set_markup('<small>%s</small>' % filename)
        
    def get_application_filename(self):
        label = self.general_filename_label.get_label()
        return label.rstrip('</small>').lstrip('<small>')
    
    def set_application_quicklists(self, quicklists):
        """Set the application quicklists treeview."""
        listmodel = Gtk.ListStore(bool, str, str, str)
        lists = []
        for key in quicklists.keys():
            if key != '#format':
                shortcut_name = key
                displayed_name = quicklists[key]['name']
                enabled = quicklists[key]['enabled']
                command = quicklists[key]['command']
                order = quicklists[key]['order']
                lists.append( [enabled, shortcut_name, displayed_name, command, order] )
        lists = sorted(lists, key=lambda quicklist: quicklist[3])
        for group in lists:
            listmodel.append( group[:4] )
        self.quicklists_treeview.set_model(listmodel)
    
    def get_application_quicklists(self):
        model = self.quicklists_treeview.get_model()
        iter = model.get_iter_first()
        quicklists = []
        while iter != None:
            enabled = model.get_value(iter, 0)
            shortcut_name = model.get_value(iter, 1)
            displayed_name = model.get_value(iter, 2)
            command = model.get_value(iter, 3)
            quicklists.append( [enabled, shortcut_name, displayed_name, command] )
            iter = model.iter_next(iter)
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
        self.set_application_name( self.general_name_entry.get_text() )
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
        
    def clear_appselection_iconview(self):
        liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str, int)
        self.appselection_iconview.set_model(liststore)
        self.appselection_iconview.set_pixbuf_column(0)
        self.appselection_iconview.set_text_column(1)
        return liststore
    
    def show_appselection(self):
        self.appsettings_notebook.hide()
        self.appselection_search_fail.hide()
        self.appselection.show()
        
    def show_appsettings(self):
        self.appselection_search_fail.hide()
        self.appselection.hide()
        self.appsettings_notebook.show()
        
    def show_selection_fail(self):
        self.appselection.hide()
        self.appsettings_notebook.hide()
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
        
        
    def load_category_into_iconview(self, category=None):
        model = self.clear_appselection_iconview()
        if category == None:
            # Home View
            self.entry_search.set_placeholder_text('Search Applications')
            image = icon_theme.get_theme_GdkPixbuf('gtk-about', Gtk.IconSize.DIALOG)
            model.append([image, 'Show All', -9001])
            categories = self.categories.values()
            categories = sorted(categories, key=lambda category: category[0].lower())
            for category in categories:
                label, image, category_id, apps = category
                image = icon_theme.get_theme_GdkPixbuf(image, Gtk.IconSize.DIALOG)
                model.append([image, label, category_id])
            
        else:
            # Load specific category applications (Category View)
            if category == '':
                self.set_breadcrumb_category('all')
            else:
                self.set_breadcrumb_category(self.categories[category])
                label = self.breadcrumb_category_label.get_label()
                self.entry_search.set_placeholder_text('Search %s' % label)
            icon = self.get_icon_pixbuf( 'gtk-add', Gtk.IconSize.DIALOG)
            model.append( [icon, 'Add Launcher', 1337] )
            apps = sorted(self.apps.values(), key=lambda app: app.get_name().lower())
            for app in apps:
                if category in app.get_categories() or category == '':
                    icon = self.get_icon_pixbuf( app.get_icon()[1], Gtk.IconSize.DIALOG )
                    name = app.get_name()
                    appid = app.get_id()
                    model.append( [icon, name, appid] )
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
        app = self.apps[app_id]
        name = app.get_name()
        icon = app.get_icon()
        pixbuf = icon_theme.get_theme_GdkPixbuf(icon[1], Gtk.IconSize.BUTTON)
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
    
    def save_app_changes(self, app_id):
        if app_id not in self.changes.keys():
            return
        app = self.apps.get_app_by_id(app_id)
        try:
            text = self.changes[app_id][self.textview_editor]
        except KeyError:
            text = '\n'.join(app.original)
        if self.entry_appname in self.changes[app_id].keys():
            text = text.replace('\nName=%s' % app.get_name(), '\nName=%s' % self.changes[app_id][self.entry_appname])
        if self.entry_appcomment in self.changes[app_id].keys():
            text = text.replace('\nComment=%s' % app.get_comment(), '\nComment=%s' % self.changes[app_id][self.entry_appcomment])
        if self.entry_command in self.changes[app_id].keys():
            text = text.replace('\nExec=%s' % app.get_exec(), '\nExec=%s' % self.changes[app_id][self.entry_command])
            text = text.replace('\nTryExec=%s' % app.get_exec(), '\nTryExec=%s' % self.changes[app_id][self.entry_command])
        if self.entry_directory in self.changes[app_id].keys():
            text = text.replace('\nPath=%s' % app.get_path(), '\nPath=%s' % self.changes[app_id][self.entry_directory])
        if self.switch_runinterminal in self.changes[app_id].keys():
            if self.changes[app_id][self.switch_runinterminal] == True:
                terminal = 'true'
            else:
                terminal = 'false'
            text = text.replace('\nTerminal=%s' % str(app.get_terminal()).lower(), '\nTerminal=%s' % terminal)
        if self.switch_startupnotify in self.changes[app_id].keys():
            if self.changes[app_id][self.switch_startupnotify]:
                notify = 'true'
            else:
                notify = 'false'
            text = text.replace('\nStartupNotify=%s' % str(app.get_terminal()).lower(), '\nStartupNotify=%s' % notify)
        return text

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
        get_model, column = user_data
        liststore = get_model()
        liststore[path][column] = new_text
        self.history.add_event(self.get_path(), self.quicklists_treeview, quicklists, self.get_application_quicklists())
        return
    
    def update_editor(self):
        try:
            task = self.threaded_update_editor()
            GObject.idle_add(task.next)
        except AttributeError:
            pass
    
    def get_data_from_editor(self):
        editor_data = {'icon': None, 'name': None, 'comment': None, 
                       'command': None, 'path': None, 'terminal': None, 
                       'startupnotify': None}
        
        text = self.get_application_text()
        for line in text.split('\n'):
            if line[:5] == 'Icon=':
                editor_data['icon'] = line[5:]
            elif line[:5] == 'Name=':
                if editor_data['name'] == None:
                    editor_data['name'] = line[5:]
            elif line[:8] == 'Comment=':
                editor_data['comment'] = line[8:]
            elif line[:5] == 'Exec=':
                if editor_data['name'] == None:
                    editor_data['command'] = line[5:]
            elif line[:5] == 'Path=':
                editor_data['path'] = line[5:]
            elif line[:9] == 'Terminal=':
                editor_data['terminal'] = line[9:]
            elif line[:14] == 'StartupNotify=':
                editor_data['startupnotify'] = line[14:]
        return editor_data
        
    def threaded_update_editor(self):
        if not self.update_pending:
            while Gtk.events_pending(): Gtk.main_iteration()
            
            if self.editor_changed:
                data = self.get_data_from_editor()
                self.set_application_icon( data['icon'], Gtk.IconSize.DIALOG )
                self.set_application_name( data['name'] )
                self.set_application_comment( data['comment'] )
                self.set_application_command( data['command'] )
                self.set_application_path( data['path'] )
                self.set_application_terminal( data['terminal'] )
                self.set_application_startupnotify( data['startupnotify'] )
                self.editor_changed = False
            else:
            
                self.update_pending = True
                icon = self.get_application_icon()
                name = self.get_application_name()
                comment = self.get_application_comment()
                command = self.get_application_command()
                path = self.get_application_path()
                terminal = str(self.get_application_terminal()).lower()
                startupnotify = str(self.get_application_startupnotify()).lower()
                #filename = self.get_application_filename()
                #quicklists = self.get_application_quicklists()
                self.update_pending = False
                
                buffer = self.editor_textview.get_buffer()
                text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
                text_lines = text.split('\n')
                newlines = []
                for line in text_lines:
                    if line[:5] == 'Icon=':
                        newlines.append(line[:5] + icon)
                    elif line[:5] == 'Name=':
                        newlines.append(line[:5] + name)
                    elif line[:8] == 'Comment=':
                        newlines.append(line[:8] + comment)
                    elif line[:5] == 'Exec=':
                        newlines.append(line[:5] + command)
                    elif line[:8] == 'TryExec=':
                        newlines.append(line[:8] + command)
                    elif line[:5] == 'Path=':
                        newlines.append(line[:5] + path)
                    elif line[:9] == 'Terminal=':
                        newlines.append(line[:9] + terminal)
                    elif line[:14] == 'StartupNotify=':
                        newlines.append(line[:14] + startupnotify)
                    else: newlines.append(line)
                text = '\n'.join(newlines)
                buffer.set_text(text)
                
    def set_editor_line(self, buffer, textiter, textmark):
        row = textiter.get_line()
        self.editor_line = row
        self.editor_changed = True
        self.update_editor()
