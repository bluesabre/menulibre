#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2015 Sean Davis <smd.seandavis@gmail.com>
#   Copyright (C) 2016 OmegaPhil <omegaphil@startmail.com>
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

#lint:disable
try:
    import xml.etree.cElementTree
    from xml.etree.cElementTree import ElementTree, Element, SubElement
except ImportError:
    import xml.etree.ElementTree
    from xml.etree.ElementTree import ElementTree, Element, SubElement
#lint:enable

import os

from . import util
from .util import MenuItemTypes

from . import MenuEditor

# Store user desktop directory location
directories = util.getUserDirectoryPath()


# Prevent gnome-menus crash
processed_directories = []


def indent(elem, level=0):
    """Indentation code to make XML output easier to read."""
    i = "\n" + level * "\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


class XmlMenuElement(Element):
    """An extension of the ElementTree.Element class which adds Menu
    constructing functionality."""

    def __init__(self, *args, **kwargs):
        """Initialize the XmlMenuElement class.  This takes all regular
        arguments for ElementTree.Element, as well as the menu_name keyword
        argument, used for setting the Menu Name property."""
        if 'menu_name' in list(kwargs.keys()):
            menu_name = kwargs['menu_name']
            kwargs.pop("menu_name", None)
        else:
            menu_name = None
        super(XmlMenuElement, self).__init__(*args, **kwargs)
        if menu_name:
            SubElement(self, "Name").text = menu_name

    def addMenu(self, menu_name, filename=None):
        """Add a submenu <Menu> to this XmlMenuElement.

        Return a reference to that submenu XmlMenuElement."""
        menu = XmlMenuElement("Menu")
        self.append(menu)
        SubElement(menu, "Name").text = menu_name
        if filename:
            SubElement(menu, "Directory").text = os.path.basename(filename)
            if filename.startswith(directories):
                SubElement(menu, "DirectoryDir").text = directories
        return menu

    def addMenuname(self, menu_name):
        """Add a menuname <Menuname> to this XmlMenuElement.

        Return a reference to that menuname XmlMenuElement."""
        element = XmlMenuElement("Menuname")
        element.text = menu_name
        self.append(element)
        return element

    def addSeparator(self):
        """Add a <Separator> element to this XmlMenuElement.

        Return a reference to that separator XmlMenuElement."""
        element = XmlMenuElement("Separator")
        self.append(element)
        return element

    def addMergeFile(self, filename, merge_type="parent"):
        """Add a merge file <MergeFile> to this XmlMenuElement.

        Return a reference to that merge file XmlMenuElement."""
        element = XmlMenuElement("MergeFile", type=merge_type)
        element.text = filename
        self.append(element)
        return element

    def addMerge(self, merge_type):
        """Add a merge <Merge> to this XmlMenuElement.

        Return a reference to that merge SubElement."""
        return SubElement(self, "Merge", type=merge_type)

    def addLayout(self):
        """Add a layout <Layout> to this XmlMenuElement.

        Return a reference to that layout XmlMenuElement"""
        element = XmlMenuElement("Layout")
        self.append(element)
        return element

    def addFilename(self, filename):
        """Add a filename <Filename> to this XmlMenuElement.

        Return a reference to that filename XmlMenuElement."""
        element = XmlMenuElement("Filename")
        element.text = filename
        self.append(element)
        return element

    def addInclude(self):
        """Add an include <Include> to this XmlMenuElement.

        Return a reference to that include XmlMenuElement"""
        element = XmlMenuElement("Include")
        self.append(element)
        return element

    def addCategory(self, category):
        """Add a category <Category> to this XmlMenuElement. Used primarily for
        Include and Exclude.

        Return a reference to that category XmlMenuElement."""
        element = XmlMenuElement("Category")
        element.text = category
        self.append(element)
        return element

    def addDefaults(self):
        """Add Default Menu Items"""
        SubElement(self, "DefaultAppDirs")
        SubElement(self, "DefaultDirectoryDirs")
        SubElement(self, "DefaultMergeDirs")


class XmlMenuElementTree(ElementTree):
    """An extension of the ElementTree.ElementTree class which simplifies the
    creation of FD.o Menus."""

    def __init__(self, menu_name, merge_file=None):
        """Initialize the XmlMenuElementTree class.  Accepts two arguments:
        - menu_name    Name of the menu (e.g. Xfce, Gnome)
        - merge_file   Merge file, used for extending an existing menu."""
        root = XmlMenuElement("Menu", menu_name=menu_name)
        root.addDefaults()

        # Xfce toplevel support
        if menu_name == 'Xfce':
            include = root.addInclude()
            include.addCategory("X-Xfce-Toplevel")

        if merge_file:
            root.addMergeFile(merge_file)
        super().__init__(root)

    def write(self, output_file):
        """Override for the ElementTree.write function. This variation adds
        the menu specification headers and writes the output in an
        easier-to-read format."""
        header = """<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE Menu
  PUBLIC '-//freedesktop//DTD Menu 1.0//EN'
  'http://standards.freedesktop.org/menu-spec/menu-1.0.dtd'>
"""
        copy = self.getroot()
        indent(copy)
        with open(output_file, 'w') as f:
            f.write(header)
            ElementTree(copy).write(f, encoding='unicode')


