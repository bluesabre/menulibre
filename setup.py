#!/usr/bin/env python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2012-2014 Sean Davis <smd.seandavis@gmail.com>
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
import sys

try:
    import DistUtilsExtra.auto
except ImportError:
    print("To build menulibre you need "
          "https://launchpad.net/python-distutils-extra",
          file=sys.stderr)  # lint:ok
    sys.exit(1)
assert(DistUtilsExtra.auto.__version__ >= '2.18',
        'needs DistUtilsExtra.auto >= 2.18')


def update_config(libdir, values={}):
    """Update the configuration file at installation time."""
    filename = os.path.join(libdir, 'menulibre_lib/menulibreconfig.py')
    oldvalues = {}
    try:
        fin = file(filename, 'r')
        fout = file(filename + '.new', 'w')

        for line in fin:
            fields = line.split(' = ')  # Separate variable from value
            if fields[0] in values:
                oldvalues[fields[0]] = fields[1].strip()
                line = "%s = %s\n" % (fields[0], values[fields[0]])
            fout.write(line)

        fout.flush()
        fout.close()
        fin.close()
        os.rename(fout.name, fin.name)
    except (OSError, IOError), e:
        print ("ERROR: Can't find %s" % filename)
        sys.exit(1)
    return oldvalues


def move_icon_file(root, target_data, prefix):
    """Move the icon files to their installation prefix."""
    old_icon_path = os.path.normpath(root + target_data +
                                    '/share/menulibre/media')
    for icon_size in ['16x16', '22x22', '24x24', '48x48', '64x64', 'scalable']:
        if icon_size == 'scalable':
            old_icon_file = old_icon_path + '/menulibre.svg'
        else:
            old_icon_file = old_icon_path + '/menulibre_%s.svg' % \
                            icon_size.split('x')[0]
        icon_path = os.path.normpath(root + prefix +
                                    '/share/icons/hicolor/%s/apps' % icon_size)
        icon_file = icon_path + '/menulibre.svg'

        if not os.path.exists(old_icon_file):
            print ("ERROR: Can't find", old_icon_file)
            sys.exit(1)
        if not os.path.exists(icon_path):
            os.makedirs(icon_path)
        if old_icon_file != icon_file:
            os.rename(old_icon_file, icon_file)

    return icon_file


def move_desktop_file(root, target_data, prefix):
    """Move the desktop file to its installation prefix."""
    old_desktop_path = os.path.normpath(root + target_data +
                                        '/share/applications')
    old_desktop_file = old_desktop_path + '/menulibre.desktop'
    desktop_path = os.path.normpath(root + prefix + '/share/applications')
    desktop_file = desktop_path + '/menulibre.desktop'

    if not os.path.exists(old_desktop_file):
        print ("ERROR: Can't find", old_desktop_file)
        sys.exit(1)

    return desktop_file


def update_desktop_file(filename, target_pkgdata, target_scripts):
    """Update the desktop file with prefixed paths."""
    try:
        fin = file(filename, 'r')
        fout = file(filename + '.new', 'w')

        for line in fin:
            if 'Exec=' in line:
                cmd = line.split("=")[1].split(None, 1)
                line = "Exec=%s" % (target_scripts + 'menulibre')
                if len(cmd) > 1:
                    line += " %s" % cmd[1].strip()  # Add script arguments back
                line += "\n"
            fout.write(line)
        fout.flush()
        fout.close()
        fin.close()
        os.rename(fout.name, fin.name)
    except (OSError, IOError), e:
        print ("ERROR: Can't find %s" % filename)
        sys.exit(1)


class InstallAndUpdateDataDirectory(DistUtilsExtra.auto.install_auto):
    def run(self):
        DistUtilsExtra.auto.install_auto.run(self)

        if not self.root:
            self.root = ''

        target_data = '/' + os.path.relpath(self.install_data, self.root) + '/'
        target_pkgdata = target_data + 'share/menulibre/'
        target_scripts = '/' + \
                        os.path.relpath(self.install_scripts, self.root) + '/'

        values = {'__menulibre_data_directory__': "'%s'" % (target_pkgdata),
                  '__version__': "'%s'" % self.distribution.get_version()}
        update_config(self.install_lib, values)

        desktop_file = move_desktop_file(self.root, target_data, self.prefix)
        icon_file = move_icon_file(self.root, target_data, self.prefix)
        update_desktop_file(desktop_file, target_pkgdata, target_scripts)

DistUtilsExtra.auto.setup(
    name='menulibre',
    version='0.1',
    license='GPL-3',
    author='Sean Davis',
    author_email='smd.seandavis@gmail.com',
    #description='UI for managing …',
    #long_description='Here a longer description',
    url='https://launchpad.net/menulibre',
    cmdclass={'install': InstallAndUpdateDataDirectory}
    )
