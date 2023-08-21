#!/usr/bin/python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   MenuLibre - Advanced fd.o Compliant Menu Editor
#   Copyright (C) 2012-2023 Sean Davis <sean@bluesabre.org>
#   Copyright (C) 2016 OmegaPhil <OmegaPhil@startmail.com>
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

from locale import gettext as _
from xml.sax.saxutils import escape

from gi.repository import Gio, GObject, Gtk, Pango, GLib

from . import MenuEditor, MenulibreXdg, XmlMenuElementTree, util
from .util import MenuItemTypes, check_keypress, getBasename, getRelativeName, escapeText

import logging
logger = logging.getLogger('menulibre')


class Treeview(Gtk.Box):

    __gsignals__ = {
        'cursor-changed': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_BOOLEAN,
                           (GObject.TYPE_BOOLEAN,)),
        'add-directory-enabled': (GObject.SIGNAL_RUN_LAST,
                                  GObject.TYPE_BOOLEAN,
                                  (GObject.TYPE_BOOLEAN,)),
        'requires-menu-reload': (GObject.SIGNAL_RUN_LAST,
                                 GObject.TYPE_BOOLEAN,
                                 (GObject.TYPE_BOOLEAN,)),
    }

    loaded = False

    def __init__(self, parent):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.parent = parent
        self._last_selected_path = -1
        self._search_terms = None
        self._lock_menus = False

        self.set_size_request(220, -1)

        treestore = MenuEditor.get_treestore()
        if treestore:
            self.loaded = True

        scrolled = Gtk.ScrolledWindow.new(hadjustment=None, vadjustment=None)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        scrolled.set_name("MenulibreSidebarScroll")
        self.pack_start(scrolled, True, True, 0)

        self._treeview = Gtk.TreeView.new_with_model(treestore)
        self._treeview.set_show_expanders(True)
        self._treeview.set_enable_search(False)
        self._treeview.set_headers_visible(False)
        scrolled.add(self._treeview)

        # Translators: "Search Results" treeview column header
        col = Gtk.TreeViewColumn(_("Search Results"))

        # Icon renderer
        col_cell_img = Gtk.CellRendererPixbuf()
        col_cell_img.set_property("stock-size", Gtk.IconSize.LARGE_TOOLBAR)
        col.pack_start(col_cell_img, False)

        # Text renderer
        col_cell_text = Gtk.CellRendererText()
        col_cell_text.set_property("ellipsize", Pango.EllipsizeMode.END)
        col.pack_start(col_cell_text, True)

        # Set the markup property on the Text cell.
        col.add_attribute(col_cell_text, "markup", MenuEditor.COL_DISPLAY_NAME)

        # Add the cell data func for the text column to render labels.
        col.set_cell_data_func(col_cell_text, self._text_display_func, None)

        # Set the Tooltip column.
        self._treeview.set_tooltip_column(1)

        # Add the cell data func for the pixbuf column to render icons.
        col.set_cell_data_func(col_cell_img, self._icon_name_func, None)

        # Append the column, set the model.
        self._treeview.append_column(col)

        # Configure the treeview events.
        self._treeview.connect("cursor-changed",
                               self._on_treeview_cursor_changed, None)
        self._treeview.connect("key-press-event",
                               self._on_treeview_key_press_event, None)
        self._treeview.connect("row-expanded",
                               self._on_treeview_row_expansion, True)
        self._treeview.connect("row-collapsed",
                               self._on_treeview_row_expansion, False)

        self.menu_timeout_id = 0

        self._toolbar = Gtk.Toolbar.new()
        self._toolbar.set_icon_size(Gtk.IconSize.MENU)
        self._toolbar.set_name("MenulibreSidebarToolbar")
        self.add(self._toolbar)

        context = self._toolbar.get_style_context()
        context.add_class("inline-toolbar")

        img = Gtk.Image.new_from_icon_name('go-up-symbolic', Gtk.IconSize.MENU)
        self._move_up_button = Gtk.ToolButton.new(img, _("Move Up"))
        self._move_up_button.set_tooltip_text(_("Move Up"))
        self._move_up_button.connect(
            'clicked', self._move_iter, (self._treeview, -1))
        self._toolbar.add(self._move_up_button)

        img = Gtk.Image.new_from_icon_name(
            'go-down-symbolic', Gtk.IconSize.MENU)
        self._move_down_button = Gtk.ToolButton.new(img, _("Move Down"))
        self._move_down_button.set_tooltip_text(_("Move Down"))
        self._move_down_button.connect(
            'clicked', self._move_iter, (self._treeview, 1))
        self._toolbar.add(self._move_down_button)

        img = Gtk.Image.new_from_icon_name(
            'view-sort-ascending-symbolic', Gtk.IconSize.MENU)
        self._sort_button = Gtk.ToolButton.new(img, _("Sort Alphabetically"))
        self._sort_button.set_tooltip_text(_("Sort Alphabetically"))
        self._sort_button.connect('clicked', self._sort_iter)
        self._toolbar.add(self._sort_button)

        # Show the treeview, grab focus.
        self.show_all()
        self._treeview.grab_focus()

    def set_sortable(self, sortable):
        self._sort_button.set_sensitive(sortable)

    def set_move_up_enabled(self, enabled):
        self._move_up_button.set_sensitive(enabled)

    def set_move_down_enabled(self, enabled):
        self._move_down_button.set_sensitive(enabled)

