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
        
        self.label_debug = self.builder.get_object('label_debug')
        
        self.apps = menus.Applications()
        category_sets = dict()
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
            category_sets[cat] = [category, stock]
        keys = category_sets.keys()
        keys.sort()
        for key in keys:
            cat = key
            category, stock = category_sets[key]
            image = self.get_icon_pixbuf(stock, Gtk.IconSize.LARGE_TOOLBAR)
            piter = treestore.append(None, [image, cat, -1])
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
        self.button_appcomment.hide()
        self.box_appcomment.show()
        
    def on_treeview_menus_cursor_changed(self, widget):
        try:
            tree_sel = widget.get_selection()
            (tm, ti) = tree_sel.get_selected()
            appid = tm.get_value(ti, 2)
            if appid == -1:
                self.notebook_appsettings.hide()
                pass
            else:
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
                
                icon = app.get_icon()
                if os.path.isfile(icon):
                    self.image_icon.set_from_file(icon)
                else:
                    self.image_icon.set_from_icon_name( app.get_icon(), Gtk.IconSize.DIALOG )
        except AttributeError:
            pass
        except TypeError:
            pass
            
            

