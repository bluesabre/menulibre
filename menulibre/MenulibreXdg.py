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

import locale
import os
from collections import OrderedDict
from locale import gettext as _

import subprocess

from gi.repository import GLib

locale.textdomain('menulibre')


sudo = os.getuid() == 0
default_locale = locale.getdefaultlocale()[0]


class MenulibreDesktopEntry:

    """Basic class for Desktop Entry files"""

    def __init__(self, filename=None):
        """Initialize the MenulibreDesktopEntry instance."""
        self.filename = filename
        self.properties = OrderedDict()
        self.text = ""
        if filename:
            if os.path.isfile(filename):
                self.load_properties(filename)
                self.id = os.path.basename(filename)
            else:
                pass
        else:
            self.properties['Desktop Entry'] = OrderedDict()
            self.properties['Desktop Entry']['Version'] = '1.0'
            self.properties['Desktop Entry']['Type'] = 'Application'
            self.properties['Desktop Entry']['Name'] = _('New Menu Item')
            self.properties['Desktop Entry']['Comment'] = _(
                "A small descriptive blurb about this application.")
            self.properties['Desktop Entry'][
                'Icon'] = 'application-default-icon'
            self.properties['Desktop Entry']['Exec'] = ''
            self.properties['Desktop Entry']['Path'] = ''
            self.properties['Desktop Entry']['Terminal'] = 'false'
            self.properties['Desktop Entry']['StartupNotify'] = 'false'
            self.properties['Desktop Entry']['Categories'] = ''

    def __getitem__(self, prop_name):
        """Get property from this object like a dictionary."""
        return self.get_property('Desktop Entry', prop_name, default_locale)

    def __setitem__(self, prop_name, prop_value):
        """Set property to this object like a dictionary."""
        self.properties['Desktop Entry'][prop_name] = prop_value
        if prop_name in ['Name', 'Comment']:
            prop_name = "%s[%s]" % (prop_name, default_locale)
            self.properties['Desktop Entry'][prop_name] = prop_value

    def load_properties(self, filename):
        """Load the properties."""
        input_file = open(filename)
        self.load_properties_from_text(input_file.read())
        input_file.close()

    def load_properties_from_text(self, text):
        """Load the properties from a string."""
        current_property = ""
        self.text = text
        blank_count = 0
        for line in text.split('\n'):
            if line.startswith('[') and line.endswith(']'):
                current_property = line[1:-1]
                self.properties[current_property] = OrderedDict()
                self.properties[current_property][
                    "*OriginalName"] = current_property.replace(
                                    ' Shortcut Group', '').replace(
                                    'Desktop Action ', '')
            elif '=' in line:
                try:
                    key, value = line.split('=', 1)
                    self.properties[current_property][key] = value
                except KeyError:
                    pass
            elif line.strip() == '':
                try:
                    self.properties[current_property]['*Blank%i' %
                                                      blank_count] = None
                    blank_count += 1
                except KeyError:
                    pass

    def get_property(self, category, prop_name, locale_str=default_locale):
        """Return the value of the specified property."""
        prop = self.get_named_property(category, prop_name, locale_str)
        if prop in ['true', 'false']:
            return prop == 'true'
        if prop_name in ['Hidden', 'NoDisplay', 'Terminal', 'StartupNotify']:
            return False
        return prop

    def get_named_property(self, category, prop_name, locale_str=None):
        """Return the value of the specified named property."""
        if locale_str:
            try:
                return self.properties[category]["%s[%s]" %
                                (prop_name, locale_str)]
            except KeyError:
                if '_' in locale_str:
                    try:
                        return self.properties[category]["%s[%s]" %
                                (prop_name, locale_str.split('_')[0])]
                    except KeyError:
                        pass
        try:
            return self.properties[category][prop_name]
        except KeyError:
            return ""

    def get_actions(self):
        """Return a list of the Unity action groups."""
        quicklists = []
        if self.get_property('Desktop Entry', 'Actions') != '':
            enabled_quicklists = self.get_property(
                'Desktop Entry', 'Actions').split(';')
            for key in self.properties:
                if key.startswith('Desktop Action'):
                    name = key[15:]
                    displayed_name = self.get_property(key, 'Name')
                    command = self.get_property(key, 'Exec')
                    enabled = name in enabled_quicklists
                    quicklists.append(
                        (name, displayed_name, command, enabled))
        elif self.get_property('Desktop Entry',
                               'X-Ayatana-Desktop-Shortcuts') != '':
            enabled_quicklists = self.get_property(
                'Desktop Entry', 'X-Ayatana-Desktop-Shortcuts').split(';')
            for key in self.properties:
                if key.endswith('Shortcut Group'):
                    name = key[:-15]
                    displayed_name = self.get_property(key, 'Name')
                    command = self.get_property(key, 'Exec')
                    enabled = name in enabled_quicklists
                    quicklists.append(
                        (name, displayed_name, command, enabled))
        return quicklists

def desktop_menu_update():
    subprocess.call(["xdg-desktop-menu", "forceupdate"])

def desktop_menu_install(directory_files, desktop_files):
    """Install one or more applications in a submenu of the desktop menu
    system.  If multiple directory files are provided each file will represent
    a submenu within the menu that preceeds it, creating a nested menu
    hierarchy (sub-sub-menus). The menu entries themselves will be added to
    the last submenu. """
    # Check for the minimum required arguments
    if len(directory_files) == 0 or len(desktop_files) == 0:
        return

    # Do not install to system paths.
    for path in GLib.get_system_config_dirs():
        for filename in directory_files:
            if filename.startswith(path):
                return

    cmd_list = ["xdg-desktop-menu", "install", "--novendor"]
    cmd_list = cmd_list + directory_files + desktop_files
    subprocess.call(cmd_list)


def desktop_menu_uninstall(directory_files, desktop_files):
    """Remove applications or submenus from the desktop menu system
    previously installed with xdg-desktop-menu install."""
    # Check for the minimum required arguments
    if len(directory_files) == 0 or len(desktop_files) == 0:
        return

    # Do not uninstall from system paths.
    for path in GLib.get_system_config_dirs():
        for filename in directory_files:
            if filename.startswith(path):
                return

    # xdg-desktop-menu uninstall does not work... implement ourselves.
    basenames = []
    for filename in directory_files:
        basenames.append(os.path.basename(filename))
    basenames.sort()
    base_filename = os.path.basename(desktop_files[0])

    # Find the file with all the details to remove the filename.
    merged_dir = os.path.join(GLib.get_user_config_dir(),
                                    "menus", "applications-merged")

    for filename in os.listdir(merged_dir):
        filename = os.path.join(merged_dir, filename)
        found_directories = []
        filename_found = False
        with open(filename, 'r') as open_file:
            write_contents = ""
            for line in open_file:
                if "<Filename>" in line:
                    if base_filename in line:
                        filename_found = True
                    else:
                        write_contents += line
                else:
                    write_contents += line
                if "<Directory>" in line:
                    line = line.split("<Directory>")[1]
                    line = line.split("</Directory>")[0]
                    found_directories.append(line)
        if filename_found:
            found_directories.sort()
            if basenames == found_directories:
                with open(filename, 'w') as open_file:
                    open_file.write(write_contents)
                return
