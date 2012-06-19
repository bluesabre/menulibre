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

from gi.repository import Gtk, GdkPixbuf # pylint: disable=E0611
import logging
logger = logging.getLogger('menulibre')

from menulibre_lib import Window, menus
from menulibre.AboutMenulibreDialog import AboutMenulibreDialog
from menulibre.PreferencesMenulibreDialog import PreferencesMenulibreDialog

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
        
        self.image_icon = self.builder.get_object('image_icon')
        
        self.label_appname = self.builder.get_object('label_appname')
        self.entry_appname = self.builder.get_object('entry_appname')
        self.label_appcomment = self.builder.get_object('label_appcomment')
        self.entry_appcomment = self.builder.get_object('entry_appcomment')
        
        self.entry_command = self.builder.get_object('entry_command')
        self.entry_directory = self.builder.get_object('entry_directory')
        
        self.apps = menus.Applications()
        for category in self.apps.Applications.keys():
            image = self.treeview_menus.render_icon( 'gtk-missing-image', Gtk.IconSize.SMALL_TOOLBAR )
            piter = treestore.append(None, [image, category, None])
            for app in self.apps.Applications[category]:
                icon = app.get_icon()
                if os.path.isfile(icon):
                    image = GdkPixbuf.Pixbuf.new_from_file(icon)
                    size = Gtk.icon_size_lookup(Gtk.IconSize.SMALL_TOOLBAR)
                    image = image.scale_simple(size[1], size[2], GdkPixbuf.InterpType.BILINEAR)
                else:
                    icontheme = Gtk.IconTheme()
                    imageinfo = icontheme.lookup_icon(icon, 18, Gtk.IconLookupFlags.USE_BUILTIN)
                    if not imageinfo:
                        image = self.treeview_menus.render_icon( 'gtk-missing-image', Gtk.IconSize.SMALL_TOOLBAR )
                    else:
                        image = icontheme.load_icon(icon, 18, Gtk.IconLookupFlags.USE_BUILTIN)
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
        
    def on_treeview_menus_cursor_changed(self, widget):
        tree_sel = widget.get_selection()
        (tm, ti) = tree_sel.get_selected()
        app = self.apps.get_app_by_id(tm.get_value(ti, 2))
        app_name = app.get_name()
        app_comment = app.get_comment()
        self.label_appname.set_markup('<big><b>%s</b></big>' % app_name)
        self.entry_appname.set_text(app_name)
        self.label_appcomment.set_markup('<i>%s</i>' % app_comment)
        self.entry_appcomment.set_text(app_name)
        self.entry_command.set_text( app.get_exec() )
        self.entry_directory.set_text( app.get_path() )
        
        icon = app.get_icon()
        if os.path.isfile(icon):
            self.image_icon.set_from_file(icon)
        else:
            self.image_icon.set_from_icon_name( app.get_icon(), Gtk.IconSize.DIALOG )
        
        