# TreeView Modifiers
    def append(self, row_data):
        """Add a new launcher entry below the current selected one."""
        model, treeiter = self._get_selected_iter()
        model, parent = self.get_parent()

        new_iter = model.insert_after(parent, treeiter)
        self._populate_and_select_iter(model, new_iter, row_data)

        return new_iter

    def prepend(self, row_data):
        """Add a new launcher entry above the current selected one."""
        model, treeiter = self._get_selected_iter()
        parent = self.get_parent()

        new_iter = model.insert_before(parent, treeiter)
        self._populate_and_select_iter(model, new_iter, row_data)

        return new_iter

    def add_child(self, row_data, treeiter=None, model=None, do_select=True):
        """Add a new child launcher to the current selected one, or the
        specified iter if adding elsewhere in the tree, with optional
        selection."""
        if treeiter is None or model is None:
            model, treeiter = self._get_selected_iter()

        new_iter = model.prepend(treeiter)

        if do_select:
            self._treeview.expand_row(model[treeiter].path, False)

        self._populate_and_select_iter(model, new_iter, row_data, do_select)

        return new_iter

    def remove_selected(self, ui_only=False):  # noqa
        """Remove the selected launcher. If ui_only is True, the associated
        desktop file is not deleted but the launcher is removed from the
        interface. This is useful for removing categories."""

        self._last_selected_path = -1
        model, treeiter = self._get_selected_iter()

        if not ui_only:

            filename = model[treeiter][MenuEditor.COL_FILENAME]
            item_type = model[treeiter][MenuEditor.COL_TYPE]
            if filename is not None:
                basename = getRelativeName(filename)
                original = util.getSystemLauncherPath(basename)
            else:
                original = None

            # Get files for deletion - only one item can be selected at a time,
            # but this may be a directory
            del_dirs, del_apps = self._get_delete_filenames(model, treeiter)
            del_files = del_dirs + del_apps

            # Uninstall the launcher
            self.xdg_menu_uninstall(model, treeiter, filename)

            # Delete each of the files - this will fail silently for non-user
            # desktop files/directories, these are hidden below
            for filename in del_files:
                try:
                    os.remove(filename)
                except:  # noqa
                    pass

        self.xdg_menu_update()
        self._cleanup_applications_merged()

        if not ui_only:

            # How is it possible that a launcher is to be removed, but its
            # associated desktop file has not been returned to be deleted?
            if filename not in del_files:
                # Update the required categories.
                model, parent_data = self.get_parent_row_data()
                if parent_data is not None:
                    categories = util.getRequiredCategories(
                        parent_data[MenuEditor.COL_FILENAME])
                else:
                    categories = util.getRequiredCategories(None)
                self.parent.update_launcher_categories(categories, [])

            if original is not None:
                # Original found (this is a system-installed desktop file/
                # directory rather than a user-made one), hide the desktop file
                # and all associated instances in the menu
                entry = MenulibreXdg.MenulibreDesktopEntry(original)
                name = entry['Name']
                comment = entry['Comment']
                categories = entry['Categories']
                executable = entry['Exec']
                icon_name = entry['Icon']
                hidden = entry['Hidden'] or entry['NoDisplay']
                self.update_selected(
                    name,
                    comment,
                    executable,
                    categories,
                    item_type,
                    icon_name,
                    original,
                    not hidden)
                model, row_data = self.get_selected_row_data()
                self.update_launcher_instances(filename, row_data)
                treeiter = None

        if treeiter is not None:
            path = model.get_path(treeiter)
            if model is not None and treeiter is not None:
                if not isinstance(model, Gtk.TreeModelFilter):
                    model.remove(treeiter)
            if path:
                self._treeview.set_cursor(path)

        self.update_menus()

    def remove_iter(self, model, treeiter):
        """Remove launcher pointed to by iter from the model only - use this
        when you need to remove a launcher from a non-selected directory, e.g.
        when the associated category has been removed"""

        # This feels a bit redundant for a function, but it keeps the
        # functionality close to remove_selected
        model.remove(treeiter)

