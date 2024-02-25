#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2024 Sean Davis <sean@bluesabre.org>
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
import sys
import subprocess

if len(sys.argv) > 1:
    args = sys.argv[1:]
else:
    args = []

command = [sys.executable, 'setup.py', 'install'] + \
    args + ['--record', 'files.txt']
returncode = subprocess.run(
    command,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL).returncode

if returncode != 0:
    sys.stderr.write("Invalid commandline arguments provided.\n")
    sys.stderr.write(
        "Use the same commandline arguments you used to install.\n\n")
    sys.stderr.write("\t$ python3 uninstall.py --user\n")
    sys.stderr.write("\t$ sudo python3 uninstall.py\n\n")
    sys.exit(returncode)

if not os.path.exists('files.txt'):
    sys.stderr.write("Failed to generate uninstall file list.\n")
    sys.exit(1)

files = []
target = None
with open('files.txt', 'r') as filelist:
    for line in filelist.readlines():
        line = line.strip()
        files.append(line)
        if target is None and 'share' in line.split('/'):
            target = line.split('/share')[0]

os.remove('files.txt')

files.append('%s/share/pixmaps/menulibre.png' % target)
for size in ['scalable', '16x16', '24x24', '32x32', '48x48', '64x64']:
    files.append(
        '%s/share/icons/hicolor/%s/apps/menulibre.svg' %
        (target, size))

if len(files) == 0:
    sys.stderr.write("Failed to parse uninstall file list.\n")
    sys.exit(1)

for filename in files:
    if not os.path.exists(filename):
        continue
    try:
        os.remove(filename)
        print("Removing %s" % filename)
    except FileNotFoundError:
        print("Failed to remove %s" % filename)

sys.exit(0)
