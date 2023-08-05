#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2023 Sean Davis <sean@bluesabre.org>
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

import logging

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


# lint:disable
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
# lint:enable


def set_up_logging(opts):
    """Set up logging for menulibre"""
    # add a handler to prevent basicConfig
    root = logging.getLogger()
    null_handler = NullHandler()
    root.addHandler(null_handler)

    formatter = logging.Formatter("%(levelname)s:%(name)s: "
                                  "%(funcName)s() '%(message)s'")

    logger = logging.getLogger('menulibre')
    logger_sh = logging.StreamHandler()
    logger_sh.setFormatter(formatter)
    logger.addHandler(logger_sh)

    lib_logger = logging.getLogger('menulibre_lib')
    lib_logger_sh = logging.StreamHandler()
    lib_logger_sh.setFormatter(formatter)
    lib_logger.addHandler(lib_logger_sh)

    # Set the logging level to show debug messages.
    try:
        if opts.verbose:
            logger.setLevel(logging.DEBUG)
            logger.debug('logging enabled')
        if opts.verbose > 1:
            lib_logger.setLevel(logging.DEBUG)
    except TypeError:
        pass


def show_uri(parent, link):
    """Open a web browser to the specified link."""
    screen = parent.get_screen()
    Gtk.show_uri(screen, link, Gtk.get_current_event_time())


def alias(alternative_function_name):
    '''see http://www.drdobbs.com/web-development/184406073#l9'''
    def decorator(function):
        '''attach alternative_function_name(s) to function'''
        if not hasattr(function, 'aliases'):
            function.aliases = []
        function.aliases.append(alternative_function_name)
        return function
    return decorator
