#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2014 Sean Davis <smd.seandavis@gmail.com>
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
import xml.dom.minidom

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib


def getUniqueFileId(name, extension):
    """Return a unique filename to use for a new .desktop file."""
    print('getUniqueFileId')
    append = 0
    while 1:
        if append == 0:
            filename = name + extension
        else:
            filename = name + '-' + str(append) + extension
        if extension == '.desktop':
            path = getUserItemPath()
            if not os.path.isfile(os.path.join(path, filename)) and \
                    not getItemPath(filename):
                break
        elif extension == '.directory':
            path = getUserDirectoryPath()
            if not os.path.isfile(os.path.join(path, filename)) and \
                    not getDirectoryPath(filename):
                break
        append += 1
    return filename


def getItemPath(file_id):
    """Return the path to the system-installed .desktop file."""
    print('getItemPath')
    for path in GLib.get_system_data_dirs():
        file_path = os.path.join(path, 'applications', file_id)
        if os.path.isfile(file_path):
            return file_path
    return None


def getUserItemPath():
    """Return the path to the user applications directory."""
    print('getUserItemPath')
    item_dir = os.path.join(GLib.get_user_data_dir(), 'applications')
    if not os.path.isdir(item_dir):
        os.makedirs(item_dir)
    return item_dir


def getDirectoryPath(file_id):
    """Return the path to the system-installed .directory file."""
    print('getDirectoryPath')
    for path in GLib.get_system_data_dirs():
        file_path = os.path.join(path, 'desktop-directories', file_id)
        if os.path.isfile(file_path):
            return file_path
    return None


def getUserDirectoryPath():
    """Return the path to the user desktop-directories directory."""
    print('getUserDirectoryPath')
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


def getSystemMenuPath(file_id):
    """Return the path to the system-installed menu file."""
    print('getSystemMenuPath')
    for path in GLib.get_system_config_dirs():
        file_path = os.path.join(path, 'menus', file_id)
        if os.path.isfile(file_path):
            return file_path
    return None


def getUserMenuXml(tree):
    """Return the header portions of the menu xml file."""
    print('getUserMenuXml')
    system_file = getSystemMenuPath(
            os.path.basename(tree.get_canonical_menu_path()))
    name = tree.get_root_directory().get_menu_id()
    menu_xml = "<!DOCTYPE Menu PUBLIC '-//freedesktop//DTD Menu 1.0//EN'" \
               " 'http://standards.freedesktop.org/menu-spec/menu-1.0.dtd'>\n"
    menu_xml += "<Menu>\n  <Name>" + name + "</Name>\n  "
    menu_xml += "<MergeFile type=\"parent\">" + system_file + \
                "</MergeFile>\n</Menu>\n"
    return menu_xml


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
