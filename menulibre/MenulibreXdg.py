# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2012-2013 Sean Davis <smd.seandavis@gmail.com>
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

import os

import xdg
from xdg import BaseDirectory, DesktopEntry

import locale
from locale import gettext as _
locale.textdomain('menulibre')

from collections import OrderedDict

sudo = os.getuid() == 0
default_locale = locale.getdefaultlocale()[0]

class MenulibreDesktopEntry:
    """Basic class for Desktop Entry files"""
    def __init__(self, filename=None):
        self.filename = filename
        self.properties = OrderedDict()
        self.text = ""
        if filename:
            self.load_properties(filename)
            self.id = os.path.basename(filename)
        else:
            self.properties['Desktop Entry'] = OrderedDict()
            self.properties['Desktop Entry']['Version'] = '1.0'
            self.properties['Desktop Entry']['Type'] = 'Application'
            self.properties['Desktop Entry']['Name'] = _('New Menu Item')
            self.properties['Desktop Entry']['Comment'] = _("A small descriptive blurb about this application.")
            self.properties['Desktop Entry']['Icon'] = 'application-default-icon'
            self.properties['Desktop Entry']['Exec'] = ''
            self.properties['Desktop Entry']['Path'] = ''
            self.properties['Desktop Entry']['Terminal'] = 'false'
            self.properties['Desktop Entry']['StartupNotify'] = 'false'
            self.properties['Desktop Entry']['Categories'] = ''
            
    def __getitem__(self, prop_name):
        return self.get_property('Desktop Entry', prop_name, default_locale)
        
    def __setitem__(self, prop_name, prop_value):
        self.properties['Desktop Entry'][prop_name] = prop_value
        if prop_name in ['Name', 'Comment']:
            prop_name = "%s[%s]" % (prop_name, default_locale)
            self.properties['Desktop Entry'][prop_name] = prop_value
        
    def __str__(self):
        text = ""
        for category in self.properties:
            text += '[%s]\n' % category
            for key in self.properties[category]:
                if key.startswith("*Blank"):
                    text += "\n"
                elif key == "*OriginalName":
                    pass
                else:
                    text += "%s=%s\n" % (key, self.properties[category][key])
        return text
            
    def load_properties(self, filename):
        input_file = open(filename)
        self.load_properties_from_text(input_file.read())
        input_file.close()
                    
    def load_properties_from_text(self, text):
        current_property = ""
        self.text = text
        blank_count = 0
        for line in text.split('\n'):
            if line.startswith('[') and line.endswith(']'):
                current_property = line[1:-1]
                self.properties[current_property] = OrderedDict()
                self.properties[current_property]["*OriginalName"] = current_property.replace(' Shortcut Group', '').replace('Desktop Action ', '')
            elif '=' in line:
                try:
                    key, value = line.split('=', 1)
                    self.properties[current_property][key] = value
                except KeyError:
                    pass
            elif line.strip() == '':
                try:
                    self.properties[current_property]['*Blank%i' % blank_count] = None
                    blank_count += 1
                except KeyError:
                    pass
                
    def get_property(self, category, prop_name, locale_str=default_locale):
        print 'get_property, %s, %s' % (category, prop_name)
        prop = self.get_named_property(category, prop_name, locale_str)
        if prop in ['true', 'false']:
            return prop == 'true'
        if prop_name in ['Hidden', 'NoDisplay', 'Terminal', 'StartupNotify']:
            return False
        return prop
            
    def get_named_property(self, category, prop_name, locale_str=None):
        if locale_str:
            try:
                return self.properties[category]["%s[%s]" % (prop_name, locale_str)]
            except KeyError:
                if '_' in locale_str:
                    try:
                        return self.properties[category]["%s[%s]" % (prop_name, locale_str.split('_')[0])]
                    except KeyError:
                        pass
        try:
            return self.properties[category][prop_name]
        except KeyError:
            return ""
            
    def get_actions(self):
        quicklists = []
        if self.get_property('Desktop Entry', 'Actions') != '':
            enabled_quicklists = self.get_property('Desktop Entry', 'Actions').split(';')
            for key in self.properties:
                if key.startswith('Desktop Action'):
                    name = key[15:]
                    displayed_name = self.get_property(key, 'Name')
                    command = self.get_property(key, 'Exec')
                    enabled = name in enabled_quicklists
                    quicklists.append( (name, displayed_name, command, enabled) )
        elif self.get_property('Desktop Entry', 'X-Ayatana-Desktop-Shortcuts') != '':
            enabled_quicklists = self.get_property('Desktop Entry', 'X-Ayatana-Desktop-Shortcuts').split(';')
            for key in self.properties:
                if key.endswith('Shortcut Group'):
                    name = key[:-15]
                    displayed_name = self.get_property(key, 'Name')
                    command = self.get_property(key, 'Exec')
                    enabled = name in enabled_quicklists
                    quicklists.append( (name, displayed_name, command, enabled) )
        return quicklists
            
    def write(self, filename=None):
        if filename:
            self.filename = filename
        out_file = open(self.filename, 'w')
        out_file.write(str(self))
        out_file.close()
            
class Application(MenulibreDesktopEntry):
    def __init__(self, filename=None, name=None):
        if filename:
            if not filename.endswith('.desktop'):
                raise ValueError(_("\'%s\' is not a .desktop file") % filename)
        else:
            if not name:
                raise ValueError(_("Initialized without required parameters."))
        MenulibreDesktopEntry.__init__(self, filename)
        if name:
            if name != 'MenulibreNewLauncher':
                self.properties['Desktop Entry']['Name'] = name
        
class Directory(MenulibreDesktopEntry):
    def __init__(self, filename):
        if not filename.endswith('.directory'):
            raise ValueError(_("\'%s\' is not a .directory file") % filename)
        MenulibreDesktopEntry.__init__(self, filename)
        
def get_application_paths():
    data_dirs = BaseDirectory.xdg_data_dirs
    data_dirs.reverse()
    
    if sudo:
        data_dirs = data_dirs[:-1]
        
    application_paths = []
    for path in data_dirs:
        path = os.path.join(path, 'applications')
        if path not in application_paths and os.path.isdir(path):
            application_paths.append(path)
        
    return application_paths
        
def get_applications():
    """Return all installed applications for the current user.  If the
    program is started as root, only show system launchers."""
    applications = dict()
    
    for path in get_application_paths():
        for root, dirs, files in os.walk(path):
            for filename in files:
                if filename.endswith('.desktop'):
                    applications[filename] = Application(os.path.join(root, filename))

    return applications
    
def load_properties_from_text(text):
    properties = OrderedDict()
    current_property = ""
    blank_count = 0
    for line in text.split('\n'):
        if line.startswith('[') and line.endswith(']'):
            current_property = line[1:-1]
            properties[current_property] = OrderedDict()
        elif '=' in line:
            key, value = line.split('=', 1)
            properties[current_property][key] = value
        elif line.strip() == '':
            try:
                properties[current_property]['*Blank%i' % blank_count] = None
                blank_count += 1
            except KeyError:
                pass
    return properties
