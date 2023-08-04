#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2022 Sean Davis <sean@bluesabre.org>
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

import os

from locale import gettext as _

from gi.repository import Gtk

import menulibre_lib

import logging
logger = logging.getLogger('menulibre')


class AboutDialog(Gtk.AboutDialog):
    def __init__(self, parent, use_headerbar):
        Gtk.AboutDialog.__init__(self, use_header_bar=use_headerbar)
        authors = ["Sean Davis"]
        documenters = ["Sean Davis"]

        # Translators: About Dialog, window title.
        self.set_title(_("About MenuLibre"))
        self.set_program_name("MenuLibre")
        self.set_logo_icon_name("menulibre")
        self.set_copyright("Copyright © 2012-2022 Sean Davis")
        self.set_authors(authors)
        self.set_documenters(documenters)
        self.set_website("https://github.com/bluesabre/menulibre")
        self.set_version(menulibre_lib.get_version())

        # Connect the signal to destroy the AboutDialog when Close is clicked.
        self.connect("response", self.about_close_cb)
        self.set_transient_for(parent)

        # Fix weird bug with duplicate buttons
        if use_headerbar:
            headerbar = self.get_header_bar()
            for child in headerbar.get_children():
                if isinstance(child, Gtk.Button):
                    child.destroy()

    def about_close_cb(self, widget, response):
        """Destroy the AboutDialog when it is closed."""
        widget.destroy()


class HelpDialog(Gtk.MessageDialog):
    def __init__(self, parent, use_headerbar):
        # Translators: Help Dialog, window title.
        title = _("Online Documentation")
        # Translators: Help Dialog, primary text.
        primary = _("Do you want to read the MenuLibre manual online?")
        # Translators: Help Dialog, secondary text.
        secondary = _("You will be redirected to the documentation website "
                    "where the help pages are maintained.")
        buttons = [
            # Translators: Help Dialog, cancel button.
            (_("Cancel"), Gtk.ResponseType.CANCEL),
            # Translators: Help Dialog, confirmation button. Navigates to
            # online documentation.
            (_("Read Online"), Gtk.ResponseType.OK)
        ]

        Gtk.MessageDialog.__init__(self, transient_for=parent, modal=True,
                                   message_type=Gtk.MessageType.QUESTION,
                                   buttons=Gtk.ButtonsType.NONE,
                                   text=primary, use_header_bar=False)
        self.set_title(title)
        self.format_secondary_markup(secondary)
        for button in buttons:
            self.add_button(button[0], button[1])

        self.connect("response", self.response_cb)

    def response_cb(self, widget, response):
        if response == Gtk.ResponseType.OK:
            url = "https://github.com/bluesabre/menulibre/wiki"
            logger.debug("Navigating to help page, %s" % url)
            menulibre_lib.show_uri(self.get_transient_for(), url)
        widget.destroy()


class SaveOnCloseDialog(Gtk.MessageDialog):
    def __init__(self, parent, use_headerbar):
        # Translators: Save On Close Dialog, window title.
        title = _("Save Changes")
        # Translators: Save On Close Dialog, primary text.
        primary = _("Do you want to save the changes before closing?")
        # Translators: Save On Close Dialog, secondary text.
        secondary = _("If you don't save the launcher, all the changes "
                      "will be lost.")
        buttons = [
            # Translators: Save On Close Dialog, don't save, then close.
            (_("Don't Save"), Gtk.ResponseType.NO),
            # Translators: Save On Close Dialog, don't save, cancel close.
            (_("Cancel"), Gtk.ResponseType.CANCEL),
            # Translators: Save On Close Dialog, do save, then close.
            (_("Save"), Gtk.ResponseType.YES)
        ]

        Gtk.MessageDialog.__init__(self, transient_for=parent, modal=True,
                                   message_type=Gtk.MessageType.QUESTION,
                                   buttons=Gtk.ButtonsType.NONE,
                                   text=primary, use_header_bar=False)
        self.set_title(title)
        self.format_secondary_markup(secondary)
        for button in buttons:
            self.add_button(button[0], button[1])


