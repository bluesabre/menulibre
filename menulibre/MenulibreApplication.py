#!/usr/bin/python3
import locale
import os
import re
from locale import gettext as _

from gi.repository import Gio, GObject, Gtk, Pango, Gdk, GdkPixbuf

from . import MenuEditor, MenulibreXdg, XmlMenuElementTree
from .enums import MenuItemTypes

locale.textdomain('menulibre')


def check_keypress(event, keys):
    """Compare keypress events with desired keys and return True if matched."""
    if 'Control' in keys:
        if not bool(event.get_state() & Gdk.ModifierType.CONTROL_MASK):
            return False
    if 'Alt' in keys:
        if not bool(event.get_state() & Gdk.ModifierType.MOD1_MASK):
            return False
    if 'Shift' in keys:
        if not bool(event.get_state() & Gdk.ModifierType.SHIFT_MASK):
            return False
    if 'Super' in keys:
        if not bool(event.get_state() & Gdk.ModifierType.SUPER_MASK):
            return False

    if Gdk.keyval_name(event.get_keyval()[1]).lower() not in keys:
        return False

    return True


session = os.getenv("DESKTOP_SESSION")

category_descriptions = {
    # Standard Items
    'AudioVideo': _('Multimedia'),
    'Development': _('Development'),
    'Education': _('Education'),
    'Game': _('Games'),
    'Graphics': _('Graphics'),
    'Network': _('Internet'),
    'Office': _('Office'),
    'Settings': _('Settings'),
    'System': _('System'),
    'Utility': _('Accessories'),
    'WINE': _('WINE'),
    # Desktop Environment
    'DesktopSettings': _('Desktop configuration'),
    'PersonalSettings': _('User configuration'),
    'HardwareSettings': _('Hardware configuration'),
    # GNOME Specific
    'GNOME': _('GNOME application'),
    'GTK': _('GTK+ application'),
    'X-GNOME-PersonalSettings': _('GNOME user configuration'),
    'X-GNOME-HardwareSettings': _('GNOME hardware configuration'),
    'X-GNOME-SystemSettings': _('GNOME system configuration'),
    'X-GNOME-Settings-Panel': _('GNOME system configuration'),
    # Xfce Specific
    'XFCE': _('Xfce menu item'),
    'X-XFCE': _('Xfce menu item'),
    'X-Xfce-Toplevel': _('Xfce toplevel menu item'),
    'X-XFCE-PersonalSettings': _('Xfce user configuration'),
    'X-XFCE-HardwareSettings': _('Xfce hardware configuration'),
    'X-XFCE-SettingsDialog': _('Xfce system configuration'),
    'X-XFCE-SystemSettings': _('Xfce system configuration'),
}