# Get
    def get_parent(self, model=None, treeiter=None):
        """Get the parent iterator for the current treeiter"""
        parent = None
        if model is None:
            model, treeiter = self._get_selected_iter()
        if treeiter:
            path = model.get_path(treeiter)
            if path.up():
                if path.get_depth() > 0:
                    try:
                        parent = model.get_iter(path)
                    except:  # noqa
                        parent = None
        return model, parent

    def is_first(self, model=None, treeiter=None):
        if model is None:
            model, treeiter = self._get_selected_iter()
        if treeiter:
            path = model.get_path(treeiter)
            if path.prev():
                return False
        return True

    def _next(self, model, treeiter, path):
        # path.next() seems to be broken, so we will do it ourselves.
        try:
            string = path.to_string()
            parts = string.split(":")
            parts[-1] = str(int(parts[-1]) + 1)
            string = ":".join(parts)
            path = Gtk.TreePath.new_from_string(string)
            model.get_iter(path)
        except (TypeError, ValueError):
            return None
        return path

    def is_last(self, model=None, treeiter=None):
        if model is None:
            model, treeiter = self._get_selected_iter()
        if treeiter:
            path = model.get_path(treeiter)

            if self._next(model, treeiter, path) is not None:
                return False
        return True

    def get_parent_filename(self):
        """Get the filename of the parent iter."""
        model, parent = self.get_parent()
        if parent is None:
            return None
        return model[parent][MenuEditor.COL_FILENAME]

    def get_parent_row_data(self):
        """Get the row data of the parent iter."""
        model, parent = self.get_parent()
        if parent is not None:
            return model, model[parent][:]
        return model, None

    def get_selected_filename(self):
        """Return the filename of the current selected treeiter."""
        model, row_data = self.get_selected_row_data()
        if row_data is not None:
            return row_data[MenuEditor.COL_FILENAME]
        return None

    def get_selected_row_data(self):
        """Get the row data of the current selected item."""
        model, treeiter = self._get_selected_iter()
        if model is None or treeiter is None:
            return model, None
        return model, model[treeiter][:]

# Set
    def set_can_select_function(self, can_select_func):
        """Set the external function used for can-select."""
        selection = self._treeview.get_selection()
        selection.set_select_function(self._on_treeview_selection,
                                      can_select_func)

# Update
    def update_launcher_instances(self, filename, row_data):
        """Update all same launchers with the new information."""
        model, treeiter = self._get_selected_iter()
        for instance in self._get_launcher_instances(filename, model):
            for i in range(len(row_data)):
                model[instance][i] = row_data[i]

    def update_selected(self, name, comment, executable, categories, item_type,
                        icon_name, filename, show=True):
        """Update the application treeview selected row data."""
        model, treeiter = self._get_selected_iter()
        model[treeiter][MenuEditor.COL_NAME] = name
        model[treeiter][MenuEditor.COL_DISPLAY_NAME] = escape(name)
        model[treeiter][MenuEditor.COL_COMMENT] = escapeText(comment)
        model[treeiter][MenuEditor.COL_EXEC] = executable
        model[treeiter][MenuEditor.COL_CATEGORIES] = categories
        model[treeiter][MenuEditor.COL_TYPE] = item_type
        if os.path.isfile(icon_name):
            gfile = Gio.File.parse_name(icon_name)
            icon = Gio.FileIcon.new(gfile)
        else:
            icon = Gio.ThemedIcon.new(icon_name)
        model[treeiter][MenuEditor.COL_G_ICON] = icon
        model[treeiter][MenuEditor.COL_ICON_NAME] = icon_name
        model[treeiter][MenuEditor.COL_FILENAME] = filename
        model[treeiter][MenuEditor.COL_SHOW] = show

        # Refresh the displayed launcher
        self._last_selected_path = -1
        self._on_treeview_cursor_changed(self._treeview, None)