def model_to_xml_menus(model, model_parent=None, menu_parent=None):
    """Append the <Menu> elements to menu_parent."""
    for n_child in range(model.iter_n_children(model_parent)):
        treeiter = model.iter_nth_child(model_parent, n_child)

        # Extract the menu item details.
        name, comment, categories, item_type, gicon, icon, desktop, expanded = \
                model[treeiter][:]

        if item_type == MenuItemTypes.DIRECTORY:
            # Do not save duplicate directories.
            global processed_directories
            if desktop in processed_directories:
                continue

            # Add a menu child.
            if desktop is None:
                # Cinnamon fix.
                if name == 'wine-wine':
                    next_element = menu_parent.addMenu(name)
                else:
                    continue
            else:
                directory_name = util.getDirectoryName(desktop)
                next_element = menu_parent.addMenu(directory_name, desktop)

            # Do Menus
            model_to_xml_menus(model, treeiter, next_element)

            # Do Includes to allow for alacarte-created entries without
            # categories to persist (see https://bugs.launchpad.net/menulibre/+bug/1315880)
            model_to_xml_includes(model, treeiter, next_element)

            # Do Layouts
            model_to_xml_layout(model, treeiter, next_element)

        elif item_type == MenuItemTypes.APPLICATION:
            pass

        elif item_type == MenuItemTypes.SEPARATOR:
            pass


def model_to_xml_includes(model, model_parent=None, menu_parent=None):
    """Append <Include> elements for any application items that lack categories
    (e.g. alacarte-created entries)."""

    for n_child in range(model.iter_n_children(model_parent)):
        treeiter = model.iter_nth_child(model_parent, n_child)

        # Extract the menu item details.
        name, comment, categories, item_type, gicon, icon, desktop, expanded = \
                model[treeiter][:]

        if item_type == MenuItemTypes.APPLICATION and not categories:
            include = menu_parent.addInclude()
            try:
                include.addFilename(os.path.basename(desktop))
            except AttributeError:
                pass


def model_to_xml_layout(model, model_parent=None, menu_parent=None, merge=True):
    """Append the <Layout> element to menu_parent."""
    layout = menu_parent.addLayout()

    # Add a merge for any submenus (except toplevel)
    if merge:
        layout.addMerge("menus")

    for n_child in range(model.iter_n_children(model_parent)):
        treeiter = model.iter_nth_child(model_parent, n_child)

        # Extract the menu item details.
        name, comment, categories, item_type, gicon, icon, desktop, expanded = \
                model[treeiter][:]

        if item_type == MenuItemTypes.DIRECTORY:
            # Do not save duplicate directories.
            global processed_directories
            if desktop in processed_directories:
                continue
            else:
                processed_directories.append(desktop)

            if desktop is None:
                # Cinnamon fix.
                if name == 'wine-wine':
                    layout.addMenuname(name)
                else:
                    continue
            else:
                directory_name = util.getDirectoryName(desktop)
                layout.addMenuname(directory_name)

        elif item_type == MenuItemTypes.APPLICATION:
            try:
                layout.addFilename(os.path.basename(desktop))
            except AttributeError:
                pass

        elif item_type == MenuItemTypes.SEPARATOR:
            layout.addSeparator()

    # Add a merge for any new/unincluded menu items (except toplevel).
    if merge:
        layout.addMerge("files")

    return layout


def model_children_to_xml(model, model_parent=None, menu_parent=None):
    """Add child menu items to menu_parent from model_parent."""
    # Prevent menu duplication that crashes gnome-menus
    global processed_directories
    processed_directories = []

    # Menus First...
    model_to_xml_menus(model, model_parent, menu_parent)

    # Includes Second... to allow for alacarte-created entries without
    # categories to persist (see https://bugs.launchpad.net/menulibre/+bug/1315880)
    model_to_xml_includes(model, model_parent, menu_parent)

    # Layouts Third...
    model_to_xml_layout(model, model_parent, menu_parent, merge=False)


def treeview_to_xml(treeview):
    """Write the current treeview to the -applications.menu file."""
    model = treeview.get_model()

    # Get the necessary details
    menu_name = MenuEditor.menu_name
    menu_file = MenuEditor.get_default_menu()
    merge_file = util.getSystemMenuPath(menu_file)
    filename = os.path.join(util.getUserMenuPath(), menu_file)

    # Create the menu XML
    menu = XmlMenuElementTree(menu_name, merge_file)
    root = menu.getroot()
    model_children_to_xml(model, menu_parent=root)

    # Write the file.
    menu.write(filename)
