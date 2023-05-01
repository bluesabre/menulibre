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
import subprocess
import sys

try:
    import DistUtilsExtra.auto
except ImportError:
    sys.stderr.write("To build menulibre you need "
                     "https://launchpad.net/python-distutils-extra\n")
    sys.exit(1)
assert DistUtilsExtra.auto.__version__ >= '2.18', \
        'needs DistUtilsExtra.auto >= 2.18'


def update_config(libdir, values={}):
    """Update the configuration file at installation time."""
    filename = os.path.join(libdir, 'menulibre_lib', 'menulibreconfig.py')
    oldvalues = {}
    try:
        fin = open(filename, 'r', encoding='utf-8')
        fout = open(filename + '.new', 'w', encoding='utf-8')

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
    except (OSError, IOError):
        print(("ERROR: Can't find %s" % filename))
        sys.exit(1)
    return oldvalues


def move_icon_file(root, target_data, prefix):
    """Move the icon files to their installation prefix."""
    old_icon_path = os.path.normpath(
            os.path.join(root, target_data, 'share', 'menulibre', 'media'))
    for icon_size in ['16x16', '24x24', '32x32', '48x48', '64x64', 'scalable',
                      'pixmap']:
        # Install menulibre.png to share/pixmaps
        if icon_size == 'pixmap':
            old_icon_file = os.path.join(old_icon_path, 'menulibre.png')
            icon_path = os.path.normpath(
                        os.path.join(root, target_data, 'share', 'pixmaps'))
            icon_file = os.path.join(icon_path, 'menulibre.png')
        # Install everything else to share/icons/hicolor
        else:
            if icon_size == 'scalable':
                old_icon_file = os.path.join(old_icon_path, 'menulibre.svg')
            else:
                old_icon_file = os.path.join(old_icon_path,
                                             'menulibre_%s.svg' %
                                             icon_size.split('x')[0])
            icon_path = os.path.normpath(
                    os.path.join(root, target_data, 'share', 'icons',
                                 'hicolor', icon_size, 'apps'))
            icon_file = os.path.join(icon_path, 'menulibre.svg')

        # Get the real paths.
        old_icon_file = os.path.realpath(old_icon_file)
        icon_file = os.path.realpath(icon_file)

        if not os.path.exists(old_icon_file):
            print(("ERROR: Can't find", old_icon_file))
            sys.exit(1)
        if not os.path.exists(icon_path):
            os.makedirs(icon_path)
        if old_icon_file != icon_file:
            print(("Moving icon file: %s -> %s" % (old_icon_file, icon_file)))
            os.rename(old_icon_file, icon_file)

    # Media is now empty
    if len(os.listdir(old_icon_path)) == 0:
        print(("Removing empty directory: %s" % old_icon_path))
        os.rmdir(old_icon_path)

    return icon_file


def remove_appdata_in_file(root, target_data):
    metainfo = os.path.normpath(
        os.path.join(root, target_data, 'share', 'menulibre', 'metainfo'))
    appdata_in = os.path.join(metainfo, 'menulibre.appdata.xml.in')
    os.remove(appdata_in)
    os.rmdir(metainfo)


def get_desktop_file(root, target_data, prefix):
    """Move the desktop file to its installation prefix."""
    desktop_path = os.path.realpath(
            os.path.join(root, target_data, 'share', 'applications'))
    desktop_file = os.path.join(desktop_path, 'menulibre.desktop')
    return desktop_file


def update_desktop_file(filename, script_path):
    """Update the desktop file with prefixed paths."""
    try:
        fin = open(filename, 'r', encoding='utf-8')
        fout = open(filename + '.new', 'w', encoding='utf-8')

        for line in fin:
            if 'Exec=' in line:
                cmd = line.split("=")[1].split(None, 1)
                line = "Exec=%s" % os.path.join(script_path, 'menulibre')
                if len(cmd) > 1:
                    line += " %s" % cmd[1].strip()  # Add script arguments back
                line += "\n"
            fout.write(line)
        fout.flush()
        fout.close()
        fin.close()
        os.rename(fout.name, fin.name)
    except (OSError, IOError):
        print(("ERROR: Can't find %s" % filename))
        sys.exit(1)