# Events
    def _on_treeview_cursor_changed(self, widget, selection):
        """Update the editor frame when the selected row is changed."""
        # Check if the selection is valid.
        sel = widget.get_selection()
        if sel:
            treestore, treeiter = sel.get_selected()
            if not treestore:
                return
            if not treeiter:
                return

            # Do nothing if we didn't change path
            path = str(treestore.get_path(treeiter))
            if path == self._last_selected_path:
                return
            self._last_selected_path = path

            # Notify the application that the cursor selection has changed.
            self.emit("cursor-changed", True)

            # Update the Add Directory menu item
            self._update_add_directory()

    def _on_treeview_key_press_event(self, widget, event, user_data=None):
        """Handle treeview keypress events."""
        # Right expands the selected row.
        if check_keypress(event, ['right']):
            self._set_treeview_selected_expanded(widget, True)
            return True
        # Left collapses the selected row.
        elif check_keypress(event, ['left']):
            self._set_treeview_selected_expanded(widget, False)
            return True
        # Spacebar toggles the expansion of the selected row.
        elif check_keypress(event, ['space']):
            self._toggle_treeview_selected_expanded(widget)
            return True
        return False

    def _on_treeview_row_expansion(self, treeview, treeiter, column, expanded):
        if self._toolbar.get_sensitive():
            model = treeview.get_model()
            row = model[treeiter]
            row[MenuEditor.COL_EXPAND] = expanded

    def _on_treeview_selection(self, sel, store, path, is_selected,
                               can_select_func):
        """Save changes on cursor change."""
        if is_selected:
            return can_select_func()
        return True

# Helper functions
    def _set_treeview_selected_expanded(self, treeview, expanded=True):
        """Set the expansion (True or False) of the selected row."""
        sel = treeview.get_selection()
        model, treeiter = sel.get_selected()
        row = model[treeiter]
        if expanded:
            treeview.expand_row(row.path, False)
        else:
            treeview.collapse_row(row.path)

    def _toggle_treeview_selected_expanded(self, treeview):
        """Toggle the expansion of the selected row."""
        expanded = self._get_treeview_selected_expanded(treeview)
        self._set_treeview_selected_expanded(treeview, not expanded)

    def _text_display_func(self, col, renderer, treestore, treeiter,
                           user_data):
        """CellRenderer function to set the gicon for each row."""
        show = treestore[treeiter][MenuEditor.COL_SHOW]
        if show:
            renderer.set_property("style", Pango.Style.NORMAL)
        else:
            renderer.set_property("style", Pango.Style.ITALIC)
        separator = treestore[treeiter][MenuEditor.COL_TYPE] == MenuItemTypes.SEPARATOR
        renderer.set_property("sensitive", not separator)
        renderer.set_property("style-set", True)

    def _icon_name_func(self, col, renderer, treestore, treeiter, user_data):
        """CellRenderer function to set the gicon for each row."""
        renderer.set_property("gicon",
                              treestore[treeiter][MenuEditor.COL_G_ICON])
        separator = treestore[treeiter][MenuEditor.COL_TYPE] == MenuItemTypes.SEPARATOR
        renderer.set_property("sensitive", not separator)

    def _get_selected_iter(self):
        """Return the current treeview model and selected iter."""
        model, treeiter = self._treeview.get_selection().get_selected()
        return model, treeiter

    def _populate_and_select_iter(self, model, treeiter, row_data,
                                  do_select=True):
        """Fill the specified treeiter with data and optionally select it."""
        for i in range(len(row_data)):
            model[treeiter][i] = row_data[i]

        # Select the new iter if requested
        if do_select:
            path = model.get_path(treeiter)
            self._treeview.set_cursor(path)

    def _get_deletable_launcher(self, filename):
        """Return True if the launcher is available for deletion."""
        if not os.path.exists(filename):
            return False
        return True

    def _get_delete_filenames(self, model, treeiter):  # noqa
        """Return a list of files to be deleted after uninstall."""
        directories = []
        applications = []

        filename = model[treeiter][MenuEditor.COL_FILENAME]
        block_run = False

        if filename is not None:
            basename = getRelativeName(filename)
            original = util.getSystemLauncherPath(basename)
            item_type = model[treeiter][MenuEditor.COL_TYPE]
            if original is None and item_type == MenuItemTypes.DIRECTORY:
                pass
            else:
                block_run = True

        if model.iter_has_child(treeiter) and not block_run:
            for i in range(model.iter_n_children(treeiter)):
                child_iter = model.iter_nth_child(treeiter, i)
                filename = model[child_iter][MenuEditor.COL_FILENAME]
                if filename is not None:
                    if filename.endswith('.directory'):
                        d, a = self._get_delete_filenames(model, child_iter)
                        directories = directories + d
                        applications = applications + a
                        directories.append(filename)
                    else:
                        if self._get_deletable_launcher(filename):
                            applications.append(filename)

        filename = model[treeiter][MenuEditor.COL_FILENAME]
        if filename is not None:
            if filename.endswith('.directory'):
                directories.append(filename)
            else:
                if self._get_deletable_launcher(filename):
                    applications.append(filename)
        return directories, applications

    def _get_treeview_selected_expanded(self, treeview):
        """Return True if the selected row is currently expanded."""
        sel = treeview.get_selection()
        model, treeiter = sel.get_selected()
        row = model[treeiter]
        return treeview.row_expanded(row.path)

    def _get_launcher_instances(self, filename, model=None, parent=None):
        """Return a list of all treeiters referencing this filename."""
        if filename is None:
            return []
        if model is None:
            model, treeiter = self._get_selected_iter()
        treeiters = []
        for n_child in range(model.iter_n_children(parent)):
            treeiter = model.iter_nth_child(parent, n_child)
            iter_filename = model[treeiter][MenuEditor.COL_FILENAME]
            if iter_filename == filename:
                treeiters.append(treeiter)
            if model.iter_has_child(treeiter):
                treeiters += self._get_launcher_instances(filename, model,
                                                          treeiter)
        return treeiters

    def _get_n_launcher_instances(self, filename):
        return len(self._get_launcher_instances(filename))

    def _is_menu_locked(self):
        """Return True if menu editing is currently locked."""
        return self._lock_menus

    def _update_add_directory(self):
        """Prevent adding subdirectories to system menus."""
        add_enabled = True
        prefix = util.getDefaultMenuPrefix()

        treestore, treeiter = self._get_selected_iter()
        model, parent_iter = self.get_parent()
        while parent_iter is not None:
            filename = treestore[parent_iter][MenuEditor.COL_FILENAME]
            if getBasename(filename).startswith(prefix):
                add_enabled = False
            model, parent_iter = self.get_parent(treestore, parent_iter)

        self.emit("add-directory-enabled", add_enabled)

