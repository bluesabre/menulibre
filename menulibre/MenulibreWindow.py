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

from gi.repository import Gtk, Gdk, GdkPixbuf # pylint: disable=E0611
import logging
logger = logging.getLogger('menulibre')

from menulibre_lib import Window, IconTheme, menus
from menulibre.AboutMenulibreDialog import AboutMenulibreDialog
from menulibre.PreferencesMenulibreDialog import PreferencesMenulibreDialog

icon_theme = IconTheme.CurrentTheme()
IconSize = Gtk.icon_size_lookup(Gtk.IconSize.SMALL_TOOLBAR)

# See menulibre_lib.Window.py for more details about how this class works
class MenulibreWindow(Window):
    __gtype_name__ = "MenulibreWindow"
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(MenulibreWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutMenulibreDialog
        self.PreferencesDialog = PreferencesMenulibreDialog

        # Code for other initialization actions should be added here.
        self.treeview_menus = self.builder.get_object('treeview_menus')
        treestore = Gtk.TreeStore(GdkPixbuf.Pixbuf, str, int)
        self.treeview_menus.set_model(treestore)
        self.notebook_appsettings = self.builder.get_object('notebook_appsettings')
        self.textview_editor = self.builder.get_object('textview_editor')
        
        self.image_icon = self.builder.get_object('image_icon')
        
        self.button_appname = self.builder.get_object('button_appname')
        self.box_appname = self.builder.get_object('box_appname')
        self.label_appname = self.builder.get_object('label_appname')
        self.entry_appname = self.builder.get_object('entry_appname')
        self.button_appcomment = self.builder.get_object('button_appcomment')
        self.box_appcomment = self.builder.get_object('box_appcomment')
        self.label_appcomment = self.builder.get_object('label_appcomment')
        self.entry_appcomment = self.builder.get_object('entry_appcomment')
        
        self.entry_command = self.builder.get_object('entry_command')
        self.entry_directory = self.builder.get_object('entry_directory')
        
        self.switch_runinterminal = self.builder.get_object('switch_runinterminal')
        self.switch_startupnotify = self.builder.get_object('switch_startupnotify')
        
        self.image_appcategory = self.builder.get_object('image_appcategory')
        
        self.label_debug = self.builder.get_object('label_debug')
        
        self.treeview_quicklists = self.builder.get_object('treeview_quicklists')
        
        self.box_applicationcategory = self.builder.get_object('box_applicationcategory')
        self.label_appcategory = self.builder.get_object('label_appcategory')
        
        self.grid_appcategory = self.builder.get_object('grid_appcategory')
        
        self.apps = menus.Applications()
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
            else:
                cat = category
                stock = 'applications-other'
            self.category_sets[cat] = [category, stock]
        keys = self.category_sets.keys()
        keys.sort()
        category_id = -1
        for key in keys:
            cat = key
            category, stock = self.category_sets[key]
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
                image = self.get_icon_pixbuf(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
                treestore.append(piter, [image, app.get_name(), app.get_id()])
                
        
                
        tvcolumn = Gtk.TreeViewColumn('Menus')
        self.treeview_menus.append_column(tvcolumn)
        pixbuf = Gtk.CellRendererPixbuf()
        tvcolumn.pack_start(pixbuf, True)
        tvcolumn.add_attribute(pixbuf, 'pixbuf', 0)
        text = Gtk.CellRendererText()
        tvcolumn.pack_start(text, True)
        tvcolumn.add_attribute(text, 'text', 1)
        
        tvcolumn.set_sort_column_id(1)
        tvcolumn.set_sort_order(Gtk.SortType.ASCENDING)
        
        
        togglerender = Gtk.CellRendererToggle()
        togglerender.connect("toggled", self.on_quicklist_toggle, self.treeview_quicklists.get_model())
        col = Gtk.TreeViewColumn("Show", togglerender, active=0)
        self.treeview_quicklists.append_column(col)
        tvcolumn = Gtk.TreeViewColumn('Name')
        text = Gtk.CellRendererText()
        tvcolumn.pack_start(text, True)
        tvcolumn.add_attribute(text, 'text', 1)
        self.treeview_quicklists.append_column(tvcolumn)
        tvcolumn = Gtk.TreeViewColumn('Command')
        text = Gtk.CellRendererText()
        tvcolumn.pack_start(text, True)
        tvcolumn.add_attribute(text, 'text', 2)
        self.treeview_quicklists.append_column(tvcolumn)
        
    def get_icon_pixbuf(self, icon_name, IconSize):
        #IconSize = Gtk.IconSize.DIALOG
        #pixbuf = None
        #if os.path.isfile(icon_name):
        #    pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_name)
        #    pixbuf = pixbuf.scale_simple(height, width, GdkPixbuf.InterpType.BILINEAR)
        #if not pixbuf:
        #    icon_info = IconTheme.lookup_icon(icon_name, IconSize, Gtk.IconLookupFlags.USE_BUILTIN)
        #    if not icon_info:
        #        icon_info = IconTheme.lookup_icon('gtk-missing-image', IconSize, Gtk.IconLookupFlags.USE_BUILTIN)
        #    pixbuf = icon_info.load_icon()
        #    return pixbuf
        #pixbuf = IconTheme.load_icon(icon_name, width, Gtk.IconLookupFlags.USE_BUILTIN)
        #return pixbuf
        icon = icon_theme.get_stock_image(icon_name, IconSize)
        if icon:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon)
            if os.path.splitext(icon)[1] == '.svg':
                ignore, height, width = Gtk.icon_size_lookup(IconSize)
                pixbuf = pixbuf.scale_simple(height, width, GdkPixbuf.InterpType.HYPER)
                # gtk.gdk.INTERP_HYPER, GdkPixbuf.InterpType.BILINEAR
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
#            try:
#                name = 'gnome-mime-' + icon_name
#                icon = icon_theme.load_icon(icon_name, Gtk.icon_size_lookup(IconSize)[1], 0)
#                return icon
#            except:
#                pass
        #            icon_name = 'gnome-mime-%s-%s' % (media, subtype)
        #            return self.get_icon_pixbuf(icon_name, icon_size)
        #        except Exception:
        #            try:
        #                # Then try generic icon
        #                icon_name = 'gnome-mime-%s' % media
#        pixbuf = self.treeview_menus.render_icon( icon_name, IconSize )
#        if not pixbuf:
#            ignore, height, width = Gtk.icon_size_lookup(IconSize)
#            if os.path.isfile(icon_name):
#                pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_name)
#                pixbuf = pixbuf.scale_simple(height, width, GdkPixbuf.InterpType.BILINEAR)
#            else:
#                imageinfo = icon_theme.lookup_icon(icon_name, width, Gtk.IconLookupFlags.USE_BUILTIN)
#                if not imageinfo:
                    #print icon_name
#                    pixbuf = self.treeview_menus.render_icon('gtk-missing-image', IconSize)
#                else:
#                    pixbuf = icon_theme.load_icon(icon_name, width, Gtk.IconLookupFlags.USE_BUILTIN)
#        return pixbuf

    def set_quicklists(self, quicklist_sets=[]):
        listmodel = Gtk.ListStore(bool, str, str)
        for pair in quicklist_sets:
            enabled, name, command = pair
            listmodel.append([enabled, name, command])
        self.treeview_quicklists.set_model(listmodel)
        
    def on_button_appname_clicked(self, widget):
        self.edit_string = self.entry_appname.get_text()
        self.button_appname.hide()
        self.box_appname.show()
        self.set_focus(self.entry_appname)
        
    def on_entry_appname_modify(self, widget):
        new_text = '<big><b>%s</b></big>' % self.entry_appname.get_text()
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
        try:
            tree_sel = widget.get_selection()
            (tm, ti) = tree_sel.get_selected()
            label = tm.get_value(ti, 1)
            appid = tm.get_value(ti, 2)
            grid_location = 0
            if appid < 0:
                for child in self.grid_appcategory.get_children():
                    self.grid_appcategory.remove(child)
                app_cat, stock_icon = self.category_sets[label]
                apps = self.apps.Applications[app_cat]
                apps = sorted(apps, key=lambda app: app.get_name().lower())
                self.image_appcategory.set_from_icon_name( stock_icon, Gtk.IconSize.DIALOG )
                self.label_appcategory.set_markup('<big><big><b>%s</b></big></big>' % label)
                for app in apps:
                    app_box = Gtk.Box()
                    app_box.set_orientation(Gtk.Orientation.VERTICAL)
                    image = Gtk.Image()
                    image.set_from_icon_name( app.get_icon(), Gtk.IconSize.LARGE_TOOLBAR )
                    label = Gtk.Label()
                    label.set_markup('<small>%s</small>' % app.get_name())
                    app_box.pack_start(image, True, True, 0)
                    app_box.pack_start(label, True, True, 0)
                    app_box.show_all()
                    if grid_location == 0:
                        last_button = Gtk.Button()
                        last_button.add(app_box)
                        last_button.set_relief(Gtk.ReliefStyle.NONE)
                        last_button.show()
                        last_button.connect('clicked', self.on_categoryapp_clicked, app.get_id())
                        self.grid_appcategory.add(last_button)
                        grid_location = 1
                    else:
                        button = Gtk.Button()
                        button.add(app_box)
                        button.set_relief(Gtk.ReliefStyle.NONE)
                        button.show()
                        button.connect('clicked', self.on_categoryapp_clicked, app.get_id())
                        self.grid_appcategory.attach_next_to(button, last_button, Gtk.PositionType.RIGHT, 1, 1)
                        grid_location = 0
                    
                self.notebook_appsettings.hide()
                self.box_applicationcategory.show()
                self.set_quicklists()
            else:
                self.box_applicationcategory.hide()
                self.notebook_appsettings.show()
                app = self.apps.get_app_by_id(tm.get_value(ti, 2))
                app_name = app.get_name()
                app_comment = app.get_comment()
                self.label_debug.set_markup('<small>%s</small>' % app.filename)
                self.label_appname.set_markup('<big><b>%s</b></big>' % app_name)
                self.entry_appname.set_text(app_name)
                self.label_appcomment.set_markup('<i>%s</i>' % app_comment)
                self.entry_appcomment.set_text(app_comment)
                self.entry_command.set_text( app.get_exec() )
                self.entry_directory.set_text( app.get_path() )
                editor_buffer = self.textview_editor.get_buffer()
                text = '\n'.join(app.original)
                editor_buffer.set_text(text)
                

                
                self.switch_runinterminal.set_active(app.get_terminal())
                self.switch_startupnotify.set_active(app.get_startupnotify())
                
                icon = app.get_icon()
                if os.path.isfile(icon):
                    self.image_icon.set_from_file(icon)
                else:
                    self.image_icon.set_from_icon_name( app.get_icon(), Gtk.IconSize.DIALOG )
                    
                self.set_quicklists(app.get_quicklists())
            
        except AttributeError:
            self.set_quicklists()
            pass
        except TypeError:
            try:
                self.set_quicklists()
            except AttributeError:
                pass
            pass
            
    def on_quicklist_toggle(self, widget):
        pass
        
    def on_categoryapp_clicked(self, widget, appid):
        print appid
            
            

