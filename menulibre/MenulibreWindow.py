# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import gettext
from gettext import gettext as _
gettext.textdomain('menulibre')

from gi.repository import Gtk # pylint: disable=E0611
import logging
logger = logging.getLogger('menulibre')

from menulibre_lib import Window
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

