#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2015 Sean Davis <smd.seandavis@gmail.com>
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

from locale import gettext as _

from gi.repository import Gtk

import menulibre_lib

import logging
logger = logging.getLogger('menulibre')

class AboutDialog(Gtk.AboutDialog):
    def __init__(self, parent):
        # Create and display the AboutDialog.
        Gtk.AboutDialog.__init__(self)

        # Credits
        authors = ["Sean Davis"]
        documenters = ["Sean Davis"]

        # Populate the AboutDialog with all the relevant details.
        self.set_title(_("About MenuLibre"))
        self.set_program_name(_("MenuLibre"))
        self.set_logo_icon_name("menulibre")
        self.set_copyright(_("Copyright © 2012-2015 Sean Davis"))
        self.set_authors(authors)
        self.set_documenters(documenters)
        self.set_website("https://launchpad.net/menulibre")
        self.set_version(menulibre_lib.get_version())

        # Connect the signal to destroy the AboutDialog when Close is clicked.
        self.connect("response", self.about_close_cb)
        self.set_transient_for(parent)

    def about_close_cb(self, widget, response):
        """Destroy the AboutDialog when it is closed."""
        widget.destroy()

def HelpDialog(parent):
    question = _("Do you want to read the MenuLibre manual online?")
    details = _("You will be redirected to the documentation website "
                "where the help pages are maintained.")
    dialog = Gtk.MessageDialog(transient_for=parent, modal=True,
                                message_type=Gtk.MessageType.QUESTION,
                                buttons=Gtk.ButtonsType.NONE,
                                text=question)
    dialog.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
    dialog.add_button(_("Read Online"), Gtk.ResponseType.OK)
    dialog.set_title(_("Online Documentation"))

    dialog.format_secondary_markup(details)
    if dialog.run() == Gtk.ResponseType.OK:
        help_url = "http://wiki.smdavis.us/doku.php?id=menulibre-docs"
        logger.debug("Navigating to help page, %s" % help_url)
        menulibre_lib.show_uri(parent, help_url)
    dialog.destroy()

class SaveOnCloseDialog(Gtk.MessageDialog):
    def __init__(self, parent):
        question = _("Do you want to save the changes before closing?")
        details = _("If you don't save the launcher, all the changes "
                    "will be lost.'")
        Gtk.MessageDialog.__init__ (self, transient_for=parent, modal=True,
                                    message_type=Gtk.MessageType.QUESTION,
                                    buttons=Gtk.ButtonsType.NONE,
                                    text=question)
        self.format_secondary_markup(details)
        self.set_title(_("Save Changes"))
        self.add_button(_("Don't Save"), Gtk.ResponseType.NO)
        self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        self.add_button(_("Save"), Gtk.ResponseType.YES)

class SaveOnLeaveDialog(Gtk.MessageDialog):
    def __init__(self, parent):
        question = _("Do you want to save the changes before leaving this "
                    "launcher?")
        details = _("If you don't save the launcher, all the changes "
                    "will be lost.")
        Gtk.MessageDialog.__init__ (self, transient_for=parent, modal=True,
                                    message_type=Gtk.MessageType.QUESTION,
                                    buttons=Gtk.ButtonsType.NONE,
                                    text=question)
        self.format_secondary_markup(details)
        self.set_title(_("Save Changes"))
        self.add_button(_("Don't Save"), Gtk.ResponseType.NO)
        self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        self.add_button(_("Save"), Gtk.ResponseType.YES)

class DeleteDialog(Gtk.MessageDialog):
    def __init__(self, parent, question):
        details = _("This cannot be undone.")
        Gtk.MessageDialog.__init__ (self, transient_for=parent, modal=True,
                                    message_type=Gtk.MessageType.QUESTION,
                                    buttons=Gtk.ButtonsType.OK_CANCEL,
                                    text=question)
        self.format_secondary_markup(details)

class RevertDialog(Gtk.MessageDialog):
    def __init__(self, parent, question):
        question = _("Are you sure you want to restore this launcher?")
        details = _("All changes since the last saved state will be lost "
                    "and cannot be restored automatically.")
        Gtk.MessageDialog.__init__ (self, transient_for=parent, modal=True,
                                    message_type=Gtk.MessageType.QUESTION,
                                    buttons=Gtk.ButtonsType.NONE,
                                    text=question)
        self.format_secondary_markup(details)

        self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        self.add_button(_("Restore Launcher"), Gtk.ResponseType.OK)
        self.set_title(_("Restore Launcher"))

class FileChooserDialog(Gtk.FileChooserDialog):
    def __init__(self, parent, title, action):
        Gtk.FileChooserDialog.__init__(self, title=title, transient_for=parent,
                                       action=action)
        self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        self.add_button(_("OK"), Gtk.ResponseType.OK)