# Search
    def search(self, terms):
        """Search the treeview for the specified terms."""
        self._search_terms = str(terms.lower())
        model = self._treeview.get_model()
        model.refilter()

    def set_searchable(self, searchable, expand=False):
        """Set the TreeView searchable."""
        model = self._treeview.get_model()
        if searchable:
            self._lock_menus = True
            # Show the "Search Results" header and disable the inline toolbar.
            self._treeview.set_headers_visible(True)
            self._toolbar.set_sensitive(False)

            # If specified, expand the treeview.
            if expand:
                self._treeview.expand_all()

            # If the model is not a filter, make it so.
            if not isinstance(model, Gtk.TreeModelFilter):
                model = model.filter_new()
                self._treeview.set_model(model)
                model.set_visible_func(self._treeview_match_func)

        else:
            self._lock_menus = False
            # Hide the headers and enable the inline toolbar.
            self._treeview.set_headers_visible(False)
            self._toolbar.set_sensitive(True)

            if isinstance(model, Gtk.TreeModelFilter):
                # Get the model and iter.
                f_model, f_iter = self._get_selected_iter()

                # Restore the original model.
                model = model.get_model()
                self._treeview.set_model(model)

                # Restore expanded items (lp 1307000)
                self._treeview.collapse_all()
                for n_child in range(model.iter_n_children(None)):
                    treeiter = model.iter_nth_child(None, n_child)
                    row = model[treeiter]
                    if row[MenuEditor.COL_FILENAME]:
                        self._treeview.expand_row(row.path, False)

                # Try to get the row that was selected previously.
                if (f_model is not None) and (f_iter is not None):
                    row_data = f_model[f_iter][:]
                    selected_iter = self._get_iter_by_data(row_data, model,
                                                           parent=None)

                # If that fails, just select the first iter.
                else:
                    selected_iter = model.get_iter_first()

                # Set the cursor.
                path = model.get_path(selected_iter)
                self._treeview.set_cursor(path)

    def _treeview_match(self, model, treeiter, query):
        """Match subfunction for filtering search results."""
        name = model[treeiter][MenuEditor.COL_NAME]
        comment = model[treeiter][MenuEditor.COL_COMMENT]
        executable = model[treeiter][MenuEditor.COL_EXEC]
        item_type = model[treeiter][MenuEditor.COL_TYPE]
        desktop = model[treeiter][MenuEditor.COL_FILENAME]

        # Hide separators in the search results.
        if item_type == MenuItemTypes.SEPARATOR:
            return False

        # Convert None to blank.
        if not name:
            name = ""
        if not comment:
            comment = ""
        if not executable:
            executable = ""

        # Expand all the rows.
        self._treeview.expand_all()

        # Match against the name.
        if query in name.lower():
            return True

        # Match against the comment.
        if query in comment.lower():
            return True

        if query in executable.lower():
            return True

        # Match against the desktop file.
        desktop = desktop.replace("menulibre-", "")
        desktop = desktop.replace("alacarte-", "")
        if query in desktop.lower():
            return True

        # Show the directory if any child items match.
        if item_type == MenuItemTypes.DIRECTORY:
            return self._treeview_match_directory(query, model, treeiter)

        # No matches, return False.
        return False

    def _treeview_match_directory(self, query, model, treeiter):
        """Match subfunction for matching directory children."""
        for child_i in range(model.iter_n_children(treeiter)):
            child = model.iter_nth_child(treeiter, child_i)
            if self._treeview_match(model, child, query):
                return True

        return False

    def _treeview_match_func(self, model, treeiter, data=None):
        """Match function for filtering search results."""
        # Make the query case-insensitive.
        if self._search_terms == "":
            return True

        return self._treeview_match(model, treeiter, self._search_terms)

