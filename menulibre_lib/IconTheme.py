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

from menulibreconfig import get_data_file

import subprocess

home = os.getenv('HOME')

class MenulibreIconTheme:
    def __init__(self):
        self.gtk_icon_theme = Gtk.IconTheme.get_default()
        
    def get_theme_GdkPixbuf(self, name, IconSize):
		"""Return a GdkPixbuf for an icon name at size IconSize."""
		icon_flags = Gtk.IconLookupFlags.USE_BUILTIN|Gtk.IconLookupFlags.FORCE_SVG
        unused, width, height = Gtk.icon_size_lookup(IconSize)
        if os.path.isfile(name):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(name)
            return pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.HYPER)
            
        try:
            # Try to load the icon name from the theme...
            pixbuf = self.gtk_icon_theme.load_icon(name, width, icon_flags)
        except GError:
            # If that fails, split paths between category and application.
            if name.startswith("applications-"):
                try:
                    # Try the load the theme "applications-other" icon.
                    pixbuf = self.gtk_icon_theme.load_icon("applications-other", width, icon_flags)
                except GError:
                    # If that fails, fallback on our backup tango icon.
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(get_data_file("media", "applications-other.svg"), width, height)
            else:
                # Make sure the icon name doesn't have an extension...
                name = os.path.splitext(name)[0]
                try:
                    # Try the load the icon again now that the extension is gone.
                    pixbuf = self.gtk_icon_theme.load_icon(name, width, icon_flags)
                except GError:
                    try:
                        # If that fails, try using the app fallback icon.
                        pixbuf = self.gtk_icon_theme.load_icon("application-default-icon", width, icon_flags)
                    except GError:
                        try:
                            # If that fails, try using the "image-missing" icon.
                            pixbuf = self.gtk_icon_theme.load_icon("image-missing", width, icon_flags)
                        except GError:
                            # And if that fails, use the backup fallback icon.
                            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(get_data_file("media", "image-missing.svg"), width, height)

        if pixbuf.get_width() != width: pixbuf = pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.HYPER)
        return pixbuf

    def get_all_icons(self, IconSize):
		"""Return all unique icons at the given icon size."""
        return self.gtk_icon_theme.list_icons(None)
        
    def has_icon(self, icon_name):
        return icon_name in self.gtk_icon_theme.list_icons()