class MenulibreWindow(Gtk.ApplicationWindow):
    """The Menulibre application window."""
    ui_file = 'data/ui/MenulibreWindow.glade'

    __gsignals__ = {
        'about': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,
                  (GObject.TYPE_BOOLEAN,)),
        'help': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,
                 (GObject.TYPE_BOOLEAN,)),
        'quit': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE,
                 (GObject.TYPE_BOOLEAN,))
    }

    def __init__(self, app):
        """Initialize the Menulibre application."""
        # Initialize the GtkBuilder to get our widgets from Glade.
        builder = Gtk.Builder()
        builder.add_from_file(self.ui_file)

        # Steal the window contents for the GtkApplication.
        self.configure_application_window(builder, app)

        self.values = dict()

        # Set up the actions, menubar, and toolbar
        self.configure_application_actions(builder)
        self.configure_application_menubar(builder)
        self.configure_application_toolbar(builder)

        # Set up the application editor
        self.configure_application_editor(builder)

        # Set up the applicaton browser
        self.configure_application_treeview(builder)

        self.history_undo = list()
        self.history_redo = list()

    def configure_application_window(self, builder, app):
        """Glade is currently unable to create a GtkApplicationWindow.  This
        function takes the GtkWindow from the UI file and reparents the
        contents into the Menulibre GtkApplication window, preserving the
        window's properties.'"""
        # Get the GtkWindow.
        window = builder.get_object('menulibre_window')

        # Back up the window properties.
        window_title = window.get_title()
        window_icon = window.get_icon_name()
        window_contents = window.get_children()[0]
        size_request = window.get_size_request()

        # Initialize the GtkApplicationWindow.
        Gtk.Window.__init__(self, title=window_title, application=app)
        self.set_wmclass(_("MenuLibre"), _("MenuLibre"))

        # Restore the window properties.
        self.set_title(window_title)
        self.set_icon_name(window_icon)
        self.set_size_request(size_request[0], size_request[1])

        # Reparent the widgets.
        window_contents.reparent(self)

        # Connect any window-specific events.
        self.connect('key-press-event', self.on_window_keypress_event)

    def configure_application_actions(self, builder):
        """Configure the GtkActions that are used in the Menulibre
        application."""
        self.actions = {}

        # Add Launcher
        self.actions['add_launcher'] = Gtk.Action(
                                            'add_launcher',
                                            _('_Add Launcher...'),
                                            _('Add Launcher...'),
                                            Gtk.STOCK_NEW)

        # Save Launcher
        self.actions['save_launcher'] = Gtk.Action(
                                            'save_launcher',
                                            _('_Save'),
                                            _('Save'),
                                            Gtk.STOCK_SAVE)

        # Undo
        self.actions['undo'] = Gtk.Action('undo',
                                            _('_Undo'),
                                            _('Undo'),
                                            Gtk.STOCK_UNDO)

        # Redo
        self.actions['redo'] = Gtk.Action('redo',
                                            _('_Redo'),
                                            _('Redo'),
                                            Gtk.STOCK_REDO)

        # Revert
        self.actions['revert'] = Gtk.Action('revert',
                                            _('_Revert'),
                                            _('Revert'),
                                            Gtk.STOCK_REVERT_TO_SAVED)

        # Quit
        self.actions['quit'] = Gtk.Action('quit',
                                            _('_Quit'),
                                            _('Quit'),
                                            Gtk.STOCK_QUIT)

        # Help
        self.actions['help'] = Gtk.Action('help',
                                            _('_Contents'),
                                            _('Help'),
                                            Gtk.STOCK_HELP)

        # About
        self.actions['about'] = Gtk.Action('about',
                                            _('_About'),
                                            _('About'),
                                            Gtk.STOCK_ABOUT)

        # Connect the GtkAction events.
        self.actions['add_launcher'].connect('activate',
                                            self.on_add_launcher_cb)
        self.actions['save_launcher'].connect('activate',
                                            self.on_save_launcher_cb)
        self.actions['undo'].connect('activate',
                                            self.on_undo_cb)
        self.actions['redo'].connect('activate',
                                            self.on_redo_cb)
        self.actions['revert'].connect('activate',
                                            self.on_revert_cb)
        self.actions['quit'].connect('activate',
                                            self.on_quit_cb)
        self.actions['help'].connect('activate',
                                            self.on_help_cb)
        self.actions['about'].connect('activate',
                                            self.on_about_cb)

    def configure_application_menubar(self, builder):
        """Configure the application GlobalMenu (in Unity) and AppMenu."""
        self.app_menu_button = None
        placeholder = builder.get_object('app_menu_holder')

        # Show the app menu button if not using gnome or ubuntu.
        if session not in ['gnome', 'ubuntu', 'ubuntu-2d']:
            # Create the AppMenu button on the right side of the toolbar.
            self.app_menu_button = Gtk.MenuButton()
            self.app_menu_button.set_size_request(32, 32)

            # Use the classic "cog" image for the button.
            image = Gtk.Image.new_from_icon_name("emblem-system-symbolic",
                                                 Gtk.IconSize.MENU)
            self.app_menu_button.set_image(image)
            self.app_menu_button.show()

            # Pack the AppMenu button.
            placeholder.add(self.app_menu_button)
        else:
            # Hide the app menu placeholder.
            placeholder.hide()

        # Show the menubar if using a Unity session.
        if session in ['ubuntu', 'ubuntu-2d']:
            builder.get_object('menubar').set_visible(True)

            # Connect the menubar events.
            for action_name in ['add_launcher', 'save_launcher', 'undo',
                                'redo', 'revert', 'quit', 'help', 'about']:
                widget = builder.get_object("menubar_%s" % action_name)
                widget.set_related_action(self.actions[action_name])
                widget.set_use_action_appearance(True)

    def activate_action_cb(self, widget, action_name):
        """Activate the specified GtkAction."""
        self.actions[action_name].activate()

    def configure_application_toolbar(self, builder):
        """Configure the application toolbar."""
        # Configure the Add, Save, Undo, Redo, Revert widgets.
        for action_name in ['add_launcher', 'save_launcher', 'undo', 'redo',
                            'revert']:
            widget = builder.get_object("toolbar_%s" % action_name)
            widget.connect("clicked", self.activate_action_cb, action_name)

        # Configure the Delete widget.
        self.delete_button = builder.get_object('toolbar_delete')

        # Configure the search widget.
        self.search_box = builder.get_object('toolbar_search')
        self.search_box.connect('icon-press', self.on_search_cleared)

    def configure_application_treeview(self, builder):
        """Configure the menu-browsing GtkTreeView."""
        # Get the menu treestore.
        treestore = MenuEditor.get_treestore()

        # Prepare the GtkTreeView.
        self.treeview = builder.get_object('classic_view_treeview')

        # Create a new column.
        col = Gtk.TreeViewColumn(_("Search Results"))

        # Create and pack the PixbufRenderer.
        col_cell_img = Gtk.CellRendererPixbuf()
        col_cell_img.set_property("stock-size", Gtk.IconSize.LARGE_TOOLBAR)
        col.pack_start(col_cell_img, False)

        # Create and pack the TextRenderer.
        col_cell_text = Gtk.CellRendererText()
        col_cell_text.set_property("ellipsize", Pango.EllipsizeMode.END)
        col.pack_start(col_cell_text, True)

        # Set the markup property on the Text cell.
        col.add_attribute(col_cell_text, "markup", 0)

        # Set the Tooltip column.
        self.treeview.set_tooltip_column(1)

        # Add the cell data func for the pixbuf column to render icons.
        col.set_cell_data_func(col_cell_img, self.icon_name_func, None)

        # Append the column, set the model.
        self.treeview.append_column(col)
        self.treeview.set_model(treestore)

        # Configure the treeview's inline toolbar.
        self.browser_toolbar = builder.get_object('browser_toolbar')
        move_up = builder.get_object('classic_view_move_up')
        move_up.connect('clicked', self.move_iter, (self.treeview, -1))
        move_down = builder.get_object('classic_view_move_down')
        move_down.connect('clicked', self.move_iter, (self.treeview, 1))

        # Configure searching.
        self.treeview.set_search_entry(self.search_box)
        self.search_box.connect('changed', self.on_app_search_changed,
                                            self.treeview, True)

        # Configure the treeview events.
        self.treeview.connect("cursor-changed",
                                self.on_treeview_cursor_changed, None)
        self.treeview.connect("key-press-event",
                                self.on_treeview_key_press_event, None)

        # Show the treeview, grab focus.
        self.treeview.show_all()
        self.treeview.grab_focus()

        # Select the topmost item.
        self.treeview.set_cursor(Gtk.TreePath.new_from_string("0"))

    def configure_application_editor(self, builder):
        """Configure the editor frame."""
        # Set up the fancy notebook.
        self.settings_notebook = builder.get_object('settings_notebook')
        buttons = ['categories_button', 'quicklists_button', 'advanced_button']
        for i in range(len(buttons)):
            button = builder.get_object(buttons[i])
            button.connect("clicked", self.on_settings_group_changed, i)
            button.activate()

        # Store the editor.
        self.editor = builder.get_object('application_editor')

        # Keep a dictionary of the widgets for easy lookup and updates.
        # The keys are the DesktopSpec keys.
        self.widgets = {
            'Name': (  # GtkButton, GtkLabel, GtkEntry
                builder.get_object('button_Name'),
                builder.get_object('label_Name'),
                builder.get_object('entry_Name')),
            'Comment': (  # GtkButton, GtkLabel, GtkEntry
                builder.get_object('button_Comment'),
                builder.get_object('label_Comment'),
                builder.get_object('entry_Comment')),
            'Icon': (  # GtkButton, GtkImage
                builder.get_object('button_Icon'),
                builder.get_object('image_Icon')),
            'Filename': builder.get_object('label_Filename'),
            'Exec': builder.get_object('entry_Exec'),
            'Path': builder.get_object('entry_Path'),
            'Terminal': builder.get_object('switch_Terminal'),
            'StartupNotify': builder.get_object('switch_StartupNotify'),
            'NoDisplay': builder.get_object('switch_NoDisplay'),
            'GenericName': builder.get_object('entry_GenericName'),
            'TryExec': builder.get_object('entry_TryExec'),
            'OnlyShowIn': builder.get_object('entry_OnlyShowIn'),
            'NotShowIn': builder.get_object('entry_NotShowIn'),
            'MimeType': builder.get_object('entry_Mimetype'),
            'Keywords': builder.get_object('entry_Keywords'),
            'StartupWMClass': builder.get_object('entry_StartupWMClass'),
            'Hidden': builder.get_object('entry_Hidden'),
            'DBusActivatable': builder.get_object('entry_DBusActivatable')
        }

        # These widgets are hidden when the selected item is a Directory.
        self.directory_hide_widgets = []
        for widget_name in ['details_frame', 'settings_frame',
                            'terminal_label', 'switch_Terminal',
                            'notify_label', 'switch_StartupNotify']:
            self.directory_hide_widgets.append(builder.get_object(widget_name))

        # Configure the Name/Comment widgets.
        for widget_name in ['Name', 'Comment']:
            button = builder.get_object('button_%s' % widget_name)
            cancel = builder.get_object('cancel_%s' % widget_name)
            accept = builder.get_object('apply_%s' % widget_name)
            button.connect('clicked', self.on_NameComment_clicked,
                                      widget_name, builder)
            cancel.connect('clicked', self.on_NameComment_cancel,
                                      widget_name, builder)
            accept.connect('clicked', self.on_NameComment_apply,
                                      widget_name, builder)

        # Configure the Exec/Path widgets.
        for widget_name in ['Exec', 'Path']:
            button = builder.get_object('button_%s' % widget_name)
            button.connect('clicked', self.on_ExecPath_clicked,
                                      widget_name, builder)

        # Connect the Icon button.
        button = builder.get_object('button_Icon')
        button.connect("clicked", self.on_Icon_clicked, builder)

        # Preview Images, keys are the image height/width
        self.previews = {
            16: builder.get_object('preview_16'),
            32: builder.get_object('preview_32'),
            64: builder.get_object('preview_64'),
            128: builder.get_object('preview_128')
        }

        # Configure the IconSelection treeview.
        self.icon_selection_treeview = \
            builder.get_object('icon_selection_treeview')
        entry = builder.get_object('icon_selection_search')
        model = self.icon_selection_treeview.get_model()
        model_filter = model.filter_new()
        model_filter.set_visible_func(self.icon_selection_match_func, entry)
        self.icon_selection_treeview.set_model(model_filter)
        entry.connect("changed", self.on_search_changed, model_filter)

        # Configure the IconType selection.
        for widget_name in ['IconName', 'ImageFile']:
            radio = builder.get_object('radiobutton_%s' % widget_name)
            radio.connect("clicked", self.on_IconGroup_toggled,
                                     widget_name, builder)
            entry = builder.get_object('entry_%s' % widget_name)
            entry.connect("changed", self.on_IconEntry_changed, widget_name)
            button = builder.get_object('button_%s' % widget_name)
            button.connect("clicked", self.on_IconButton_clicked,
                                        widget_name, builder)

        # Categories Treeview and Inline Toolbar
        self.categories_treeview = builder.get_object('categories_treeview')
        add_button = builder.get_object('categories_add')
        add_button.connect("clicked", self.on_categories_add)
        remove_button = builder.get_object('categories_remove')
        remove_button.connect("clicked", self.on_categories_remove)
        clear_button = builder.get_object('categories_clear')
        clear_button.connect("clicked", self.on_categories_clear)

        # Actions Treeview and Inline Toolbar
        self.actions_treeview = builder.get_object('actions_treeview')
        add_button = builder.get_object('actions_add')
        add_button.connect("clicked", self.on_actions_add)
        remove_button = builder.get_object('actions_remove')
        remove_button.connect("clicked", self.on_actions_remove)
        clear_button = builder.get_object('actions_clear')
        clear_button.connect("clicked", self.on_actions_clear)

    def on_categories_add(self, widget):
        """Add a new row to the Categories TreeView."""
        #TODO: Implement fully
        self.treeview_add(self.categories_treeview, ['', ''])

    def on_categories_remove(self, widget):
        """Remove the currently selected row from the Categories TreeView."""
        #TODO: Implement fully
        self.treeview_remove(self.categories_treeview)

    def on_categories_clear(self, widget):
        """Clear all rows from the Categories TreeView."""
        #TODO: Implement fully
        self.treeview_clear(self.categories_treeview)

    def on_actions_add(self, widget):
        """Add a new row to the Actions TreeView."""
        #TODO: Implement fully
        self.treeview_add(self.actions_treeview, [False, '', '', ''])

    def on_actions_remove(self, widget):
        """Remove the currently selected row from the Actions TreeView."""
        #TODO: Implement fully
        self.treeview_remove(self.actions_treeview)

    def on_actions_clear(self, widget):
        """Clear all rows from the Actions TreeView."""
        #TODO: Implement fully
        self.treeview_clear(self.actions_treeview)

    def model_children_to_xml(self, model, model_parent=None, menu_parent=None):
        """Add child menu items to menu_parent from model_parent."""
        # For each child iter...
        for n_child in range(model.iter_n_children(model_parent)):
            treeiter = model.iter_nth_child(model_parent, n_child)

            # Extract the menu item details.
            name, comment, item_type, gicon, icon, desktop = model[treeiter][:]

            # If it's a directory...
            if item_type == MenuItemTypes.DIRECTORY:
                # Add a menu child.
                next_element = menu_parent.addMenu(name)

                # Add a layout to that menu.
                layout = next_element.addLayout()

                # Add a merge for any submenus.
                layout.addMerge("menus")

                # If there are any children nodes, append them.
                if model.iter_n_children(treeiter) != 0:
                    self.model_children_to_xml(model, treeiter, layout)

                # Add a merge for any new/unincluded menu items.
                layout.addMerge("files")

            # If it's an application...
            elif item_type == MenuItemTypes.APPLICATION:
                # Append the menu item.
                menu_parent.addFilename(os.path.basename(desktop))

            elif item_type == MenuItemTypes.SEPARATOR:
                #TODO: Add Separator functionality.
                pass

    def treeview_to_xml(self, treeview):
        """Write the current treeview to the -applications.menu file."""
        model = treeview.get_model()
        menu_name = "Xfce"
        merge_file = "/etc/xdg/xdg-xubuntu/menus/xfce-applications.menu"
        filename = "/home/sean/Desktop/test.txt"
        menu = XmlMenuElementTree.XmlMenuElementTree(menu_name, merge_file)
        root = menu.getroot()
        self.model_children_to_xml(model, menu_parent=root)
        menu.write(filename)

    def treeview_add(self, treeview, row_data):
        """Append the specified row_data to the treeview."""
        model = treeview.get_model()
        model.append(row_data)

    def treeview_remove(self, treeview):
        """Remove the selected row from the treeview."""
        model, treeiter = treeview.get_selection().get_selected()
        model.remove(treeiter)

    def treeview_clear(self, treeview):
        """Remove all items from the treeview."""
        model = treeview.get_model()
        model.clear()

    def load_icon_selection_treeview(self):
        """Load the IconSelection treeview."""
        model = self.icon_selection_treeview.get_model().get_model()
        for icon_name in self.icons_list:
            model.append([icon_name])

    def on_IconButton_clicked(self, widget, widget_name, builder):
        """Load the IconSelection dialog to choose a new icon."""
        # Icon Name
        if widget_name == 'IconName':
            dialog = builder.get_object('icon_selection_dialog')
            self.load_icon_selection_treeview()
            response = dialog.run()
            if response == Gtk.ResponseType.APPLY:
                treeview = builder.get_object('icon_selection_treeview')
                model, treeiter = treeview.get_selection().get_selected()
                icon_name = model[treeiter][0]
                entry = builder.get_object('entry_IconName')
                entry.set_text(icon_name)
            dialog.hide()

        # Image File
        else:
            buttons = [
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK
            ]
            dialog = Gtk.FileChooserDialog("Select an image",
                                            self,
                                            Gtk.FileChooserAction.OPEN,
                                            buttons)
            if dialog.run() == Gtk.ResponseType.OK:
                filename = dialog.get_filename()
                entry = builder.get_object('entry_ImageFile')
                entry.set_text(filename)
            dialog.hide()

    def on_IconEntry_changed(self, widget, widget_name):
        """Update the Icon previews when the icon text has changed."""
        text = widget.get_text()
        if widget_name == 'IconName':
            self.update_icon_preview(icon_name=text)
        else:
            self.update_icon_preview(filename=text)

    def update_icon_preview(self, icon_name='image-missing', filename=None):
        """Update the icon preview."""
        # If filename is specified...
        if filename is not None:
            # If the file exists...
            if os.path.isfile(filename):
                # Render it to a pixbuf...
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
                for size in [16, 32, 64, 128]:
                    # Scale the image...
                    scaled = pixbuf.scale_simple(size, size,
                                    GdkPixbuf.InterpType.HYPER)
                    # Then update the preview images.
                    self.previews[size].set_from_pixbuf(scaled)
                return

        # Check if the icon theme lists this icon.
        if icon_name not in self.icons_list:
            icon_name = 'image-missing'

        # Update each of the preview images with the icon.
        for size in [16, 32, 64, 128]:
            self.previews[size].set_from_icon_name(icon_name, size)

    def on_IconGroup_toggled(self, widget, group_name, builder):
        """Update the sensitivity of the icon/image widgets based on the
        selected radio group."""
        if widget.get_active():
            entry = builder.get_object('entry_%s' % group_name)
            if group_name == 'IconName':
                builder.get_object('box_IconName').set_sensitive(True)
                builder.get_object('box_ImageFile').set_sensitive(False)
                self.update_icon_preview(icon_name=entry.get_text())
            else:
                builder.get_object('box_ImageFile').set_sensitive(True)
                builder.get_object('box_IconName').set_sensitive(False)
                self.update_icon_preview(filename=entry.get_text())

    def on_Icon_clicked(self, widget, builder):
        """Show the Icon Selection dialog when the Icon button is clicked."""
        # Update the icon theme.
        self.icon_theme = Gtk.IconTheme.get_default()

        # Update the icons list.
        self.icons_list = self.icon_theme.list_icons(None)
        self.icons_list.sort()

        # Get the dialog widgets.
        dialog = builder.get_object('icon_dialog')
        dialog.set_transient_for(self)
        radio_IconName = builder.get_object('radiobutton_IconName')
        radio_ImageFile = builder.get_object('radiobutton_ImageFile')
        entry_IconName = builder.get_object('entry_IconName')
        entry_ImageFile = builder.get_object('entry_ImageFile')

        # Get the current icon name.
        icon_name = self.values['icon-name']

        # If the current icon name is actually a filename...
        if os.path.isfile(icon_name):
            # Select the Image File radio button and set its details.
            radio_ImageFile.set_active(True)
            entry_ImageFile.set_text(icon_name)
            entry_ImageFile.grab_focus()

            # Update the icon preview.
            self.update_icon_preview(filename=icon_name)

            # Clear the IconName field.
            entry_IconName.set_text("")

        # If the icon name is an icon...
        else:
            # Select the Icon Name radio button and set its details.
            radio_IconName.set_active(True)
            entry_IconName.set_text(icon_name)
            entry_IconName.grab_focus()

            # Update the icon preview.
            self.update_icon_preview(icon_name=icon_name)

            # Clear the ImageFile field.
            entry_ImageFile.set_text("")

        # Run the dialog, updating the entries as needed.
        response = dialog.run()
        if response == Gtk.ResponseType.APPLY:
            if radio_IconName.get_active():
                self.set_value('Icon', entry_IconName.get_text())
            else:
                self.set_value('Icon', entry_ImageFile.get_text())
        dialog.hide()

    def on_NameComment_clicked(self, widget, widget_name, builder):
        """Show the Name/Comment editor widgets when the button is clicked."""
        entry = builder.get_object('entry_%s' % widget_name)
        box = builder.get_object('box_%s' % widget_name)
        self.values[widget_name] = entry.get_text()
        widget.hide()
        box.show()

    def on_NameComment_cancel(self, widget, widget_name, builder):
        """Hide the Name/Comment editor widgets when canceled."""
        box = builder.get_object('box_%s' % widget_name)
        button = builder.get_object('button_%s' % widget_name)
        box.hide()
        button.show()
        self.set_value(widget_name, self.values[widget_name])

    def on_NameComment_apply(self, widget, widget_name, builder):
        """Update the Name/Comment fields when the values are to be updated."""
        entry = builder.get_object('entry_%s' % widget_name)
        box = builder.get_object('box_%s' % widget_name)
        button = builder.get_object('button_%s' % widget_name)
        box.hide()
        button.show()
        self.set_value(widget_name, entry.get_text())

    def on_ExecPath_clicked(self, widget, widget_name, builder):
        """Show the file selection dialog when Exec/Path Browse is clicked."""
        entry = builder.get_object('entry_%s' % widget_name)
        buttons = [
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        ]
        if widget_name == 'Path':
            dialog = Gtk.FileChooserDialog(_("Select a working directory..."),
                                           self,
                                           Gtk.FileChooserAction.SELECT_FOLDER,
                                           buttons)
        else:
            dialog = Gtk.FileChooserDialog(_("Select an executable..."),
                                           self,
                                           Gtk.FileChooserAction.OPEN,
                                           buttons)
        result = dialog.run()
        dialog.hide()
        if result == Gtk.ResponseType.OK:
            entry.set_text(dialog.get_filename())

    def on_window_keypress_event(self, widget, event, user_data=None):
        """Handle window keypress events."""
        # Ctrl-F (Find)
        if check_keypress(event, ['Control', 'f']):
            self.search_box.grab_focus()
            return True
        # Ctrl-S (Save)
        if check_keypress(event, ['Control', 's']):
            #TODO: Implement Save
            pass
        return False

    def on_settings_group_changed(self, widget, page_number):
        """Handle setting the Notebook page with Radio Buttons."""
        if widget.get_active():
            self.settings_notebook.set_current_page(page_number)

    def get_treeview_selected_expanded(self, treeview):
        """Return True if the selected row is currently expanded."""
        sel = treeview.get_selection()
        model, treeiter = sel.get_selected()
        row = model[treeiter]
        return treeview.row_expanded(row.path)

    def set_treeview_selected_expanded(self, treeview, expanded=True):
        """Set the expansion (True or False) of the selected row."""
        sel = treeview.get_selection()
        model, treeiter = sel.get_selected()
        row = model[treeiter]
        if expanded:
            treeview.expand_row(row.path, False)
        else:
            treeview.collapse_row(row.path)

    def toggle_treeview_selected_expanded(self, treeview):
        """Toggle the expansion of the selected row."""
        expanded = self.get_treeview_selected_expanded(treeview)
        self.set_treeview_selected_expanded(treeview, not expanded)

    def on_treeview_key_press_event(self, widget, event, user_data=None):
        """Handle treeview keypress events."""
        # Right expands the selected row.
        if check_keypress(event, ['right']):
            self.set_treeview_selected_expanded(widget, True)
            return True
        # Left collapses the selected row.
        elif check_keypress(event, ['left']):
            self.set_treeview_selected_expanded(widget, False)
            return True
        # Spacebar toggles the expansion of the selected row.
        elif check_keypress(event, ['space']):
            self.toggle_treeview_selected_expanded(widget)
            return True
        # Enter activates the selected row.
        elif check_keypress(event, ['return']):
            #TODO: Implement Activation.
            return True
        return False

    def on_treeview_cursor_changed(self, widget, selection):
        """Update the editor frame when the selected row is changed."""
        # Check if the selection is valid.
        sel = widget.get_selection()
        if sel:
            treestore, treeiter = sel.get_selected()
            if not treestore:
                return
            if not treeiter:
                return

            # Clear the individual entries.
            for key in ['Exec', 'Path', 'Terminal', 'StartupNotify',
                        'NoDisplay', 'GenericName', 'TryExec',
                        'OnlyShowIn', 'NotShowIn', 'MimeType',
                        'Keywords', 'StartupWMClass', 'Categories']:
                        self.set_value(key, None)

            # Clear the Actions and Icon.
            self.set_editor_actions(None)
            self.set_editor_image(None)

            item_type = treestore[treeiter][2]

            # If the selected row is a separator, hide the editor.
            if item_type == MenuItemTypes.SEPARATOR:
                self.editor.hide()
                self.set_value('Name', _("Separator"))
                self.set_value('Comment', "")
                self.set_value('Filename', None)
                self.set_value('Type', 'Separator')

            # Otherwise, show the editor and update the values.
            else:
                self.editor.show()

                displayed_name = treestore[treeiter][0]
                comment = treestore[treeiter][1]
                filename = treestore[treeiter][5]
                self.set_editor_image(treestore[treeiter][3],
                                      treestore[treeiter][4])
                self.set_value('Name', displayed_name)
                self.set_value('Comment', comment)
                self.set_value('Filename', filename)

                if item_type == MenuItemTypes.APPLICATION:
                    self.editor.show_all()
                    entry = MenulibreXdg.MenulibreDesktopEntry(filename)
                    for key in ['Exec', 'Path', 'Terminal', 'StartupNotify',
                                'NoDisplay', 'GenericName', 'TryExec',
                                'OnlyShowIn', 'NotShowIn', 'MimeType',
                                'Keywords', 'StartupWMClass', 'Categories']:
                        self.set_value(key, entry[key])
                    self.set_editor_actions(entry.get_actions())
                    self.set_value('Type', 'Application')
                else:
                    self.set_value('Type', 'Directory')
                    for widget in self.directory_hide_widgets:
                        widget.hide()

    def icon_name_func(self, col, renderer, treestore, treeiter, user_data):
        """CellRenderer function to set the gicon for each row."""
        renderer.set_property("gicon", treestore[treeiter][3])
        pass

    def treeview_match(self, model, treeiter, query):
        """Match subfunction for filtering search results."""
        name, comment, item_type, icon, pixbuf, desktop = model[treeiter][:]

        # Hide separators in the search results.
        if item_type == MenuItemTypes.SEPARATOR:
            return False

        # Convert None to blank.
        if not name:
            name = ""
        if not comment:
            comment = ""

        # Expand all the rows.
        self.treeview.expand_all()

        # Match against the name.
        if query in name.lower():
            return True

        # Match against the comment.
        if query in comment.lower():
            return True

        # Show the directory if any child items match.
        if item_type == MenuItemTypes.DIRECTORY:
            return self.treeview_match_directory(query, model, treeiter)

        # No matches, return False.
        return False

    def treeview_match_directory(self, query, model, treeiter):
        """Match subfunction for matching directory children."""
        for child_i in range(model.iter_n_children(treeiter)):
            child = model.iter_nth_child(treeiter, child_i)
            if self.treeview_match(model, child, query):
                return True

        return False

    def treeview_match_func(self, model, treeiter, data=None):
        """Match function for filtering search results."""
        # Make the query case-insensitive.
        query = str(self.search_box.get_text().lower())

        if query == "":
            return True

        return self.treeview_match(model, treeiter, query)

    def icon_selection_match_func(self, model, treeiter, entry):
        """Match function for filtering IconSelection search results."""
        # Make the query case-insensitive.
        query = str(entry.get_text().lower())

        if query == "":
            return True

        return query in model[treeiter][0].lower()

    def on_app_search_changed(self, widget, treeview, expand=False):
        """Update search results when query text is modified."""
        query = widget.get_text()
        model = treeview.get_model()

        # If blank query...
        if len(query) == 0:
            # Remove the clear button.
            widget.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY,
                                            None)

            # If the model is a filter, we want to remove the filter.
            if isinstance(model, Gtk.TreeModelFilter):
                # Get the model and iter.
                f_model, f_iter = treeview.get_selection().get_selected()

                # Restore the original model.
                model = model.get_model()
                treeview.set_model(model)
                treeview.expand_all()

                # Try to get the row that was selected previously.
                if (f_model is not None) and (f_iter is not None):
                    row_data = f_model[f_iter][:]
                    selected_iter = self.get_iter_by_data(row_data, model,
                                                            parent=None)
                # If that fails, just select the first iter.
                else:
                    selected_iter = model.get_iter_first()

                # Set the cursor.
                path = model.get_path(selected_iter)
                treeview.set_cursor(path)

            # Hide the headers and enable the inline toolbar.
            treeview.set_headers_visible(False)
            self.browser_toolbar.set_sensitive(True)

        # If the entry has a query...
        else:
            # Show the clear button.
            widget.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY,
                                            'edit-clear-symbolic')

            # If specified, expand the treeview.
            if expand:
                self.treeview.expand_all()

            # If the model is not a filter, make it so.
            if not isinstance(model, Gtk.TreeModelFilter):
                model = model.filter_new()
                treeview.set_model(model)
                model.set_visible_func(self.treeview_match_func)

            # Show the "Search Results" header and disable the inline toolbar.
            treeview.set_headers_visible(True)
            self.browser_toolbar.set_sensitive(False)

            # Rerun the filter.
            model.refilter()

    def on_search_changed(self, widget, treefilter, expand=False):
        """Generic search entry changed callback function."""
        query = widget.get_text()

        if len(query) == 0:
            widget.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY,
                                            None)

        else:
            widget.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY,
                                            'edit-clear-symbolic')
            if expand:
                self.treeview.expand_all()

        treefilter.refilter()

    def on_search_cleared(self, widget, event, user_data=None):
        """Generic search cleared callback function."""
        widget.set_text("")

    def set_editor_image(self, gicon, icon_name=None):
        """Set the editor Icon button image."""
        button, image = self.widgets['Icon']

        # If the Gio.Icon is defined, use it.
        if gicon is not None:
            image.set_from_gicon(
                gicon, image.get_preferred_height()[0])

        # Otherwise, use the icon-name.
        else:
            if icon_name is not None:
                # Load the Icon Theme.
                icon_theme = Gtk.IconTheme.get_default()

                # If the Icon Theme has the icon, set the image to that icon.
                if icon_theme.has_icon(icon_name):
                    image.set_from_icon_name(icon_name, 48)

                # If the icon name is actually a file, render it to the Image.
                elif os.path.isfile(icon_name):
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon_name)
                    size = image.get_preferred_height()[1]
                    scaled = pixbuf.scale_simple(size, size,
                                                    GdkPixbuf.InterpType.HYPER)
                    image.set_from_pixbuf(scaled)

                # Fallback icon.
                else:
                    image.set_from_icon_name("application-default-icon", 48)
            else:
                image.set_from_icon_name("application-default-icon", 48)
        self.values['icon-name'] = icon_name

    def set_editor_filename(self, filename):
        """Set the editor filename."""
        # Since the filename has changed, check if it is now writable...
        if filename is None or os.access(filename, os.W_OK):
            self.delete_button.set_sensitive(True)
            self.delete_button.set_tooltip_text("")
        else:
            self.delete_button.set_sensitive(False)
            self.delete_button.set_tooltip_text(
                _("You do not have permission to delete this file."))

        # If the filename is None, make it blank.
        if filename is None:
            filename = ""

        # Get the filename widget.
        widget = self.widgets['Filename']

        # Set the label and tooltip.
        widget.set_label("<small><i>%s</i></small>" % filename)
        widget.set_tooltip_text(filename)

        # Store the filename value.
        self.values['filename'] = filename

    def get_editor_categories(self):
        """Get the editor categories.

        Return the categories as a semicolon-delimited string."""
        model = self.categories_treeview.get_model()
        categories = ""
        for row in model:
            categories = "%s%s;" % (categories, row[0])
        return categories

    def set_editor_categories(self, entries_string):
        """Populate the Categories treeview with the Categories string."""
        if not entries_string:
            entries_string = ""

        # Split the entries into a list.
        entries = entries_string.split(';')
        entries.sort()

        # Clear the model.
        model = self.categories_treeview.get_model()
        model.clear()

        # Cleanup the entry text and generate a description.
        for entry in entries:
            entry = entry.strip()
            if len(entry) > 0:
                try:
                    description = category_descriptions[entry]
                except KeyError:
                    # Regex <3 Split CamelCase into separate words.
                    description = re.sub('(?!^)([A-Z]+)', r' \1', entry)
                model.append([entry, description])

    def get_editor_actions(self):
        """Return the .desktop formatted actions."""
        # Get the model.
        model = self.actions_treeview.get_model()

        # Start the output string.
        actions = "\nActions="
        groups = "\n"

        # Return None if there are no actions.
        if len(model) == 0:
            return None

        # For each row...
        for row in model:
            # Extract the details.
            show, name, displayed, executable = row[:]

            # Append it to the actions list if it is selected to be shown.
            if show:
                actions = "%s%s;" % (actions, name)

            # Populate the group text.
            group = "[Desktop Action %s]\n" \
                    "Name=%s\n" \
                    "Exec=%s\n" \
                    "OnlyShowIn=Unity\n" % (name, displayed, executable)

            # Append the new group text to the groups string.
            groups = "%s\n%s" % (groups, group)

        # Return the .desktop formatted actions.
        return actions + groups

    def set_editor_actions(self, action_groups):
        """Set the editor Actions from the list action_groups."""
        model = self.actions_treeview.get_model()
        model.clear()
        if not action_groups:
            return
        for name, displayed, command, show in action_groups:
            model.append([show, name, displayed, command])

    def set_value(self, key, value):
        """Set the DesktopSpec key, value pair in the editor."""
        # Name and Comment must formatted correctly for their buttons.
        if key in ['Name', 'Comment']:
            if not value:
                value = ""
            button, label, entry = self.widgets[key]
            if key == 'Name':
                markup = "<big><b>%s</b></big>" % (value)
            else:
                markup = "%s" % (value)
            tooltip = "%s <i>(Click to modify.)</i>" % (value)

            button.set_tooltip_markup(tooltip)
            entry.set_text(value)
            label.set_label(markup)

        # Filename, Categories, and Icon have their own functions.
        elif key == 'Filename':
            self.set_editor_filename(value)
        elif key == 'Categories':
            self.set_editor_categories(value)
        elif key == 'Icon':
            self.set_editor_image(gicon=None, icon_name=value)

        # Type is just stored.
        elif key == 'Type':
            self.values['Type'] = value

        # Everything else is set by its widget type.
        else:
            widget = self.widgets[key]
            # GtkButton
            if isinstance(widget, Gtk.Button):
                if not value:
                    value = ""
                widget.set_label(value)
            # GtkLabel
            elif isinstance(widget, Gtk.Label):
                if not value:
                    value = ""
                widget.set_label(value)
            # GtkEntry
            elif isinstance(widget, Gtk.Entry):
                if not value:
                    value = ""
                widget.set_text(value)
            # GtkSwitch
            elif isinstance(widget, Gtk.Switch):
                if not value:
                    value = False
                widget.set_active(value)
            else:
                #TODO: add logger.debug here.
                print(("Unknown widget: %s" % key))

    def get_value(self, key):
        """Return the value stored for the specified key."""
        if key in ['Name', 'Comment']:
            button, label, entry = self.widgets[key]
            return entry.get_text()
        elif key == 'Icon':
            return self.values['icon-name']
        elif key == 'Type':
            return self.values[key]
        elif key == 'Categories':
            return self.get_editor_categories()
        elif key == 'Filename':
            return self.values['filename']
        else:
            widget = self.widgets[key]
            if isinstance(widget, Gtk.Button):
                return widget.get_label()
            elif isinstance(widget, Gtk.Label):
                return widget.get_label()
            elif isinstance(widget, Gtk.Entry):
                return widget.get_text()
            elif isinstance(widget, Gtk.Switch):
                return widget.get_active()
            else:
                return None

    def move_iter(self, widget, user_data):
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
        self.treeview_to_xml(treeview)

        # Get the current selected row
        #model = treeview.get_model().get_model()
        sel = treeview.get_selection().get_selected()
        if sel:
            model, selected_iter = sel

            #selected_iter = sel[1]
            selected_type = model[selected_iter][2]
            print (selected_type)
            #model = model.get_model()

            # Move the row up if relative_position < 0
            if relative_position < 0:
                sibling = model.iter_previous(selected_iter)
            else:
                sibling = model.iter_next(selected_iter)

            if sibling:
                path = model.get_path(sibling)
                # If the selected row is not a directory and
                # the neighboring row is expanded, prepend/append to it.
                if selected_type != MenuItemTypes.DIRECTORY and \
                        treeview.row_expanded(path):
                    self.move_iter_down_level(treeview, selected_iter,
                                        sibling, relative_position)
                else:
                    # Otherwise, just move down/up
                    if relative_position < 0:
                        model.move_before(selected_iter, sibling)
                        #self.move_iter_before(model, selected_iter, sibling)
                    else:
                        model.move_after(selected_iter, sibling)
                        #self.move_iter_after(model, selected_iter, sibling)
            else:
                # If there is no neighboring row, move up a level.
                self.move_iter_up_level(treeview, selected_iter,
                                      relative_position)

    def get_iter_by_data(self, row_data, model, parent=None):
        """Search the TreeModel for a row matching row_data.

        Return the TreeIter found or None if none found."""
        for n_child in range(model.iter_n_children(parent)):
            treeiter = model.iter_nth_child(parent, n_child)
            if model[treeiter][:] == row_data:
                return treeiter
            if model.iter_n_children(treeiter) != 0:
                value = self.get_iter_by_data(row_data, model, treeiter)
                if value is not None:
                    return value
        return None

    def move_iter_up_level(self, treeview, treeiter, relative_position):
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
            model.remove(treeiter)
            path = model.get_path(new_iter)
            treeview.set_cursor(path)

    def move_iter_down_level(self, treeview, treeiter, parent_iter,
                             relative_position):
        """Move the specified iter down one level."""
        model = treeview.get_model()
        row_data = model[treeiter][:]
        if relative_position < 0:
            n_children = model.iter_n_children(parent_iter)
            sibling = model.iter_nth_child(parent_iter, n_children - 1)
            new_iter = model.insert_after(parent_iter, sibling, row_data)
        else:
            sibling = model.iter_nth_child(parent_iter, 0)
            new_iter = model.insert_before(parent_iter, sibling, row_data)
        model.remove(treeiter)
        path = model.get_path(new_iter)
        treeview.set_cursor(path)

    def on_add_launcher_cb(self, widget):
        """Add Launcher callback function."""
        #TODO: Implement AddLauncher
        print ('add launcher')

    def get_save_filename(self):
        """Determime the filename to be used to store the launcher.

        Return the filename to be used."""
        # Get the filename that is currently set, item type, and name.
        filename = self.get_value('Filename')
        item_type = self.get_value('Type')
        name = self.get_value('Name')

        # Check if the filename is writeable. If not, generate a new one.
        if filename is None or not os.access(filename, os.W_OK):
            # No filename, make one from the launcher name.
            if filename is None:
                basename = name.lower().replace(' ', '-')

            # Use the current filename as a base.
            else:
                basename = os.path.basename(filename)

            # Split the basename into filename and extension.
            name, ext = os.path.splitext(basename)

            # Get the save location of the launcher base on type.
            if item_type == 'Application':
                path = "%s/.local/share/applications/" % os.getenv("HOME")
            elif item_type == 'Directory':
                path = "%s/.local/share/desktop-directories/" % \
                        os.getenv("HOME")

            # Create the new base filename.
            filename = "%s%s" % (path, basename)

            # Append numbers as necessary to make the filename unique.
            count = 1
            while os.path.exists(filename):
                filename = "%s%s%i%s" % (path, name, count, ext)
                count += 1

        return filename

    def save_launcher(self):
        """Save the current launcher details."""
        # Get the filename to be used.
        filename = self.get_save_filename()

        # Open the file and start writing.
        with open(filename, 'w') as output:
            output.write('[Desktop Entry]\n')
            output.write('Version=1.0\n')
            for prop in ['Type', 'Name', 'GenericName', 'Comment', 'Icon',
                         'TryExec', 'Exec', 'Path', 'NoDisplay', 'Hidden',
                         'OnlyShowIn', 'NotShowIn', 'Categories', 'Keywords',
                         'MimeType', 'StartupWMClass', 'StartupNotify',
                         'Terminal', 'DBusActivatable']:
                value = self.get_value(prop)
                if value in [True, False]:
                    value = str(value).lower()
                if value:
                    output.write('%s=%s\n' % (prop, value))
            actions = self.get_editor_actions()
            if actions:
                output.write(actions)

        # Set the editor to the new filename.
        self.set_value('Filename', filename)

    def on_save_launcher_cb(self, widget):
        """Save Launcher callback function."""
        self.save_launcher()

    def on_undo_cb(self, widget):
        """Undo callback function."""
        #TODO: Implement Undo.
        print ('undo')

    def on_redo_cb(self, widget):
        """Redo callback function."""
        #TODO: Implement Redo.
        print ('redo')

    def on_revert_cb(self, widget):
        """Revert callback function."""
        #TODO: Implement Revert.
        print ('revert')

    def on_quit_cb(self, widget):
        """Quit callback function.  Send the quit signal to the parent
        GtkApplication instance."""
        self.emit('quit', True)

    def on_help_cb(self, widget):
        """Help callback function.  Send the help signal to the parent
        GtkApplication instance."""
        self.emit('help', True)

    def on_about_cb(self, widget):
        """About callback function.  Send the about signal to the parent
        GtkApplication instance."""
        self.emit('about', True)