class SaveOnLeaveDialog(Gtk.MessageDialog):
    def __init__(self, parent, use_headerbar):
        # Translators: Save On Leave Dialog, window title.
        title = _("Save Changes")
        # Translators: Save On Leave Dialog, primary text.
        primary = _("Do you want to save the changes before leaving this "
                    "launcher?")
        # Translators: Save On Leave Dialog, primary text.
        secondary = _("If you don't save the launcher, all the changes "
                      "will be lost.")
        buttons = [
            # Translators: Save On Leave Dialog, don't save, then leave.
            (_("Don't Save"), Gtk.ResponseType.NO),
            # Translators: Save On Leave Dialog, don't save, cancel leave.
            (_("Cancel"), Gtk.ResponseType.CANCEL),
            # Translators: Save On Leave Dialog, do save, then leave.
            (_("Save"), Gtk.ResponseType.YES)
        ]

        Gtk.MessageDialog.__init__(self, transient_for=parent, modal=True,
                                   message_type=Gtk.MessageType.QUESTION,
                                   buttons=Gtk.ButtonsType.NONE,
                                   text=primary, use_header_bar=False)
        self.set_title(title)
        self.format_secondary_markup(secondary)
        for button in buttons:
            self.add_button(button[0], button[1])


class DeleteDialog(Gtk.MessageDialog):
    def __init__(self, parent, primary, use_headerbar):
        # Translations: Delete Dialog, secondary text. Notifies user that
        # the file cannot be restored once deleted.
        secondary = _("This cannot be undone.")
        Gtk.MessageDialog.__init__(self, transient_for=parent, modal=True,
                                   message_type=Gtk.MessageType.QUESTION,
                                   buttons=Gtk.ButtonsType.OK_CANCEL,
                                   text=primary, use_header_bar=False)
        self.format_secondary_markup(secondary)


class RevertDialog(Gtk.MessageDialog):
    def __init__(self, parent, use_headerbar):
        # Translators: Revert Dialog, window title.
        title = _("Restore Launcher")
        # Translators: Revert Dialog, primary text. Confirmation to revert
        # all changes since the last file save.
        primary = _("Are you sure you want to restore this launcher?")
        # Translators: Revert Dialog, secondary text.
        secondary = _("All changes since the last saved state will be lost "
                      "and cannot be restored automatically.")
        buttons = [
            # Translators: Revert Dialog, cancel button.
            (_("Cancel"), Gtk.ResponseType.CANCEL),
            # Translators: Revert Dialog, confirmation button.
            (_("Restore Launcher"), Gtk.ResponseType.OK)
        ]

        Gtk.MessageDialog.__init__(self, transient_for=parent, modal=True,
                                   message_type=Gtk.MessageType.QUESTION,
                                   buttons=Gtk.ButtonsType.NONE,
                                   text=primary, use_header_bar=False)
        self.set_title(title)
        self.format_secondary_markup(secondary)
        for button in buttons:
            self.add_button(button[0], button[1])


class LauncherRemovedDialog(Gtk.MessageDialog):
    def __init__(self, parent, use_headerbar):
        # Translators: Launcher Removed Dialog, primary text. Indicates that
        # the selected application is no longer installed.
        primary = _("No Longer Installed")
        # Translators: Launcher Removed Dialog, secondary text.
        secondary = _("This launcher has been removed from the "
                      "system.\nSelecting the next available item.")

        Gtk.MessageDialog.__init__(self, transient_for=parent, modal=True,
                                   message_type=Gtk.MessageType.INFO,
                                   buttons=Gtk.ButtonsType.OK,
                                   text=primary, use_header_bar=False)
        self.format_secondary_markup(secondary)


class NotFoundInPathDialog(Gtk.MessageDialog):
    def __init__(self, parent, command, use_headerbar):
        # Translators: Not Found In PATH Dialog, primary text. Indicates
        # that the provided script was not found in any PATH directory.
        primary = _("Could not find \"%s\" in your PATH.") % command

        path = os.getenv("PATH", "").split(":")
        secondary = "<b>PATH:</b>\n%s" % "\n".join(path)
        Gtk.MessageDialog.__init__(self, transient_for=parent, modal=True,
                                   message_type=Gtk.MessageType.ERROR,
                                   buttons=Gtk.ButtonsType.OK,
                                   text=primary, use_header_bar=False)
        self.format_secondary_markup(secondary)
        self.connect("response", self.response_cb)

    def response_cb(self, widget, user_data):
        widget.destroy()


class SaveErrorDialog(Gtk.MessageDialog):
    def __init__(self, parent, filename, use_headerbar):
        # Translators: Save Error Dialog, primary text.
        primary = _("Failed to save \"%s\".") % filename
        # Translators: Save Error Dialog, secondary text.
        secondary = \
            _("Do you have write permission to the file and directory?")

        Gtk.MessageDialog.__init__(self, transient_for=parent, modal=True,
                                   message_type=Gtk.MessageType.ERROR,
                                   buttons=Gtk.ButtonsType.OK,
                                   text=primary, use_header_bar=False)
        self.format_secondary_markup(secondary)
        self.connect("response", self.response_cb)

    def response_cb(self, widget, user_data):
        widget.destroy()
