#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2023 Sean Davis <sean@bluesabre.org>
#   Copyright (C) 2016-2018 OmegaPhil <OmegaPhil@startmail.com>
#
#   Portions of this file are adapted from Alacarte Menu Editor,
#   Copyright (C) 2006 Travis Watkins, Heinrich Wendel
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
import xml.dom.minidom
import xml.parsers.expat
from locale import gettext as _
from xml.sax.saxutils import escape

import logging
logger = logging.getLogger('menulibre')  # noqa

import gi
gi.require_version('GMenu', '3.0')  # noqa
from gi.repository import Gio, GMenu, Gtk

from . import util
from .util import MenuItemTypes, escapeText, mapDesktopEnvironmentDirectories, unmapDesktopEnvironmentDirectories

locale.textdomain('menulibre')

icon_theme = Gtk.IconTheme.get_default()


def get_icon_theme_name_from_settings():
    try:
        theme_name = Gtk.Settings.get_default().get_property("gtk-icon-theme-name")
        if theme_name is not None and len(theme_name) > 0:
            return theme_name
    except BaseException:
        pass
    return None


def get_icon_theme_name_from_icons():
    try:
        lookup = icon_theme.lookup_icon("folder", 16, 0)
        if lookup is not None:
            filename = os.path.realpath(lookup.get_filename())
            path = filename.split('/')
            for i in range(len(path) - 1):
                index = os.path.join('/'.join(path[0:-i]), 'index.theme')
                if os.path.exists(index):
                    return path[-i - 1]
    except BaseException:
        pass
    return None


def get_icon_theme_name():
    theme_name = get_icon_theme_name_from_settings()
    if theme_name is not None:
        return theme_name

    theme_name = get_icon_theme_name_from_icons()
    if theme_name is not None:
        return theme_name

    return "Adwaita"


icon_theme_name = get_icon_theme_name()


menu_name = ""


COL_NAME = 0
COL_DISPLAY_NAME = 1
COL_COMMENT = 2
COL_EXEC = 3
COL_CATEGORIES = 4
COL_TYPE = 5
COL_G_ICON = 6
COL_ICON_NAME = 7
COL_FILENAME = 8
COL_EXPAND = 9
COL_SHOW = 10


def get_default_menu():
    """Return the filename of the default application menu."""
    prefixes = [
        util.getDefaultMenuPrefix(),
        ''
    ]
    user_basedir = util.getUserMenusDirectory()
    for prefix in prefixes:
        filename = '%s%s' % (prefix, 'applications.menu')
        user_dir = os.path.join(user_basedir, filename)
        if os.path.exists(user_dir):
            return filename
        system_dir = util.getSystemMenuPath(filename)
        if system_dir:
            return filename
    return None


def menu_to_treestore(treestore, parent, menu_items):
    """Convert the Alacarte menu to a standard treestore."""
    for item in menu_items:
        item_type = item[0]
        if item_type == MenuItemTypes.SEPARATOR:
            executable = ""
            name = _("Separator")
            displayed_name = name
            # Translators: Separator menu item
            tooltip = _("Separator")
            categories = ""
            filename = None
            icon_name = "content-loading-symbolic"
            icon = Gio.ThemedIcon.new(icon_name)
            item_type = MenuItemTypes.SEPARATOR
            show = False
        else:
            executable = item[2]['executable']
            name = item[2]['display_name']
            displayed_name = escape(name)
            show = item[2]['show']
            tooltip = escapeText(item[2]['comment'])
            categories = item[2]['categories']
            icon = item[2]['icon']
            filename = item[2]['filename']
            icon_name = item[2]['icon_name']

        treeiter = treestore.append(
            parent, [name, displayed_name, tooltip, executable, categories,
                     item_type, icon, icon_name, filename, False, show])

        if item_type == MenuItemTypes.DIRECTORY:
            treestore = menu_to_treestore(treestore, treeiter, item[3])

    return treestore


def get_treestore():
    """Get the TreeStore implementation of the current menu."""
    treestore = Gtk.TreeStore(
        str,  # Name
        str,  # Displayed Name
        str,  # Comment
        str,  # Executable
        str,  # Categories
        int,  # MenuItemType
        Gio.Icon,  # GIcon
        str,  # icon-name
        str,  # Filename
        bool,  # Expand
        bool  # Show
    )
    menus = get_menus()
    if not menus:
        return None
    return menu_to_treestore(treestore, None, menus[0])


