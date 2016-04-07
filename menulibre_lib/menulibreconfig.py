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

__all__ = [
    'project_path_not_found',
    'get_data_file',
    'get_data_path',
    ]

# Where your project will look for your data (for instance, images and ui
# files). By default, this is ../data, relative your trunk layout
__menulibre_data_directory__ = '../data/'
__license__ = 'GPL-3'
__version__ = '2.1.3'

import os

from locale import gettext as _  # lint:ok


class project_path_not_found(Exception):
    """Raised when we can't find the project directory."""


def get_data_file(*path_segments):
    """Get the full path to a data file.

    Returns the path to a file underneath the data directory (as defined by
    `get_data_path`). Equivalent to os.path.join(get_data_path(),
    *path_segments).
    """
    return os.path.join(get_data_path(), *path_segments)


def get_data_path():
    """Retrieve menulibre data path

    This path is by default <menulibre_lib_path>/../data/ in trunk
    and /usr/share/menulibre in an installed version but this path
    is specified at installation time.
    """
    if __menulibre_data_directory__ == '../data/':
        path = os.path.join(
            os.path.dirname(__file__), __menulibre_data_directory__)
        abs_data_path = os.path.abspath(path)
    else:
        abs_data_path = os.path.abspath(__menulibre_data_directory__)
    if not os.path.exists(abs_data_path):
        print (abs_data_path)
        raise project_path_not_found

    return abs_data_path


def get_version():
    """Retrieve the program version."""
    return __version__
