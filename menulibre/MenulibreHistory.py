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

from locale import gettext as _

from gi.repository import GObject

import logging
logger = logging.getLogger('menulibre')


class History(GObject.GObject):
    """The MenulibreHistory object. This stores all history for Menulibre and
    allows for Undo/Redo/Revert functionality."""

    __gsignals__ = {
        'undo-changed': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_BOOLEAN,
                        (GObject.TYPE_BOOLEAN,)),
        'redo-changed': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_BOOLEAN,
                        (GObject.TYPE_BOOLEAN,)),
        'revert-changed': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_BOOLEAN,
                        (GObject.TYPE_BOOLEAN,))
    }

    def __init__(self):
        """Intialize the MenulibreHistory object."""
        GObject.GObject.__init__(self)
        self._undo = []
        self._redo = []
        self._restore = dict()
        self._block = False

    def append(self, key, before, after):
        """Add a new change to the History, clear the redo."""
        if self._block:
            return
        self._append_undo(key, before, after)
        self._clear_redo()
        self._check_revert()

    def store(self, key, value):
        """Store an original value to be used for reverting."""
        self._restore[key] = value

    def restore(self):
        """Return a copy of the restore dictionary."""
        return self._restore.copy()

    def undo(self):
        """Return the next key-value pair to undo, push it to redo."""
        key, before, after = self._pop_undo()
        self._append_redo(key, before, after)
        self._check_revert()
        return (key, before)

    def redo(self):
        """Return the next key-value pair to redo, push it to undo."""
        key, before, after = self._pop_redo()
        self._append_undo(key, before, after)
        self._check_revert()
        return (key, after)

    def clear(self):
        """Clear all history items."""
        self._clear_undo()
        self._clear_redo()
        self._restore.clear()
        self._check_revert()

    def block(self):
        """Block all future history changes."""
        logger.debug('Blocking history updates')
        self._block = True

    def unblock(self):
        """Unblock all future history changes."""
        logger.debug('Unblocking history updates')
        self._block = False

    def is_blocked(self):
        """Is History allowed currently?"""
        return self._block

    def _append_undo(self, key, before, after):
        """Internal append_undo function. Emit 'undo-changed' if the undo stack
        now contains a history."""
        self._undo.append((key, before, after))
        if len(self._undo) == 1:
            self.emit('undo-changed', True)

    def _pop_undo(self):
        """Internal pop_undo function. Emit 'undo-changed' if the undo stack is
        now empty."""
        history = self._undo.pop()
        if len(self._undo) == 0:
            self.emit('undo-changed', False)
        return history

    def _clear_undo(self):
        """Internal clear_undo function. Emit 'undo-changed' if the undo stack
        previously had items."""
        has_history = len(self._undo) > 0
        self._undo.clear()
        if has_history:
            self.emit('undo-changed', False)

    def _clear_redo(self):
        """Internal clear_redo function. Emit 'redo-changed' if the redo stack
        previously had items."""
        has_history = len(self._redo) > 0
        self._redo.clear()
        if has_history:
            self.emit('redo-changed', False)

    def _append_redo(self, key, before, after):
        """Internal append_redo function. Emit 'redo-changed' if the redo stack
        now contains a history."""
        self._redo.append((key, before, after))
        if len(self._redo) == 1:
            self.emit('redo-changed', True)

    def _pop_redo(self):
        """Internal pop_redo function. Emit 'redo-changed' if the redo stack is
        now empty."""
        history = self._redo.pop()
        if len(self._redo) == 0:
            self.emit('redo-changed', False)
        return history

    def _check_revert(self):
        """Check if revert should now be enabled and emit the 'revert-changed'
        signal."""
        if len(self._undo) == 0 and len(self._redo) == 0:
            self.emit('revert-changed', False)
        elif len(self._undo) == 1 or len(self._redo) == 1:
            self.emit('revert-changed', True)
