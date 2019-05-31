#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2019 Sean Davis <smd.seandavis@gmail.com>
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
import subprocess

from locale import gettext as _

from gi.repository import Gtk, GLib

import menulibre_lib

import logging
logger = logging.getLogger('menulibre')


class AboutDialog(Gtk.AboutDialog):
    def __init__(self, parent):
        Gtk.AboutDialog.__init__(self)
        authors = ["Sean Davis"]
        documenters = ["Sean Davis"]

        # Translators: About Dialog, window title.
        self.set_title(_("About MenuLibre"))
        self.set_program_name("MenuLibre")
        self.set_logo_icon_name("menulibre")
        self.set_copyright("Copyright © 2012-2019 Sean Davis")
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
    url = "https://wiki.bluesabre.org/menulibre-docs"

    dialog = Gtk.MessageDialog(transient_for=parent, modal=True,
                               message_type=Gtk.MessageType.QUESTION,
                               buttons=Gtk.ButtonsType.NONE,
                               text=primary)
    dialog.set_title(title)
    dialog.format_secondary_markup(secondary)
    for button in buttons:
        dialog.add_button(button[0], button[1])

    if dialog.run() == Gtk.ResponseType.OK:
        logger.debug("Navigating to help page, %s" % url)
        menulibre_lib.show_uri(parent, url)
    dialog.destroy()


class SaveOnCloseDialog(Gtk.MessageDialog):
    def __init__(self, parent):
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
                                   text=primary)
        self.set_title(title)
        self.format_secondary_markup(secondary)
        for button in buttons:
            self.add_button(button[0], button[1])


class SaveOnLeaveDialog(Gtk.MessageDialog):
    def __init__(self, parent):
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
                                   text=primary)
        self.set_title(title)
        self.format_secondary_markup(secondary)
        for button in buttons:
            self.add_button(button[0], button[1])


class DeleteDialog(Gtk.MessageDialog):
    def __init__(self, parent, primary):
        # Translations: Delete Dialog, secondary text. Notifies user that
        # the file cannot be restored once deleted.
        secondary = _("This cannot be undone.")
        Gtk.MessageDialog.__init__(self, transient_for=parent, modal=True,
                                   message_type=Gtk.MessageType.QUESTION,
                                   buttons=Gtk.ButtonsType.OK_CANCEL,
                                   text=primary)
        self.format_secondary_markup(secondary)


class RevertDialog(Gtk.MessageDialog):
    def __init__(self, parent):
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
                                   text=primary)
        self.set_title(title)
        self.format_secondary_markup(secondary)
        for button in buttons:
            self.add_button(button[0], button[1])


class FileChooserDialog(Gtk.FileChooserDialog):
    def __init__(self, parent, title, action):
        Gtk.FileChooserDialog.__init__(self, title=title, transient_for=parent,
                                       action=action)
        # Translators: File Chooser Dialog, cancel button.
        self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        # Translators: File Chooser Dialog, confirmation button.
        self.add_button(_("OK"), Gtk.ResponseType.OK)


class LauncherRemovedDialog(Gtk.MessageDialog):
    def __init__(self, parent):
        # Translators: Launcher Removed Dialog, primary text. Indicates that
        # the selected application is no longer installed.
        primary = _("No Longer Installed")
        # Translators: Launcher Removed Dialog, secondary text.
        secondary = _("This launcher has been removed from the "
                      "system.\nSelecting the next available item.")

        Gtk.MessageDialog.__init__(self, transient_for=parent, modal=True,
                                   message_type=Gtk.MessageType.INFO,
                                   buttons=Gtk.ButtonsType.OK,
                                   text=primary)
        self.format_secondary_markup(secondary)


class NotFoundInPathDialog(Gtk.MessageDialog):
    def __init__(self, parent, command):
        # Translators: Not Found In PATH Dialog, primary text. Indicates
        # that the provided script was not found in any PATH directory.
        primary = _("Could not find \"%s\" in your PATH.") % command

        path = os.getenv("PATH", "").split(":")
        secondary = "<b>PATH:</b>\n%s" % "\n".join(path)
        Gtk.MessageDialog.__init__(self, transient_for=parent, modal=True,
                                   message_type=Gtk.MessageType.ERROR,
                                   buttons=Gtk.ButtonsType.OK,
                                   text=primary)
        self.format_secondary_markup(secondary)
        self.connect("response", self.response_cb)

    def response_cb(self, widget, user_data):
        widget.destroy()


class SaveErrorDialog(Gtk.MessageDialog):
    def __init__(self, parent, filename):
        # Translators: Save Error Dialog, primary text.
        primary = _("Failed to save \"%s\".") % filename
        # Translators: Save Error Dialog, secondary text.
        secondary = \
            _("Do you have write permission to the file and directory?")

        Gtk.MessageDialog.__init__(self, transient_for=parent, modal=True,
                                   message_type=Gtk.MessageType.ERROR,
                                   buttons=Gtk.ButtonsType.OK,
                                   text=primary)
        self.format_secondary_markup(secondary)
        self.connect("response", self.response_cb)

    def response_cb(self, widget, user_data):
        widget.destroy()


class XpropWindowDialog(Gtk.MessageDialog):
    def __init__(self, parent, launcher_name):
        # Translators: Identify Window Dialog, primary text.
        primary = _("Identify Window")
        # Translators: Identify Window Dialog, secondary text. The selected
        # application is displayed in the placeholder text.
        secondary = _("Click on the main application window for '%s'.") % \
            launcher_name
        icon_name = "edit-find"

        Gtk.MessageDialog.__init__(self, transient_for=parent, modal=True,
                                   message_type=Gtk.MessageType.INFO,
                                   buttons=Gtk.ButtonsType.OK,
                                   text=primary)
        self.format_secondary_markup(secondary)

        image = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DIALOG)
        self.set_image(image)

        self.process = None
        self.classes = []

    def run_xprop(self):
        GLib.timeout_add(500, self.start_xprop)
        self.run()
        self.classes.sort()
        return self.classes

    def start_xprop(self):
        cmd = ['xprop', 'WM_CLASS']
        self.classes = []
        env = os.environ.copy()
        self.process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
        )
        GLib.idle_add(self.check_xprop)
        return False

    def check_xprop(self):
        if self.process.poll() is not None:
            output = self.process.stdout.read().decode('UTF-8').strip()
            if output.startswith("WM_CLASS"):
                values = output.split("=", 1)[1].split(", ")
                for value in values:
                    value = value.strip()
                    value = value[1:-1]
                    if value not in self.classes:
                        self.classes.append(value)
            self.destroy()
            return False
        return True