# XDG Menu Commands
    def xdg_menu_install(self, filename, parent=None):
        """Install the specified filename in the menu structure."""
        model, treeiter = self._get_selected_iter()
        if filename is None:
            return
        if filename.endswith('.desktop'):
            menu_install = True
            parents = []
            if parent is None:
                parent = model.iter_parent(treeiter)
            while parent is not None:
                parent_filename = model[parent][MenuEditor.COL_FILENAME]

                # Do not do this method if this is a known system directory.
                parents.append(parent_filename)
                parent = model.iter_parent(parent)
            parents.reverse()
            if menu_install:
                installed = MenulibreXdg.desktop_menu_install(parents, [
                                                              filename])
                if not installed:
                    self.emit("requires-menu-reload", True)

    def xdg_menu_uninstall(self, model, treeiter, filename):
        """Uninstall the specified filename from the menu structure."""
        if filename is None:
            return
        if filename.endswith('.desktop'):
            menu_install = True
            menu_prefix = util.getDefaultMenuPrefix()
            parents = []
            parent = model.iter_parent(treeiter)
            while parent is not None:
                parent_filename = model[parent][MenuEditor.COL_FILENAME]
                # Do not do this method if this is a known system directory.
                if getBasename(parent_filename).startswith(menu_prefix):
                    menu_install = False
                parents.append(parent_filename)
                parent = model.iter_parent(parent)
            parents.reverse()
            if menu_install:
                MenulibreXdg.desktop_menu_uninstall(parents, [filename])

    def xdg_menu_update(self):
        """Force an update of the Xdg Menu."""
        MenulibreXdg.desktop_menu_update()

    def update_menus(self):
        """Update the menu files."""
        if self.menu_timeout_id > 0:
            GLib.source_remove(self.menu_timeout_id)
        self.menu_timeout_id = GLib.timeout_add_seconds(
            1, self.update_menu_timeout)

    def update_menu_timeout(self):
        # Do not save menu layout if in search mode (lp #1306999)
        if not self._is_menu_locked():
            XmlMenuElementTree.treeview_to_xml(self._treeview)
            self.update_menus_kde()
        self.menu_timeout_id = 0
        return False

    def update_menus_kde(self):
        try:
            subprocess.Popen(["kbuildsycoca5"])
        except FileNotFoundError:
            pass

    def _cleanup_applications_merged(self):
        """Cleanup items from ~/.config/menus/applications-merged"""
        # xdg-desktop-menu installs menu files in
        # ~/.config/menus/applications-merged, but does not remove them
        # correctly.
        merged_dir = os.path.join(GLib.get_user_config_dir(),
                                  "menus", "applications-merged")

        # Get the list of installed user directories to compare with.
        directories_dir = os.path.join(GLib.get_home_dir(),
                                       ".local", "share",
                                       "desktop-directories")
        if os.path.isdir(directories_dir):
            directories = os.listdir(directories_dir)
        else:
            directories = []

        # Check if applications-merged actually exists...
        if os.path.isdir(merged_dir):
            for menufile in os.listdir(merged_dir):
                menufile = os.path.join(merged_dir, menufile)
                remove_file = False

                # Only interested in .menu files
                if os.path.isfile(menufile) and menufile.endswith('.menu'):
                    logger.debug("Checking if %s is still valid..." %
                                 menufile)

                    # Read the menufile to see if it has a valid directory.
                    with open(menufile) as menufile_tmp:
                        for line in menufile_tmp.readlines():
                            if "<Directory>" in line:
                                menuname = line.split('<Directory>')[1]
                                menuname = menuname.split('</Directory>')[0]
                                menuname = menuname.strip()

                                # Remove if a listed directory is not installed
                                if menuname not in directories:
                                    remove_file = True
                    if remove_file:
                        logger.debug("Removing useless %s" % menufile)
                        os.remove(menufile)