def get_extended_icons(icon_names, extended_names):
    results = []
    prefer_symbolic = icon_theme_name in [
        "Adwaita"] and "folder" in extended_names
    for name in icon_names:
        if icon_theme.has_icon(name):
            return results
    if prefer_symbolic:
        for name in extended_names:
            name = name + "-symbolic"
            if icon_theme.has_icon(name):
                results.append(name)
        if len(results) > 0:
            return results
    for name in extended_names:
        if icon_theme.has_icon(name):
            results.append(name)
    return results


def get_submenus(menu, tree_dir):
    """Get the submenus for a tree directory."""
    structure = []
    for child in menu.getContents(tree_dir):
        if isinstance(child, GMenu.TreeSeparator):
            structure.append([MenuItemTypes.SEPARATOR, child, None, None])
        else:
            if isinstance(child, GMenu.TreeEntry):
                item_type = MenuItemTypes.APPLICATION
                entry_id = child.get_desktop_file_id()
                app_info = child.get_app_info()
                icon = app_info.get_icon()
                icon_name = app_info.get_string("Icon")
                extended_icon_names = [
                    "applications-other",
                    "application-x-executable"]
                display_name = app_info.get_display_name()
                generic_name = app_info.get_generic_name()
                comment = app_info.get_description()
                keywords = app_info.get_keywords()
                categories = app_info.get_categories()
                executable = app_info.get_executable()
                filename = child.get_desktop_file_path()
                submenus = None

                is_hidden = app_info.get_is_hidden()
                no_display = app_info.get_nodisplay()
                show_in = app_info.get_show_in()
                hidden = is_hidden or no_display or not show_in

            elif isinstance(child, GMenu.TreeDirectory):
                item_type = MenuItemTypes.DIRECTORY
                entry_id = child.get_menu_id()
                icon = child.get_icon()
                icon_name = None
                extended_icon_names = ["folder"]
                display_name = child.get_name()
                generic_name = child.get_generic_name()
                comment = child.get_comment()
                keywords = []
                categories = ""
                executable = None
                filename = child.get_desktop_file_path()
                hidden = child.get_is_nodisplay()
                submenus = get_submenus(menu, child)

            else:
                extended_icon_names = []

            icon_names = []
            if isinstance(icon, Gio.ThemedIcon):
                icon_names = icon.get_names()
            elif isinstance(icon, Gio.FileIcon):
                icon_names = [icon.get_file().get_path()]

            if icon_name is not None:
                icon_names = [icon_name] + icon_names

            for extended_icon_name in get_extended_icons(
                    icon_names, extended_icon_names):
                if isinstance(icon, Gio.ThemedIcon):
                    icon.append_name(extended_icon_name)
                icon_names.append(extended_icon_name)

            if icon_name is None:
                icon_name = icon_names[0]

            elif icon is None:
                icon = Gio.ThemedIcon.new(icon_name)

            filename = os.path.realpath(filename)

            details = {'display_name': display_name,
                       'generic_name': generic_name,
                       'comment': comment,
                       'keywords': keywords,
                       'categories': categories,
                       'executable': executable,
                       'filename': filename,
                       'icon': icon,
                       'icon_name': icon_name,
                       'show': not hidden}
            entry = [item_type, entry_id, details, submenus]
            structure.append(entry)

    return structure


def get_menus():
    """Get the menus from the MenuEditor"""
    menu = MenuEditor()
    if not menu.loaded:
        return None
    structure = []
    toplevels = []
    global menu_name
    menu_name = menu.tree.get_root_directory().get_menu_id()
    for child in menu.getMenus(None):
        toplevels.append(child)
    for top in toplevels:
        structure.append(get_submenus(menu, top[0]))
    menu.unmap()
    return structure


def removeWhitespaceNodes(node):
    """Remove whitespace nodes from the xml dom."""
    remove_list = []
    for child in node.childNodes:
        if child.nodeType == xml.dom.minidom.Node.TEXT_NODE:
            child.data = child.data.strip()
            if not child.data.strip():
                remove_list.append(child)
        elif child.hasChildNodes():
            removeWhitespaceNodes(child)
    for node in remove_list:
        node.parentNode.removeChild(node)


