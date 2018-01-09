#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2015 Sean Davis <smd.seandavis@gmail.com>
#   Copyright (C) 2017 OmegaPhil <omegaphil@startmail.com>
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
import subprocess

import getpass
import psutil

from locale import gettext as _

from gi.repository import GLib, Gdk

import logging
logger = logging.getLogger('menulibre')

old_psutil_format = isinstance(psutil.Process.username, property)


def enum(**enums):
    """Add enumarations to Python."""
    return type('Enum', (), enums)


MenuItemTypes = enum(
    SEPARATOR=-1,
    APPLICATION=0,
    LINK=1,
    DIRECTORY=2
)


MenuItemKeys = (
    # Key, Type, Required, Types (MenuItemType)
    ("Version", str, False, (0, 1, 2)),
    ("Type", str, True, (0, 1, 2)),
    ("Name", str, True, (0, 1, 2)),
    ("GenericName", str, False, (0, 1, 2)),
    ("NoDisplay", bool, False, (0, 1, 2)),
    ("Comment", str, False, (0, 1, 2)),
    ("Icon", str, False, (0, 1, 2)),
    ("Hidden", bool, False, (0, 1, 2)),
    ("OnlyShowIn", list, False, (0, 1, 2)),
    ("NotShowIn", list, False, (0, 1, 2)),
    ("DBusActivatable", bool, False, (0,)),
    ("TryExec", str, False, (0,)),
    ("Exec", str, True, (0,)),
    ("Path", str, False, (0,)),
    ("Terminal", bool, False, (0,)),
    ("Actions", list, False, (0,)),
    ("MimeType", list, False, (0,)),
    ("Categories", list, False, (0,)),
    ("Implements", list, False, (0,)),
    ("Keywords", list, False, (0,)),
    ("StartupNotify", bool, False, (0,)),
    ("StartupWMClass", str, False, (0,)),
    ("URL", str, True, (1,))
)


def getRelatedKeys(menu_item_type, key_only=False):
    if isinstance(menu_item_type, str):
        if menu_item_type == "Application":
            menu_item_type = MenuItemTypes.APPLICATION
        elif menu_item_type == "Link":
            menu_item_type = MenuItemTypes.LINK
        elif menu_item_type == "Directory":
            menu_item_type = MenuItemTypes.DIRECTORY

    results = []
    for tup in MenuItemKeys:
        if menu_item_type in tup[3]:
            if key_only:
                results.append(tup[0])
            else:
                results.append((tup[0], tup[1], tup[2]))
    return results


def getProcessUsername(process):
    """Get the username of the process owner. Return None if fail."""
    username = None

    try:
        if old_psutil_format:
            username = process.username
        else:
            username = process.username()
    except:  # noqa
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
    except:  # noqa
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
        except:  # noqa
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


def getDirectoryName(directory_str):  # noqa
    """Return the directory name to be used in the XML file."""

    # Note: When adding new logic here, please see if
    # getDirectoryNameFromCategory should also be updated

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


def getDirectoryNameFromCategory(name):  # noqa
    """Guess at the directory name a category should cause its launcher to
    appear in. This is used to add launchers to or remove from the right
    directories after category addition without having to restart menulibre."""

    # Note: When adding new logic here, please see if
    # getDirectoryName should also be updated

    # I don't want to overload the use of getDirectoryName, so have spun out
    # this similar function

    # Only interested in generic categories here, so no need to handle
    # categories named after desktop environments
    prefix = getDefaultMenuPrefix()

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

    if name == 'Network':
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
        elif prefix == 'xfce-':
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


def getSaveFilename(name, filename, item_type, force_update=False):  # noqa
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


def check_keypress(event, keys):  # noqa
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


def determine_bad_desktop_files():
    """Run the gmenu-invalid-desktop-files script to get at the GMenu library's
    debug output, which lists files that failed to load, and return these as a
    sorted list."""

    # Run the helper script with normal binary lookup via the shell, capturing
    # stderr, sensitive to errors
    try:
        result = subprocess.run(['menulibre-menu-validate'],
                                stderr=subprocess.PIPE, shell=True, check=True)
    except subprocess.CalledProcessError:
        return []

    # stderr is returned as bytes, so converting it to the line-buffered output
    # I actually want
    bad_desktop_files = []
    for line in result.stderr.decode().split('\n'):
        matches = re.match(r'^Failed to load "(.+\.desktop)"$', line)
        if matches:
            bad_desktop_files.append(matches.groups()[0])

    # Alphabetical sort on bad desktop file paths
    bad_desktop_files.sort()

    return bad_desktop_files


def validate_desktop_file(desktop_file):  # noqa
    """Validate a known-bad desktop file in the same way GMenu/glib does, to
    give a user real information about why certain files are broken."""

    # This is a reimplementation of the validation logic in glib2's
    # gio/gdesktopappinfo.c:g_desktop_app_info_load_from_keyfile.
    # gnome-menus appears also to try to do its own validation in
    # libmenu/desktop-entries.c:desktop_entry_load, however
    # g_desktop_app_info_new_from_filename will not return a valid
    # GDesktopAppInfo in the first place if something is wrong with the
    # desktop file

    try:

        # Looks like load_from_file is not a class method??
        keyfile = GLib.KeyFile()
        keyfile.load_from_file(desktop_file, GLib.KeyFileFlags.NONE)

    except Exception as e:
        return _('Unable to load as a key file due to the following error:'
                 ' %s') % e

    # File is at least a valid keyfile, so can start the real desktop
    # validation
    # Start group validation
    start_group = keyfile.get_start_group()
    if start_group != GLib.KEY_FILE_DESKTOP_GROUP:
        return (_('Start group is invalid - currently \'%s\', should be '
                  '\'%s\'') % (start_group, GLib.KEY_FILE_DESKTOP_GROUP))

    # Type validation
    try:
        type_key = keyfile.get_string(start_group,
                                      GLib.KEY_FILE_DESKTOP_KEY_TYPE)
    except:  # noqa
        return _('Type key was not found')

    if type_key != GLib.KEY_FILE_DESKTOP_TYPE_APPLICATION:
        return (_('Type is invalid - currently \'%s\', should be \'%s\'')
                % (type_key, GLib.KEY_FILE_DESKTOP_TYPE_APPLICATION))

    # Validating 'try exec' if its present
    try:
        try_exec = keyfile.get_string(start_group,
                                      GLib.KEY_FILE_DESKTOP_KEY_TRY_EXEC)
    except:  # noqa
        pass

    else:
        if GLib.find_program_in_path(try_exec) is None:
            return (_('Try exec program \'%s\' has not been found in the'
                      ' PATH') % try_exec)

    # Validating executable
    try:
        exec_key = keyfile.get_string(start_group,
                                      GLib.KEY_FILE_DESKTOP_KEY_EXEC)
    except:  # noqa
        return _('Exec key not found')

    try:
        GLib.shell_parse_argv(exec_key)

    except Exception as e:
        return (_('Exec program \'%s\' is not a valid shell command '
                  'according to GLib.shell_parse_argv, error: %s')
                % (exec_key, e))

    if GLib.find_program_in_path(exec_key) is None:
        return (_('Exec program \'%s\' has not been found in the PATH')
                % exec_key)

    # At this point the desktop file is valid - execution should never reach
    # here
    return _('Desktop file is valid??')