# TreeView iter tricks
    def _move_iter(self, widget, user_data):  # noqa
        """Move the currently selected row up or down. If the neighboring row
        is expanded, make the selected row a child of the neighbor row.

        Keyword arguments:
        widget -- the triggering GtkWidget
        user_data -- list-packed parameters:
            treeview -- the GtkTreeview being modified
            relative_position -- 1 or -1, determines moving up or down

        """
        # Unpack the user data
        treeview, relative_position = user_data

        # Get the current selected row
        sel = treeview.get_selection().get_selected()
        if sel:
            model, selected_iter = sel
            selected_type = model[selected_iter][MenuEditor.COL_TYPE]

            # Get current required categories
            model, parent = self.get_parent(model, selected_iter)
            if parent:
                categories = util.getRequiredCategories(
                    model[parent][MenuEditor.COL_FILENAME])
            else:
                categories = util.getRequiredCategories(None)

            # Move the row up if relative_position < 0
            if relative_position < 0:
                sibling_iter = model.iter_previous(selected_iter)
            else:
                sibling_iter = model.iter_next(selected_iter)

            if sibling_iter:
                sibling_path = model.get_path(sibling_iter)

                # Determine where the item is being inserted.
                move_down = False

                # What is the neighboring item?
                sibling_type = model[sibling_iter][MenuEditor.COL_TYPE]

                # Sibling Directory
                if sibling_type == MenuItemTypes.DIRECTORY:
                    # Do not move directories into other directories.
                    if selected_type == MenuItemTypes.DIRECTORY:
                        move_down = False

                    # Append or Prepend to expanded directories.
                    elif treeview.row_expanded(sibling_path):
                        move_down = True

                    # Append to childless directories (lp: #1318209)
                    elif not model.iter_has_child(sibling_iter):
                        move_down = True

                # Insert the selected item into the directory.
                if move_down:
                    selected_iter = self._move_iter_down_level(
                        treeview, selected_iter,
                        sibling_iter, relative_position)

                # Move the selected item before or after the sibling item.
                else:
                    if relative_position < 0:
                        model.move_before(selected_iter, sibling_iter)
                    else:
                        model.move_after(selected_iter, sibling_iter)

            # If there is no neighboring row, move up a level.
            else:
                selected_iter = self._move_iter_up_level(
                    treeview, selected_iter, relative_position)

            # Get new required categories
            model, parent = self.get_parent(model, selected_iter)
            if parent:
                new_categories = util.getRequiredCategories(
                    model[parent][MenuEditor.COL_FILENAME])
            else:
                new_categories = util.getRequiredCategories(None)

            # Replace required categories
            if categories != new_categories:
                editor_categories = self.parent.get_editor_categories()
                split_categories = editor_categories.split(';')
                for category in categories:
                    if category in split_categories:
                        split_categories.remove(category)
                for category in new_categories:
                    if category not in split_categories:
                        split_categories.append(category)
                split_categories.sort()
                editor_categories = ';'.join(split_categories)
                self.parent.set_editor_categories(editor_categories)
                self.parent.update_launcher_categories(categories,
                                                       new_categories)

        self.update_menus()

        self.scroll_to_selection()

        self.emit("cursor-changed", True)

    def _get_iter_by_data(self, row_data, model, parent=None):
        """Search the TreeModel for a row matching row_data.

        Return the TreeIter found or None if none found."""
        for n_child in range(model.iter_n_children(parent)):
            treeiter = model.iter_nth_child(parent, n_child)
            if model[treeiter][:] == row_data:
                return treeiter
            if model.iter_n_children(treeiter) != 0:
                value = self._get_iter_by_data(row_data, model, treeiter)
                if value is not None:
                    return value
        return None

    def _move_iter_up_level(self, treeview, treeiter, relative_position):
        """Move the specified iter up one level."""
        model = treeview.get_model()
        sibling = model.iter_parent(treeiter)
        if sibling is not None:
            parent = model.iter_parent(sibling)
            row_data = model[treeiter][:]
            if relative_position < 0:
                new_iter = model.insert_before(parent,
                                               sibling,
                                               row_data)
            else:
                new_iter = model.insert_after(parent,
                                              sibling,
                                              row_data)

            # Install/Uninstall items from directories.
            filename = row_data[MenuEditor.COL_FILENAME]
            self.xdg_menu_install(filename)
            self.xdg_menu_uninstall(model, treeiter, filename)

            model.remove(treeiter)
            path = model.get_path(new_iter)
            treeview.set_cursor(path)
            return new_iter

    def _move_iter_down_level(self, treeview, treeiter, parent_iter,
                              relative_position):
        """Move the specified iter down one level."""
        model = treeview.get_model()
        row_data = model[treeiter][:]
        if model.iter_has_child(parent_iter):
            if relative_position < 0:
                n_children = model.iter_n_children(parent_iter)
                sibling = model.iter_nth_child(parent_iter, n_children - 1)
                new_iter = model.insert_after(parent_iter, sibling, row_data)
            else:
                sibling = model.iter_nth_child(parent_iter, 0)
                new_iter = model.insert_before(parent_iter, sibling, row_data)
        else:
            new_iter = model.insert(parent_iter, 0, row_data)

        # Install/Uninstall items from directories.
        filename = row_data[MenuEditor.COL_FILENAME]
        self.xdg_menu_install(filename, parent_iter)
        self.xdg_menu_uninstall(model, treeiter, filename)

        model.remove(treeiter)
        treeview.expand_row(model[parent_iter].path, False)
        path = model.get_path(new_iter)
        treeview.set_cursor(path)
        return new_iter

    def _sort_iter(self, widget):
        """Alphabetical sort of items in the current directory."""

        # Get the current selected row
        model, sel_iter = self._get_selected_iter()
        if sel_iter:

            # Move to the parent iter - if there is no parent, it must be the
            # top level, which is ignored
            item_names = []
            _, parent_iter = self.get_parent(model, sel_iter)
            if parent_iter:

                # Deteriming list of item names
                for i in range(model.iter_n_children(parent_iter)):
                    child_iter = model.iter_nth_child(parent_iter, i)
                    item_names.append(model[child_iter][MenuEditor.COL_NAME])

                # Applying unstable (?) case-insensitive alphabetical sort
                item_names = sorted(item_names, key=str.lower)

                for i in range(len(item_names)):
                    child_iter = model.iter_nth_child(parent_iter, i)

                    # Ignore if item is already sorted or at least has an
                    # identical title to that expected
                    if item_names[i] != model[child_iter][MenuEditor.COL_NAME]:

                        # Locating desired item in the remaining unsorted items
                        for r in range(i, len(item_names)):
                            search_iter = model.iter_nth_child(parent_iter, r)
                            if item_names[i] == model[search_iter][MenuEditor.COL_NAME]:
                                break

                        # Moving the found item into place
                        model.move_before(search_iter, child_iter)

                # Committing changes
                self.update_menus()

            self.scroll_to_selection()

    def scroll_to_selection(self):
        model, sel_iter = self._get_selected_iter()
        self._treeview.scroll_to_cell(model.get_path(sel_iter), None,
                                      False, 0.0, 0.0)

    def set_search_entry(self, entry):
        self._treeview.set_search_entry(entry)

    def reset_cursor(self):
        self._treeview.set_cursor(Gtk.TreePath.new_from_string("1"))
        self._treeview.set_cursor(Gtk.TreePath.new_from_string("0"))