class Application(Gtk.Application):
    """Menulibre GtkApplication"""

    def __init__(self):
        """Initialize the GtkApplication."""
        Gtk.Application.__init__(self)

    def do_activate(self):
        """Handle GtkApplication do_activate."""
        self.win = MenulibreWindow(self)
        self.win.show()

        self.win.connect('about', self.about_cb)
        self.win.connect('help', self.help_cb)
        self.win.connect('quit', self.quit_cb)

        if self.win.app_menu_button:
            self.win.app_menu_button.set_menu_model(self.menu)
            self.win.app_menu_button.show_all()

    def do_startup(self):
        """Handle GtkApplication do_startup."""
        Gtk.Application.do_startup(self)

        self.menu = Gio.Menu()
        self.menu.append(_("Help"), "app.help")
        self.menu.append(_("About"), "app.about")
        self.menu.append(_("Quit"), "app.quit")

        if session == 'gnome':
            # Configure GMenu
            self.set_app_menu(self.menu)

        help_action = Gio.SimpleAction.new("help", None)
        help_action.connect("activate", self.help_cb)
        self.add_action(help_action)

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.about_cb)
        self.add_action(about_action)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.quit_cb)
        self.add_action(quit_action)

    def help_cb(self, widget, data=None):
        """Help callback function."""
        #TODO: Implement Help.
        pass

    def about_cb(self, widget, data=None):
        """About callback function.  Display the AboutDialog."""
        # Create and display the AboutDialog.
        aboutdialog = Gtk.AboutDialog()

        # Credits
        authors = ["Sean Davis"]
        documenters = ["Sean Davis"]

        # Populate the AboutDialog with all the relevant details.
        aboutdialog.set_title(_("About MenuLibre"))
        aboutdialog.set_program_name(_("MenuLibre"))
        aboutdialog.set_logo_icon_name("menulibre")
        aboutdialog.set_copyright(_("Copyright © 2012-2014 Sean Davis"))
        aboutdialog.set_authors(authors)
        aboutdialog.set_documenters(documenters)
        aboutdialog.set_website("https://launchpad.net/menulibre")

        # Connect the signal to destroy the AboutDialog when Close is clicked.
        aboutdialog.connect("response", self.about_close_cb)

        # Show the AboutDialog.
        aboutdialog.show()

    def about_close_cb(self, widget, response):
        """Destroy the AboutDialog when it is closed."""
        widget.destroy()

    def quit_cb(self, widget, data=None):
        """Signal handler for closing the MenulibreWindow."""
        self.quit()
