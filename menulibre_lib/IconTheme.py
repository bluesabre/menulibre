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

from gi.repository import Gtk, GdkPixbuf
from gi._glib import GError
import os

import subprocess

home = os.getenv('HOME')

class MenulibreIconTheme:
    def __init__(self):
        self.gtk_icon_theme = Gtk.IconTheme.get_default()
        
    def get_theme_GdkPixbuf(self, name, IconSize):
		"""Return a GdkPixbuf for an icon name at size IconSize."""
        unused, width, height = Gtk.icon_size_lookup(IconSize)
        if os.path.isfile(name):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(name)
            return pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.HYPER)
        else:
            try:
                pixbuf = self.gtk_icon_theme.load_icon(name, width, Gtk.IconLookupFlags.USE_BUILTIN)
            except GError:
                name = os.path.splitext(name)[0]
                try:
                    pixbuf = self.gtk_icon_theme.load_icon(name, width, Gtk.IconLookupFlags.USE_BUILTIN)
                except GError:
                    if name.startswith("applications-"):
                        pixbuf = self.gtk_icon_theme.load_icon("applications-other", width, Gtk.IconLookupFlags.USE_BUILTIN)
                    else:
                        pixbuf = self.gtk_icon_theme.load_icon("application-default-icon", width, Gtk.IconLookupFlags.USE_BUILTIN)
            return pixbuf

    def get_all_icons(self, IconSize):
		"""Return all unique icons at the given icon size."""
        return self.gtk_icon_theme.list_icons()
        
    def has_icon(self, icon_name):
        return icon_name in self.gtk_icon_theme.list_icons()