def getUserMenuXml(tree):
    """Return the header portions of the menu xml file."""
    system_file = util.getSystemMenuPath(
        os.path.basename(tree.get_canonical_menu_path()))
    name = tree.get_root_directory().get_menu_id()
    menu_xml = "<!DOCTYPE Menu PUBLIC '-//freedesktop//DTD Menu 1.0//EN'" \
               " 'http://standards.freedesktop.org/menu-spec/menu-1.0.dtd'>\n"
    menu_xml += "<Menu>\n  <Name>" + name + "</Name>\n  "
    menu_xml += "<MergeFile type=\"parent\">" + system_file + \
                "</MergeFile>\n</Menu>\n"
    return menu_xml


class MenuEditor(object):
    """MenuEditor class, adapted and minimized from Alacarte Menu Editor."""

    loaded = False

    def __init__(self, basename=None):
        """init"""

        # Remember to keep menulibre-menu-validate's GMenu object creation
        # in-sync with this code
        basename = basename or get_default_menu()
        if basename is None:
            return

        # For systems where desktop directories are installed in subdirectories,
        # we need to first bring them to the toplevel for GMenu to see them
        # correctly.
        mapDesktopEnvironmentDirectories()

        self.tree = GMenu.Tree.new(basename,
                                   GMenu.TreeFlags.SHOW_EMPTY |
                                   GMenu.TreeFlags.INCLUDE_EXCLUDED |
                                   GMenu.TreeFlags.INCLUDE_NODISPLAY |
                                   GMenu.TreeFlags.SHOW_ALL_SEPARATORS |
                                   GMenu.TreeFlags.SORT_DISPLAY_NAME)
        self.load()

        self.path = os.path.join(
            util.getUserMenusDirectory(), self.tree.props.menu_basename)
        logger.debug("Using menu: %s" % self.path)
        self.loadDOM()

        self.loaded = self.hasContents()

    def loadDOM(self):
        """loadDOM"""
        try:
            self.dom = xml.dom.minidom.parse(self.path)
        except (IOError, xml.parsers.expat.ExpatError):
            self.dom = xml.dom.minidom.parseString(
                getUserMenuXml(self.tree))
        removeWhitespaceNodes(self.dom)

    def load(self):
        """load"""
        if not self.tree.load_sync():
            raise ValueError("can not load menu tree %r" %
                             (self.tree.props.menu_basename,))

    def unmap(self):
        unmapDesktopEnvironmentDirectories()

    def hasContents(self):
        for child in self.getMenus(None):
            submenus = self.getContents(child[0])
            if len(submenus) > 0:
                return True
        return False

    def getMenus(self, parent):
        """getMenus"""
        if parent is None:
            yield (self.tree.get_root_directory(), True)
            return

        item_iter = parent.iter()
        item_type = item_iter.next()
        while item_type != GMenu.TreeItemType.INVALID:
            if item_type == GMenu.TreeItemType.DIRECTORY:
                item = item_iter.get_directory()
                yield (item, self.isVisible(item))
            item_type = item_iter.next()

    def getContents(self, item):
        """getContents"""
        contents = []
        item_iter = item.iter()
        item_type = item_iter.next()

        found_directories = []

        while item_type != GMenu.TreeItemType.INVALID:
            item = None
            if item_type == GMenu.TreeItemType.DIRECTORY:
                item = item_iter.get_directory()
                desktop = item.get_desktop_file_path()
                if desktop is not None:
                    desktop = os.path.realpath(desktop)
                if desktop is None or desktop in found_directories:
                    # Do not include directories without filenames.
                    # Do not include duplicate directories.
                    item = None
                else:
                    found_directories.append(desktop)
            elif item_type == GMenu.TreeItemType.ENTRY:
                item = item_iter.get_entry()
            elif item_type == GMenu.TreeItemType.HEADER:
                item = item_iter.get_header()
            elif item_type == GMenu.TreeItemType.ALIAS:
                item = item_iter.get_alias()
            elif item_type == GMenu.TreeItemType.SEPARATOR:
                item = item_iter.get_separator()
            if item:
                contents.append(item)
            item_type = item_iter.next()
        return contents
