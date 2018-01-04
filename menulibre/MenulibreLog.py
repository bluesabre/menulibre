#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2015 Sean Davis <smd.seandavis@gmail.com>
#   Copyright (C) 2017 OmegaPhil <OmegaPhil@startmail.com>
#
#   This program is free software: you can redistribute it and/or modify it
#   under the terms of the GNU General Public License version 3, as published
#   by the Free Software Foundation.
#
#   This program is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranties of
#   MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program.  If not, see <http://www.gnu.org/licenses/>.

import menulibre_lib


class LogDialog:
    """The MenuLibre LogWindow."""

    def __init__(self, parent):
        """Initialize all values."""
        self._parent = parent

        builder = menulibre_lib.get_builder('MenulibreWindow')

        self._log_dialog = builder.get_object('log_dialog')
        self._log_ok = builder.get_object('log_ok')
        self._log_textbuffer = builder.get_object('log_textview').get_buffer()

        # Connect the signal to destroy the LogDialog when OK is clicked
        self._log_ok.connect("clicked", self.log_close_cb)

        self._log_dialog.set_transient_for(parent)

    def log_close_cb(self, widget):
        """Destroy the LogDialog when it is OK'd."""
        self._log_dialog.destroy()

    def set_text(self, text):
        """Set the text to show in the log dialog."""
        self._log_textbuffer.set_text(text)

    def show(self):
        """Show the log dialog."""
        self._log_dialog.show()
