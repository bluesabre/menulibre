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

import os
import re

import getpass
import psutil
old_psutil_format = isinstance(psutil.Process.username, property)

from gi.repository import GLib, Gdk

import logging
logger = logging.getLogger('menulibre')


def enum(**enums):
    """Add enumarations to Python."""
    return type('Enum', (), enums)

MenuItemTypes = enum(
    SEPARATOR=-1,
    APPLICATION=0,
    LINK=1,
    DIRECTORY=2
)


def getProcessUsername(process):
    """Get the username of the process owner. Return None if fail."""
    username = None

    try:
        if old_psutil_format:
            username = process.username
        else:
            username = process.username()
    except:
        pass

    return username


def getProcessName(process):
    """Get the process name. Return None if fail."""
    p_name = None

    try:
        if old_psutil_format:
            p_name = process.name
        else:
            p_name = process.name()
    except:
        pass

    return p_name


def getProcessList():
    """Return a list of unique process names for the current user."""
    username = getpass.getuser()
    try:
        pids = psutil.get_pid_list()
    except AttributeError:
        pids = psutil.pids()
    processes = []
    for pid in pids:
        try:
            process = psutil.Process(pid)
            p_user = getProcessUsername(process)
            if p_user == username:
                p_name = getProcessName(process)
                if p_name is not None and p_name not in processes:
                    processes.append(p_name)
        except:
            pass
    processes.sort()
    return processes


def getBasename(filename):
    if filename.endswith('.desktop'):
        basename = filename.split('/applications/', 1)[1]
    elif filename.endswith('.directory'):
        basename = filename.split('/desktop-directories/', 1)[1]
    return basename


def getDefaultMenuPrefix():
    """Return the default menu prefix."""
    prefix = os.environ.get('XDG_MENU_PREFIX', '')

    # Cinnamon doesn't set this variable
    if prefix == "":
        if 'cinnamon' in os.environ.get('DESKTOP_SESSION', ''):
            prefix = 'cinnamon-'

    if prefix == "":
        processes = getProcessList()
        if 'xfce4-panel' in processes:
            prefix = 'xfce-'

    if len(prefix) == 0:
        logger.warning("No menu prefix found, MenuLibre will not function "
                       "properly.")

    return prefix


def getItemPath(file_id):
    """Return the path to the system-installed .desktop file."""
    for path in GLib.get_system_data_dirs():
        file_path = os.path.join(path, 'applications', file_id)
        if os.path.isfile(file_path):
            return file_path
    return None


def getUserItemPath():
    """Return the path to the user applications directory."""
    item_dir = os.path.join(GLib.get_user_data_dir(), 'applications')
    if not os.path.isdir(item_dir):
        os.makedirs(item_dir)
    return item_dir


def getDirectoryPath(file_id):
    """Return the path to the system-installed .directory file."""
    for path in GLib.get_system_data_dirs():
        file_path = os.path.join(path, 'desktop-directories', file_id)
        if os.path.isfile(file_path):
            return file_path
    return None


def getUserDirectoryPath():
    """Return the path to the user desktop-directories directory."""
    menu_dir = os.path.join(GLib.get_user_data_dir(), 'desktop-directories')
    if not os.path.isdir(menu_dir):
        os.makedirs(menu_dir)
    return menu_dir


def getUserMenuPath():
    """Return the path to the user menus directory."""
    menu_dir = os.path.join(GLib.get_user_config_dir(), 'menus')
    if not os.path.isdir(menu_dir):
        os.makedirs(menu_dir)
    return menu_dir


def getUserLauncherPath(basename):
    """Return the user-installed path to a .desktop or .directory file."""
    if basename.endswith('.desktop'):
        check_dir = "applications"
    else:
        check_dir = "desktop-directories"
    path = os.path.join(GLib.get_user_data_dir(), check_dir)
    filename = os.path.join(path, basename)
    if os.path.isfile(filename):
        return filename
    return None


def getSystemMenuPath(file_id):
    """Return the path to the system-installed menu file."""
    for path in GLib.get_system_config_dirs():
        file_path = os.path.join(path, 'menus', file_id)
        if os.path.isfile(file_path):
            return file_path
    return None


def getSystemLauncherPath(basename):
    """Return the system-installed path to a .desktop or .directory file."""
    if basename.endswith('.desktop'):
        check_dir = "applications"
    else:
        check_dir = "desktop-directories"
    for path in GLib.get_system_data_dirs():
        path = os.path.join(path, check_dir)
        filename = os.path.join(path, basename)
        if os.path.isfile(filename):
            return filename
    return None


