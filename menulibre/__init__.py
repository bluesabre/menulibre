#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2021 Sean Davis <sean@bluesabre.org>
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

import optparse
import sys

from locale import gettext as _

from menulibre import MenulibreApplication

from menulibre_lib import set_up_logging, get_version


def parse_options():
    """Support for command line options"""
    parser = optparse.OptionParser(version="%%prog %s" % get_version())
    parser.add_option(
        "-v", "--verbose", action="count", dest="verbose",
        # Translators: Command line option to display debug messages on stdout
        help=_("Show debug messages"))
    parser.add_option(
        "-b", "--headerbar", action="count", dest="headerbar",
        # Translators: Command line option to switch layout
        help=_("Use headerbar layout (client side decorations)")
    )
    parser.add_option(
        "-t", "--toolbar", action="count", dest="toolbar",
        # Translators: Command line option to switch layout
        help=_("Use toolbar layout (server side decorations)")
    )
    (options, args) = parser.parse_args()

    set_up_logging(options)

    return options


def main():
    """Main application for Menulibre"""
    opts = parse_options()

    # Run the application.
    app = MenulibreApplication.Application()
    if opts.headerbar is not None:
        app.use_headerbar = True
    elif opts.toolbar is not None:
        app.use_toolbar = True

    exit_status = app.run(None)
    sys.exit(exit_status)
