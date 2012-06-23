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

from gi.repository import Gtk, Gdk, GdkPixbuf, Pango # pylint: disable=E0611
import logging
logger = logging.getLogger('menulibre')

from menulibre_lib import Window, IconTheme, menus, history
from menulibre.AboutMenulibreDialog import AboutMenulibreDialog
from menulibre.PreferencesMenulibreDialog import PreferencesMenulibreDialog

icon_theme = IconTheme.CurrentTheme()
IconSize = Gtk.icon_size_lookup(Gtk.IconSize.SMALL_TOOLBAR)

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
        self.get_interface()
        self.icon_cache = dict()

        self.ignore_undo = False
        

        self.apps = menus.Applications()
        
        # We will track changes to the menu with this, and commit them when 
        # the user hits 'Save'.
        self.changes = dict()
        
        self.category_sets = dict()
        for category in self.apps.Applications.keys():
            if category == 'AudioVideo':
                cat = 'Multimedia'
                stock = 'applications-multimedia'
            elif category == 'Development':
                cat = category
                stock = 'applications-development'
            elif category == 'Education':
                cat = category
                stock = 'applications-education'
            elif category == 'Game':
                cat = 'Games'
                stock = 'applications-games'
            elif category == 'Graphics':
                cat = category
                stock = 'applications-graphics'
            elif category == 'Network':
                cat = 'Internet'
                stock = 'applications-internet'
            elif category == 'Office':
                cat = category
                stock = 'applications-office'
            elif category == 'Settings':
                cat = category
                stock = 'gtk-preferences'
            elif category == 'System':
                cat = category
                stock = 'applications-system'
            elif category == 'Utility':
                cat = 'Accessories'
                stock = 'applications-accessories'
            elif category == 'WINE':
                cat = category
                stock = 'wine'
            else:
                cat = category
                stock = 'applications-other'
            self.category_sets[cat] = [category, stock]

        self.show_applications()
        
    def get_interface(self):
        self.toolbutton_addnew = self.builder.get_object('toolbutton_addnew')
        self.menu_add = self.builder.get_object('menu_add')
        self.toolbutton_addnew.set_menu(self.menu_add)
        self.toolbutton_save = self.builder.get_object('toolbutton_save')
        self.toolbutton_undo = self.builder.get_object('toolbutton_undo')
        self.toolbutton_redo = self.builder.get_object('toolbutton_redo')
        self.entry_search = self.builder.get_object('entry_search')
    
        # Applications TreeView
        self.treeview_menus = self.builder.get_object('treeview_menus')
        treestore = Gtk.TreeStore(GdkPixbuf.Pixbuf, str, int)
        self.treeview_menus.set_model(treestore)
        tvcolumn = Gtk.TreeViewColumn('Menus')
        cell_pixbuf = Gtk.CellRendererPixbuf()
        tvcolumn.pack_start(cell_pixbuf, True)
        tvcolumn.add_attribute(cell_pixbuf, 'pixbuf', 0)
        cell_text = Gtk.CellRendererText()
        tvcolumn.pack_start(cell_text, True)
        tvcolumn.add_attribute(cell_text, 'markup', 1)
        self.treeview_menus.append_column(tvcolumn)
        
        # Launcher Settings Notebook
        self.notebook_appsettings = self.builder.get_object('notebook_appsettings')
        
        # -- General Settings Tab
        self.image_icon = self.builder.get_object('image_icon')
        self.preview48 = self.builder.get_object('preview48')
        self.preview32 = self.builder.get_object('preview32')
        self.preview24 = self.builder.get_object('preview24')
        self.preview16 = self.builder.get_object('preview16')
        self.dialog_iconsel_1 = self.builder.get_object('dialog_iconsel_1')
        self.combobox_stockicon = self.builder.get_object('combobox_stockicon')
        combobox_liststore = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
        self.combobox_stockicon.set_model(combobox_liststore)

        cell_pixbuf = Gtk.CellRendererPixbuf()
        self.combobox_stockicon.pack_start(cell_pixbuf, True)
        self.combobox_stockicon.add_attribute(cell_pixbuf, 'pixbuf', 0)

        cell_text = Gtk.CellRendererText()
        self.combobox_stockicon.pack_start(cell_text, False)
        self.combobox_stockicon.add_attribute(cell_text, 'text', 1)

        stocks = Gtk.stock_list_ids()
        stocks.sort()
        for stockicon in stocks:
            try:
                icon = self.combobox_stockicon.render_icon(stockicon, Gtk.IconSize.MENU)
                combobox_liststore.append([icon, stockicon])
            except AttributeError:
                pass

        
        self.box_appname = self.builder.get_object('box_appname')
        self.button_appname = self.builder.get_object('button_appname')
        self.label_appname = self.builder.get_object('label_appname')
        self.entry_appname = self.builder.get_object('entry_appname')
        self.entry_appname.connect('changed', self.on_tracked_entry_changed)
        self.history.register(self.entry_appname, self.set_application_name)
        
        self.box_appcomment = self.builder.get_object('box_appcomment')
        self.button_appcomment = self.builder.get_object('button_appcomment')
        self.label_appcomment = self.builder.get_object('label_appcomment')
        self.entry_appcomment = self.builder.get_object('entry_appcomment')
        self.entry_appcomment.connect('changed', self.on_tracked_entry_changed)
        self.history.register(self.entry_appcomment, self.set_application_comment)
        
        self.entry_command = self.builder.get_object('entry_command')
        self.entry_command.connect('changed', self.on_tracked_entry_changed)
        self.history.register(self.entry_command, self.set_application_command)
        self.entry_directory = self.builder.get_object('entry_directory')
        self.entry_directory.connect('changed', self.on_tracked_entry_changed)
        self.history.register(self.entry_directory, self.set_application_workingdirectory)
        
        self.switch_runinterminal = self.builder.get_object('switch_runinterminal')
        self.switch_runinterminal.connect('notify::active', self.on_tracked_switch_changed)
        self.history.register(self.switch_runinterminal, self.set_application_useterminal)
        self.switch_startupnotify = self.builder.get_object('switch_startupnotify')
        self.switch_startupnotify.connect('notify::active', self.on_tracked_switch_changed)
        self.history.register(self.switch_startupnotify, self.set_application_startupnotify)
        
        self.label_debug = self.builder.get_object('label_debug')
        
        # -- Quicklists Tab
        self.treeview_quicklists = self.builder.get_object('treeview_quicklists')
        self.history.register(self.treeview_quicklists, self.set_application_quicklists)
        
        cell_toggle = Gtk.CellRendererToggle()
        cell_toggle.connect("toggled", self.on_quicklist_toggle, self.treeview_quicklists.get_model)
        tvcolumn = Gtk.TreeViewColumn("Show", cell_toggle, active=0)
        self.treeview_quicklists.append_column(tvcolumn)
        
        tvcolumn = Gtk.TreeViewColumn('Name')
        text_render_name = Gtk.CellRendererText()
        text_render_name.set_property('editable', True)
        text_render_name.connect('edited', self.edited_cb, (self.treeview_quicklists.get_model, 1))
        tvcolumn.pack_start(text_render_name, True)
        tvcolumn.add_attribute(text_render_name, 'text', 1)
        self.treeview_quicklists.append_column(tvcolumn)
        
        tvcolumn = Gtk.TreeViewColumn('Command')
        text_render_command = Gtk.CellRendererText()
        text_render_command.set_property('editable', True)
        text_render_command.connect('edited', self.edited_cb, (self.treeview_quicklists.get_model, 2))
        tvcolumn.pack_start(text_render_command, True)
        tvcolumn.add_attribute(text_render_command, 'text', 2)
        self.treeview_quicklists.append_column(tvcolumn)
        
        #self.treeview_quicklists.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK, [], Gdk.DragAction.DEFAULT|Gdk.DragAction.MOVE)
        #self.treeview_quicklists.enable_model_drag_dest([], Gdk.DragAction.DEFAULT)
        #self.treeview_quicklists.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.DEFAULT|Gdk.DragAction.MOVE)
        
        # -- Editor Tab
        self.textview_editor = self.builder.get_object('textview_editor')
        self.textview_editor.connect('key-press-event', self.on_tracked_textview_changed)
        self.history.register(self.textview_editor, self.set_application_editor)
        
        # Category View
        self.box_applicationcategory = self.builder.get_object('box_applicationcategory')
        self.image_appcategory = self.builder.get_object('image_appcategory')
        self.label_appcategory = self.builder.get_object('label_appcategory')
        self.grid_appcategory = self.builder.get_object('grid_appcategory')

    def on_combobox_stockicon_changed(self, combobox):
        model = combobox.get_model()
        active = combobox.get_active()
        if active < 0:
            return None
        stockicon = model[active][1]
        self.preview48.set_from_stock(stockicon, Gtk.IconSize.DIALOG)
        self.preview32.set_from_stock(stockicon, Gtk.IconSize.DND)
        self.preview24.set_from_stock(stockicon, Gtk.IconSize.LARGE_TOOLBAR)
        self.preview16.set_from_stock(stockicon, Gtk.IconSize.MENU)

    def on_filechooserbutton_image_file_set(self, widget):
        filename = widget.get_filename()
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
        pixbuf48 = pixbuf.scale_simple(48, 48, GdkPixbuf.InterpType.HYPER)
        self.preview48.set_from_pixbuf(pixbuf48)
        pixbuf32 = pixbuf.scale_simple(32, 32, GdkPixbuf.InterpType.HYPER)
        self.preview32.set_from_pixbuf(pixbuf32)
        pixbuf24 = pixbuf.scale_simple(24, 24, GdkPixbuf.InterpType.HYPER)
        self.preview24.set_from_pixbuf(pixbuf24)
        pixbuf16 = pixbuf.scale_simple(16, 16, GdkPixbuf.InterpType.HYPER)
        self.preview16.set_from_pixbuf(pixbuf16)


    def enable_save(self):
        self.toolbutton_save.set_sensitive(True)

    def save_app_changes(self, app_id):
        print self.changes[app_id]
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
            print self.changes[app_id][self.switch_runinterminal]
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

    def on_button_icon_clicked(self, widget):
        self.dialog_iconsel_1.show_all()
        self.dialog_iconsel_1.run()
        self.dialog_iconsel_1.hide()

    def on_toolbutton_save_clicked(self, widget):
        selection = self.treeview_menus.get_selection()
        model, iter = selection.get_selected()
        app_id = model.get_value(iter, 2)
        
        textbuffer = self.textview_editor.get_buffer()
        text = self.save_app_changes(app_id)
        textbuffer.set_text(text)
        
    def on_toolbutton_undo_clicked(self, widget):
        self.history.Undo()
    
    def on_toolbutton_redo_clicked(self, widget):
        self.history.Redo()
        
    def set_undo_enabled(self, is_enabled):
        self.toolbutton_undo.set_sensitive(is_enabled)
        
    def set_redo_enabled(self, is_enabled):
        self.toolbutton_redo.set_sensitive(is_enabled)
        
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
                    icon = icon_theme.load_icon(icon_name, Gtk.icon_size_lookup(IconSize)[1], 0)
                    return icon
                except:
                    pass
        if icon_name != 'gtk-missing-image':
            return self.get_icon_pixbuf('gtk-missing-image', IconSize)
        else:
            return None

    def show_applications(self, app_filter=''):
        treestore = Gtk.TreeStore(GdkPixbuf.Pixbuf, str, int)
        keys = self.category_sets.keys()
        keys.sort()
        category_id = -1
        for key in keys:
            cat = key
            category, stock = self.category_sets[key]
            if app_filter != '':
                show_category = False
                for app in self.apps.Applications[category]:
                    if app_filter in app.get_name().lower():
                        show_category = True
                        break
            else:
                show_category = True
            if show_category:
                image = self.get_icon_pixbuf(stock, Gtk.IconSize.LARGE_TOOLBAR)
                piter = treestore.append(None, [image, cat, category_id])
                category_id -= 1
                app_pairs = []
                for app in self.apps.Applications[category]:
                    app_pairs.append( [app.get_name(), app] )
                app_pairs = sorted(app_pairs, key=lambda app_pair: app_pair[0].lower())
                for app_pair in app_pairs:
                    app = app_pair[1]
                    icon_name = app.get_icon()
                    appid = app.get_id()
                    try:
                        image = self.icon_cache[appid]
                    except KeyError:
                        image = self.icon_cache[appid] = self.get_icon_pixbuf(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
                    if app_filter in app.get_name().lower():
                        if app.get_hidden():
                            treestore.append(piter, [image, '<i>%s</i>' % app.get_name(), app.get_id()])
                        else:
                            treestore.append(piter, [image, app.get_name(), app.get_id()])
        self.treeview_menus.set_model(treestore)
        if app_filter != '':
            self.treeview_menus.expand_all()
        else:
            self.treeview_menus.collapse_all()
        self.treeview_menus.set_cursor_on_cell( Gtk.TreePath.new_from_string( '0' ), None, None, False )
        
    def history_appname(self, data):
        replace_string = data
        new_text = '<big><b>%s</b></big>' % replace_string
        self.label_appname.set_markup(new_text)
        self.button_appname.show()
        self.box_appname.hide()
        
    def get_selected_appid(self):
        tree_sel = self.treeview_menus.get_selection()
        (tm, ti) = tree_sel.get_selected()
        appid = tm.get_value(ti, 2)
        return appid
        
    def on_button_appname_clicked(self, widget):
        self.edit_string = self.entry_appname.get_text()
        self.button_appname.hide()
        self.box_appname.show()
        self.set_focus(self.entry_appname)
        
    def on_entry_appname_modify(self, widget):
        new_string = self.entry_appname.get_text()
        self.history.add_event(self.get_path(), self.entry_appname, self.edit_string, new_string)
        new_text = '<big><b>%s</b></big>' % new_string
        self.label_appname.set_markup(new_text)
        self.box_appname.hide()
        self.button_appname.show()
        
    def on_entry_appname_cancel(self, widget):
        self.box_appname.hide()
        self.button_appname.show()
        try:
            self.entry_appname.set_text(self.edit_string)
        except TypeError:
            pass
        self.edit_string = None
        
    def on_entry_appname_key_press_event(self, widget, event):
        if Gdk.keyval_name(event.get_keyval()[1]) == 'Escape':
            self.on_entry_appname_cancel(widget)
        
    def on_button_appcomment_clicked(self, widget):
        self.edit_string = self.entry_appcomment.get_text()
        self.button_appcomment.hide()
        self.box_appcomment.show()
        self.set_focus(self.entry_appcomment)
        
    def on_entry_appcomment_modify(self, widget):
        new_text = '<i>%s</i>' % self.entry_appcomment.get_text()
        self.history.add_event(self.get_path(), self.entry_appcomment, self.edit_string, new_text)
        self.label_appcomment.set_markup(new_text)
        self.box_appcomment.hide()
        self.button_appcomment.show()
        
    def on_entry_appcomment_cancel(self, widget):
        self.box_appcomment.hide()
        self.button_appcomment.show()
        try:
            self.entry_appcomment.set_text(self.edit_string)
        except TypeError:
            pass
        self.edit_string = None
        
    def on_entry_appcomment_key_press_event(self, widget, event):
        if Gdk.keyval_name(event.get_keyval()[1]) == 'Escape':
            self.on_entry_appcomment_cancel(widget)
        
    def on_treeview_menus_cursor_changed(self, widget):
        app_filter = self.entry_search.get_text()
        try:
            tree_sel = widget.get_selection()
            (tm, ti) = tree_sel.get_selected()
            label = tm.get_value(ti, 1)
            appid = tm.get_value(ti, 2)
            grid_location = 0
            if appid < 0:
                self.clear_category_grid()
                app_cat, stock_icon = self.category_sets[label]
                apps = self.apps.Applications[app_cat]
                self.set_category_icon( stock_icon, Gtk.IconSize.DIALOG )
                self.set_category_name( label )
                for app in sorted(apps, key=lambda app: app.get_name().lower()):
                    app_name = app.get_name()
                    if app_filter in app_name.lower():
                        app_icon = app.get_icon()
                        app_id = app.get_id()
                        if grid_location == 0:
                            last_button = self.add_category_application(None, app_icon, app_name, app_id)
                            grid_location = 1
                        else:
                            self.add_category_application(last_button, app_icon, app_name, app_id)
                            grid_location = 0
                if app_filter == '':
                    if grid_location == 0:
                        self.add_category_application(None, 'gtk-add', '<b>Add Launcher</b>', 0)
                        grid_location = 1
                    else:
                        self.add_category_application(last_button, 'gtk-add', '<b>Add Launcher</b>', 0)
                self.notebook_appsettings.hide()
                self.box_applicationcategory.show()
            else:
                self.ignore_changes = True
                app = self.apps.get_app_by_id(appid)
                
                # General Settings
                self.set_application_icon( app.get_icon(), Gtk.IconSize.DIALOG )
                try:
                    self.set_application_name( self.changes[appid][self.entry_appname] )
                except KeyError:
                    self.set_application_name( app.get_name() )
                try:
                    self.set_application_comment( self.changes[appid][self.entry_appcomment] )
                except KeyError:
                    self.set_application_comment( app.get_comment() )
                try:
                    self.set_application_command( self.changes[appid][self.entry_command] )
                except KeyError:
                    self.set_application_command( app.get_exec() )
                try:
                    self.set_application_workingdirectory( self.changes[appid][self.entry_directory] )
                except KeyError:
                    self.set_application_workingdirectory( app.get_path() )
                try:
                    self.set_application_useterminal( self.changes[appid][self.switch_runinterminal] )
                except KeyError:
                    self.set_application_useterminal( app.get_terminal() )
                try:
                    self.set_application_startupnotify( self.changes[appid][self.switch_startupnotify] )
                except KeyError:
                    self.set_application_startupnotify( app.get_startupnotify() )
                self.set_application_filename( app.filename )
                
                # Quicklists
                try:
                    self.set_application_quicklists( self.changes[appid][self.treeview_quicklists] )
                except KeyError:
                    self.set_application_quicklists( app.get_quicklists() )
                
                # Editor
                try:
                    self.set_application_editor( self.changes[appid][self.textview_editor] )
                except KeyError:
                    self.set_application_editor( app.original )
                
                self.box_applicationcategory.hide()
                self.notebook_appsettings.show()
                self.ignore_changes = False

            
        except AttributeError:
            self.set_application_quicklists( [] )
            pass
        except TypeError:
            try:
                self.set_application_quicklists( [] )
            except AttributeError:
                pass
            pass
            
    def get_path(self):
        tree_sel = self.treeview_menus.get_selection()
        (treestore, treeiter) = tree_sel.get_selected()
        path = treestore.get_path(treeiter)
        return path
            
    def set_category_icon(self, icon_name, size):
        """Set the category view icon."""
        if os.path.isfile( icon_name ):
            self.image_appcategory.set_from_file( icon_name )
        else:
            self.image_appcategory.set_from_icon_name( icon_name, size )
            
    def set_category_name(self, name):
        """Set the category view label."""
        self.label_appcategory.set_markup(
                                    '<big><big><b>%s</b></big></big>' % name)
                                    
    def add_category_application(self, previous_button, icon, name, id):
        """Add an application button the category view."""
        button = self.get_application_button( icon, '<small>%s</small>' % name,
                                              20, id )
        if not previous_button:
            self.grid_appcategory.add(button)
        else:
            self.grid_appcategory.attach_next_to(button, previous_button, 
                                                 Gtk.PositionType.RIGHT, 1, 1)
        return button
                                    
    def clear_category_grid(self):
        """Remove all items from the category application grid."""
        for child in self.grid_appcategory.get_children():
            self.grid_appcategory.remove(child)
            
    def set_application_icon(self, icon_name, size):
        """Set the application icon."""
        if os.path.isfile( icon_name ):
            self.image_icon.set_from_file( icon_name )
        else:
            self.image_icon.set_from_icon_name( icon_name, size )
            
    def set_application_name(self, name):
        """Set the application name label and entry."""
        self.label_appname.set_markup( '<big><b>%s</b></big>' % name )
        self.entry_appname.set_text( name )
        
    def set_application_comment(self, comment):
        """Set the application comment label and entry."""
        self.label_appcomment.set_markup( '<i>%s</i>' % comment )
        self.entry_appcomment.set_text( comment )
        
    def set_application_command(self, command):
        """Set the application command entry."""
        self.entry_command.set_text( command )
        
    def set_application_workingdirectory(self, path):
        """Set the application working directory entry."""
        self.entry_directory.set_text( path )
        
    def set_application_useterminal(self, is_terminal_app):
        """Set the application Run in terminal switch."""
        self.switch_runinterminal.set_active( is_terminal_app )
        
    def set_application_startupnotify(self, notify):
        """Set the application Use startup notification switch."""
        self.switch_startupnotify.set_active( notify )
        
    def set_application_filename(self, filename):
        """Set the application filename."""
        self.label_debug.set_markup( '<small>%s</small>' % filename )
        
    def set_application_quicklists(self, quicklist_sets=[]):
        """Set the application quicklists treeview."""
        listmodel = Gtk.ListStore(bool, str, str)
        for pair in quicklist_sets:
            enabled, name, command = pair
            listmodel.append([enabled, name, command])
        self.treeview_quicklists.set_model(listmodel)
        
    def set_application_editor(self, text):
        """Set the application editor to the contents of its desktop file."""
        if isinstance(text, list):
            text = '\n'.join(text)
        buffer = self.textview_editor.get_buffer()
        buffer.set_text(text)
            
    def get_application_button(self, icon_name, markup, markup_length=20, app_id=0):
        app_box = Gtk.Box()
        app_box.set_orientation(Gtk.Orientation.VERTICAL)
        image = Gtk.Image()
        image.set_from_icon_name( icon_name, Gtk.IconSize.DIALOG )
        label = Gtk.Label()
        label.set_markup(markup)
        label.set_width_chars(markup_length+2)
        label.set_max_width_chars(markup_length)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        app_box.pack_start(image, True, True, 0)
        app_box.pack_start(label, True, True, 0)
        app_box.show_all()
        button = Gtk.Button()
        button.add(app_box)
        button.set_relief(Gtk.ReliefStyle.NONE)
        #button.set_tooltip(app.get_name())
        button.show()
        button.connect('clicked', self.on_categoryapp_clicked, app_id)
        return button
        
    def set_cursor_by_path(self, path):
        self.treeview_menus.set_cursor_on_cell( path, None, None, False )
        
    def on_categoryapp_clicked(self, widget, appid):
        tree_sel = self.treeview_menus.get_selection()
        
        (treestore, treeiter) = tree_sel.get_selected()
        child = treestore.iter_children(treeiter)
        path_counter = 0
        for i in range(len(treestore)):
            if treestore.get_value(child, 2) == appid:
                path, column = self.treeview_menus.get_cursor()
                self.treeview_menus.expand_row(path, False)
                self.treeview_menus.set_cursor_on_cell( Gtk.TreePath.new_from_string( path.to_string() + ':' + str(path_counter) ), None, None, False )
                return
            else:
                child = treestore.iter_next(child)
                path_counter += 1
        
    def on_entry_search_changed(self, widget):
        text = widget.get_text()
        if text == '':
            widget.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, None)
        else:
            widget.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, 'gtk-clear')
        self.show_applications(widget.get_text())
        
    def on_entry_search_icon_press(self, widget, button=None, other=None):
        if button == Gtk.EntryIconPosition.SECONDARY:
            self.entry_search.set_text('')
            
    def on_quicklist_toggle(self, widget, path, get_model):
        model = get_model()
        model[path][0] = not model[path][0]
        
    def edited_cb(self, cell, path, new_text, user_data):
        """Quicklist treeview cell edited callback function."""
        quicklists = self.get_quicklists()
        get_model, column = user_data
        liststore = get_model()
        liststore[path][column] = new_text
        self.history.add_event(self.get_path(), self.treeview_quicklists, quicklists, self.get_quicklists())
        return
            
    def on_button_quicklist_add_clicked(self, widget):
        #self.on_tracked_entry_changed(None, 'quicklists')
        quicklists = self.get_quicklists()
        listmodel = self.treeview_quicklists.get_model()
        listmodel.append([False, '', ''])
        self.treeview_quicklists.set_cursor_on_cell( Gtk.TreePath.new_from_string( str(len(listmodel)-1) ), None, None, False )
        self.on_tracked_quicklists_changed(widget)
        self.history.add_event(self.get_path(), self.treeview_quicklists, quicklists, self.get_quicklists())
        
    def on_button_quicklist_remove_clicked(self, widget):
        if len(self.treeview_quicklists.get_model()) > 0:
            #self.on_tracked_entry_changed(None, 'quicklists')
            quicklists = self.get_quicklists()
            tree_sel = self.treeview_quicklists.get_selection()
            (treestore, treeiter) = tree_sel.get_selected()
            treestore.remove(treeiter)
            self.on_tracked_quicklists_changed(widget)
            self.history.add_event(self.get_path(), self.treeview_quicklists, quicklists, self.get_quicklists())
        
    def on_button_quicklist_up_clicked(self, widget):
        if len(self.treeview_quicklists.get_model()) > 0:
            tree_sel = self.treeview_quicklists.get_selection()
            (treestore, treeiter) = tree_sel.get_selected()
            path = treestore.get_path(treeiter)
            if int(str(path)) > 0:
                #self.on_tracked_entry_changed(None, 'quicklists')
                quicklists = self.get_quicklists()
                up = treestore.iter_previous(treeiter)
                enabled = treestore.get_value(treeiter, 0)
                name = treestore.get_value(treeiter, 1)
                command = treestore.get_value(treeiter, 2)
                treestore.remove(treeiter)
                treestore.insert_before(up, [enabled, name, command])
                self.treeview_quicklists.set_cursor_on_cell( Gtk.TreePath.new_from_string( str(int(str(path))-1) ), None, None, False )
                self.on_tracked_quicklists_changed(widget)
                self.history.add_event(self.get_path(), self.treeview_quicklists, quicklists, self.get_quicklists())
        
    def on_button_quicklist_down_clicked(self, widget):
        if len(self.treeview_quicklists.get_model()) > 0:
            tree_sel = self.treeview_quicklists.get_selection()
            (treestore, treeiter) = tree_sel.get_selected()
            path = treestore.get_path(treeiter)
            if int(str(path)) < len(treestore)-1:
                #self.on_tracked_entry_changed(None, 'quicklists')
                quicklists = self.get_quicklists()
                down = treestore.iter_next(treeiter)
                enabled = treestore.get_value(treeiter, 0)
                name = treestore.get_value(treeiter, 1)
                command = treestore.get_value(treeiter, 2)
                treestore.remove(treeiter)
                treestore.insert_after(down, [enabled, name, command])
                self.treeview_quicklists.set_cursor_on_cell( Gtk.TreePath.new_from_string( str(int(str(path))+1) ), None, None, False )
                self.on_tracked_quicklists_changed(widget)
                self.history.add_event(self.get_path(), self.treeview_quicklists, quicklists, self.get_quicklists())
            
    def on_treeview_quicklists_drag_data_get(self, treeview, context, selection, target_id, etime):
        print "Drag Data GET"
        treeselection = treeview.get_selection()
        model, iter = treeselection.get_selected()
        enabled = model.get_value(iter, 0)
        name = model.get_value(iter, 1)
        command = model.get_value(iter, 2)
        selection.set(selection.target, 8, [enabled, name, command])
        
    def on_treeview_quicklists_drag_data_received(self, treeview, context, x, y, selection, info, etime):
        print "Drag Data RECEIVE"
        model = treeview.get_model()
        data = selection.data
        drop_info = treeview.get_dest_row_at_pos(x, y)
        if drop_info:
            path, position = drop_info
            iter = model.get_iter(path)
            if (position == Gtk.TreeViewDropPosition.BEFORE or position == Gtk.TreeViewDropPosition.INTO_OR_BEFORE):
                model.insert_before(iter, [data])
            else:
                model.insert_after(iter, [data])
        else:
            model.append([data])
        if context.action == Gtk.DropAction.MOVE:
            context.finish(True, True, etime)
        return
        
    def add_tracked_change(self, widget, data):
        if not self.ignore_changes:
            selection = self.treeview_menus.get_selection()
            model, iter = selection.get_selected()
            app_id = model.get_value(iter, 2)
            if app_id not in self.changes.keys():
                label = model.get_value(iter, 1)
                model.set_value(iter, 1, '<b>* %s</b>' % label)
                self.changes[app_id] = dict()
            if widget == self.entry_appname:
                label = model.get_value(iter, 1).split('</b>')[0].lstrip('<b>* ')
                new_label = self.entry_appname.get_text()
                if label == new_label:
                    model.set_value(iter, 1, '<b>* %s</b>' % label)
                else:
                    model.set_value(iter, 1, '<b>* %s</b> (%s)' % (label, new_label))
            self.changes[app_id][widget] = data
        
    def on_tracked_quicklists_changed(self, widget):
        self.add_tracked_change( self.treeview_quicklists, self.get_quicklists() )
        
    def get_quicklists(self):
        model = self.treeview_quicklists.get_model()
        iter = model.get_iter_first()
        quicklists = []
        while iter != None:
            enabled = model.get_value(iter, 0)
            name = model.get_value(iter, 1)
            command = model.get_value(iter, 2)
            quicklists.append( [enabled, name, command] )
            iter = model.iter_next(iter)
        return quicklists
            
        
    def on_tracked_textview_changed(self, widget, event):
        buffer = widget.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        selection = self.treeview_menus.get_selection()
        model, iter = selection.get_selected()
        app_id = model.get_value(iter, 2)
        try:
            if self.textview_editor not in self.changes[app_id].keys():
                app = self.apps.get_app_by_id(app_id)
                old_text = app.original
            else:
                old_text = self.changes[app_id][self.textview_editor]
        except KeyError:
            app = self.apps.get_app_by_id(app_id)
            old_text = app.original
        self.add_tracked_change(widget, text)
        self.history.add_event(self.get_path(), self.textview_editor, old_text, text)
        
    def on_tracked_entry_changed(self, widget):
        self.add_tracked_change(widget, widget.get_text())
            
    def on_tracked_switch_changed(self, widget, event):
        selection = self.treeview_menus.get_selection()
        model, iter = selection.get_selected()
        app_id = model.get_value(iter, 2)
        if not self.ignore_undo:
            self.history.add_event( self.get_path(), widget, not widget.get_active(), widget.get_active() )
        self.add_tracked_change(widget, widget.get_active())
            