def getDirectoryName(directory_str):
    """Return the directory name to be used in the XML file."""
    # Get the menu prefix
    prefix = getDefaultMenuPrefix()
    has_prefix = False

    basename = getBasename(directory_str)
    name, ext = os.path.splitext(basename)

    # Handle directories like xfce-development
    if name.startswith(prefix):
        name = name[len(prefix):]
        name = name.title()
        has_prefix = True

    # Handle X-GNOME, X-XFCE
    if name.startswith("X-"):
        # Handle X-GNOME, X-XFCE
        condensed = name.split('-', 2)[-1]
        non_camel = re.sub('(?!^)([A-Z]+)', r' \1', condensed)
        return non_camel

    # Cleanup ArcadeGames and others as per the norm.
    if name.endswith('Games') and name != 'Games':
        condensed = name[:-5]
        non_camel = re.sub('(?!^)([A-Z]+)', r' \1', condensed)
        return non_camel

    # GNOME...
    if name == 'AudioVideo' or name == 'Audio-Video':
        return 'Multimedia'

    if name == 'Game':
        return 'Games'

    if name == 'Network' and prefix != 'xfce-':
        return 'Internet'

    if name == 'Utility':
        return 'Accessories'

    if name == 'System-Tools':
        if prefix == 'lxde-':
            return 'Administration'
        else:
            return 'System'

    if name == 'Settings':
        if prefix == 'lxde-':
            return 'DesktopSettings'
        elif has_prefix and prefix == 'xfce-':
            return name
        else:
            return 'Preferences'

    if name == 'Settings-System':
        return 'Administration'

    if name == 'GnomeScience':
        return 'Science'

    if name == 'Utility-Accessibility':
        return 'Universal Access'

    # We tried, just return the name.
    return name


def getRequiredCategories(directory):
    """Return the list of required categories for a directory string."""
    prefix = getDefaultMenuPrefix()
    if directory is not None:
        basename = getBasename(directory)
        name, ext = os.path.splitext(basename)

        # Handle directories like xfce-development
        if name.startswith(prefix):
            name = name[len(prefix):]
            name = name.title()

        if name == 'Accessories':
            return ['Utility']

        if name == 'Games':
            return ['Game']

        if name == 'Multimedia':
            return ['AudioVideo']

        else:
            return [name]
    else:
        # Get The Toplevel item if necessary...
        if prefix == 'xfce-':
            return ['X-XFCE', 'X-Xfce-Toplevel']
    return []


def getSaveFilename(name, filename, item_type, force_update=False):
    """Determime the filename to be used to store the launcher.

    Return the filename to be used."""
    # Check if the filename is writeable. If not, generate a new one.
    unique = filename is None or len(filename) == 0

    if unique or not os.access(filename, os.W_OK):
        # No filename, make one from the launcher name.
        if unique:
            basename = "menulibre-" + name.lower().replace(' ', '-')

        # Use the current filename as a base.
        else:
            basename = getBasename(filename)

        # Split the basename into filename and extension.
        name, ext = os.path.splitext(basename)

        # Get the save location of the launcher base on type.
        if item_type == 'Application':
            path = getUserItemPath()
            ext = '.desktop'
        elif item_type == 'Directory':
            path = getUserDirectoryPath()
            ext = '.directory'
            
        basedir = os.path.dirname(os.path.join(path, basename))
        if not os.path.exists(basedir):
            os.makedirs(basedir)

        # Index for unique filenames.
        count = 1

        # Be sure to not overwrite system launchers if new.
        if unique:
            # Check for the system version of the launcher.
            if getSystemLauncherPath("%s%s" % (name, ext)) is not None:
                # If found, check for any additional ones.
                while getSystemLauncherPath("%s%i%s" % (name, count, ext)) \
                        is not None:
                    count += 1

                # Now be sure to not overwrite locally installed ones.
                filename = os.path.join(path, name)
                filename = "%s%i%s" % (filename, count, ext)

                # Append numbers as necessary to make the filename unique.
                while os.path.exists(filename):
                    new_basename = "%s%i%s" % (name, count, ext)
                    filename = os.path.join(path, new_basename)
                    count += 1

            else:
                # Create the new base filename.
                filename = os.path.join(path, name)
                filename = "%s%s" % (filename, ext)

                # Append numbers as necessary to make the filename unique.
                while os.path.exists(filename):
                    new_basename = "%s%i%s" % (name, count, ext)
                    filename = os.path.join(path, new_basename)
                    count += 1

        else:
            # Create the new base filename.
            filename = os.path.join(path, basename)

            if force_update:
                return filename

            # Append numbers as necessary to make the filename unique.
            while os.path.exists(filename):
                new_basename = "%s%i%s" % (name, count, ext)
                filename = os.path.join(path, new_basename)
                count += 1

    return filename


def check_keypress(event, keys):
    """Compare keypress events with desired keys and return True if matched."""
    if 'Control' in keys:
        if not bool(event.get_state() & Gdk.ModifierType.CONTROL_MASK):
            return False
    if 'Alt' in keys:
        if not bool(event.get_state() & Gdk.ModifierType.MOD1_MASK):
            return False
    if 'Shift' in keys:
        if not bool(event.get_state() & Gdk.ModifierType.SHIFT_MASK):
            return False
    if 'Super' in keys:
        if not bool(event.get_state() & Gdk.ModifierType.SUPER_MASK):
            return False
    if 'Escape' in keys:
        keys[keys.index('Escape')] = 'escape'
    if Gdk.keyval_name(event.get_keyval()[1]).lower() not in keys:
        return False

    return True