def generate_changelog():
    try:
        script_path = os.path.dirname(os.path.abspath(__file__))
        git_path = os.path.join(script_path, ".git")
        if os.path.exists(git_path):
            cmd = ['git', 'log', '--pretty=format:"%ad %h %s"',
                                    '--no-merges', '--date=short']
            data = subprocess.check_output(cmd).decode("UTF-8")
            commits = data.split("\n")
            if len(commits) > 0:
                changelog_path = os.path.join(script_path, "ChangeLog")
                with open(changelog_path, "w") as outfile:
                    for line in commits:
                        outfile.write("%s\n" % line[1:-1])
    except:
        pass


def write_appdata_file(filename_in):
    filename_out = filename_in.rstrip('.in')
    cmd = ["intltool-merge", "-x", "-d", "po", filename_in, filename_out]
    print(" ".join(cmd))
    subprocess.call(cmd, shell=False)


# Update AppData with latest translations first.
write_appdata_file("data/metainfo/menulibre.appdata.xml.in")


class InstallAndUpdateDataDirectory(DistUtilsExtra.auto.install_auto):
    """Command Class to install and update the directory."""
    def run(self):
        """Run the setup commands."""
        DistUtilsExtra.auto.install_auto.run(self)

        generate_changelog()

        print(("=== Installing %s, version %s ===" %
               (self.distribution.get_name(),
                self.distribution.get_version())))

        if not self.prefix:
            self.prefix = ''

        if self.root:
            target_data = os.path.relpath(self.install_data, self.root) + \
                os.sep
            target_pkgdata = os.path.join(target_data, 'share', 'menulibre',
                                          '')
            target_scripts = os.path.join(self.install_scripts, '')

            data_dir = os.path.join(self.prefix, 'share', 'menulibre', '')
            script_path = os.path.join(self.prefix, 'bin')
        else:
            # --user install
            self.root = ''
            target_data = os.path.relpath(self.install_data) + os.sep
            target_pkgdata = os.path.join(target_data, 'share', 'menulibre',
                                          '')
            target_scripts = os.path.join(self.install_scripts, '')

            # Use absolute paths
            target_data = os.path.realpath(target_data)
            target_pkgdata = os.path.realpath(target_pkgdata)
            target_scripts = os.path.realpath(target_scripts)

            data_dir = target_pkgdata
            script_path = target_scripts

        print(("Root: %s" % self.root))
        print(("Prefix: %s\n" % self.prefix))

        print(("Target Data:    %s" % target_data))
        print(("Target PkgData: %s" % target_pkgdata))
        print(("Target Scripts: %s\n" % target_scripts))
        print(("MenuLibre Data Directory: %s" % data_dir))

        values = {'__menulibre_data_directory__': "'%s'" % (data_dir),
                  '__version__': "'%s'" % self.distribution.get_version()}
        update_config(self.install_lib, values)

        desktop_file = get_desktop_file(self.root, target_data, self.prefix)
        print(("Desktop File: %s\n" % desktop_file))
        move_icon_file(self.root, target_data, self.prefix)
        remove_appdata_in_file(self.root, target_data)
        update_desktop_file(desktop_file, script_path)


DistUtilsExtra.auto.setup(
    name='menulibre',
    version='2.3.1',
    license='GPL-3',
    author='Sean Davis',
    author_email='sean@bluesabre.org',
    description='advanced menu editor with support for Unity actions',
    long_description='An advanced menu editor that provides modern features '
                     'and full Unity action support. Suitable for lightweight '
                     'desktop environments.',
    url='https://github.com/bluesabre/menulibre',
    data_files=[('share/man/man1', ['menulibre.1',
                                    'menulibre-menu-validate.1']),
                ('share/metainfo/', ['data/metainfo/menulibre.appdata.xml'])],
    cmdclass={'install': InstallAndUpdateDataDirectory}
    )
