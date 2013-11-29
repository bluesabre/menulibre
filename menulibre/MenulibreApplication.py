#!/usr/bin/python3
import locale
from locale import gettext as _
locale.textdomain('menulibre')

from gi.repository import Gtk, Gio, GLib, GObject, Pango

import sys
import os

import MenuEditor
import MenulibreXdg
from enums import Views, MenuItemTypes

session = os.getenv("DESKTOP_SESSION")

def set_entry_text(widget, text):
    if text is None:
        text = ""
    widget.set_text(text)
    
def set_toggle_active(widget, active):
    if active is None:
        active = False
    widget.set_active(active)

class MenulibreWindow(Gtk.ApplicationWindow):
    ui_file = 'data/ui/MenulibreWindow.glade'
    
    __gsignals__ = {
        'about' : (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, 
                    (GObject.TYPE_BOOLEAN,)),
        'help' : (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, 
                    (GObject.TYPE_BOOLEAN,)),
        'quit' : (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, 
                    (GObject.TYPE_BOOLEAN,))
        }
    
    def __init__(self, app):
        # Initialize the GtkBuilder to get our widgets from Glade.
        builder = Gtk.Builder()
        builder.add_from_file(self.ui_file)
        
        # Glade is unable to create a GtkApplication, so we have to reparent
        # the window contents to our new window. Here we get the contents.
        window = builder.get_object('menulibre_window')
        window_title = window.get_title()
        window_icon = window.get_icon_name()
        window_contents = window.get_children()[0]
        size_request = window.get_size_request()
        
        # Initialize the GtkApplicationWindow.
        Gtk.Window.__init__(self, title=window_title, application=app)
        self.set_wmclass(_("MenuLibre"), _("MenuLibre"))
        self.set_title(window_title)
        self.set_icon_name(window_icon)
        self.set_size_request(size_request[0], size_request[1])
        window_contents.reparent(self)
        
        # Configure Global Menu and AppMenu
        self.app_menu_button = None
        if session not in ['gnome', 'ubuntu', 'ubuntu-2d']:
            # Create the AppMenu button on the rightside of the toolbar
            self.app_menu_button = Gtk.MenuButton()
            self.app_menu_button.set_size_request(32,32)
            #self.app_menu_button.set_relief(Gtk.ReliefStyle.NONE)
            
            # Use the classic "cog" image for the button.
            image = Gtk.Image.new_from_icon_name("emblem-system-symbolic", 
                                                 Gtk.IconSize.MENU)
            self.app_menu_button.set_image(image)
            self.app_menu_button.show()
            
            # Pack the AppMenu button.
            placeholder = builder.get_object('app_menu_holder')
            placeholder.add(self.app_menu_button)
            
        builder.get_object('menubar').set_visible(session in ['ubuntu', 
                                                              'ubuntu-2d'])
        
        self.actions = {}
        
        # Add Launcher action and related widgets
        action = Gtk.Action(_('add_launcher'), _('_Add Launcher...'), 
                            _('Add Launcher...'),
                            Gtk.STOCK_NEW)
        action.connect('activate', self.on_add_launcher_cb)
        self.actions['add_launcher'] = action
        #for widget_name in ['menubar_new_launcher', 'toolbar_new']:
        for widget_name in ['menubar_new_launcher']:
            widget = builder.get_object(widget_name)
            widget.set_related_action(action)
            widget.set_use_action_appearance(True)
            
        # Save Launcher action and related widgets
        action = Gtk.Action(_('save_launcher'), _('_Save'), 
                            _('Save'),
                            Gtk.STOCK_SAVE)
        action.connect('activate', self.on_save_launcher_cb)
        self.actions['save_launcher'] = action
        #for widget_name in ['menubar_save_launcher', 'toolbar_save']:
        for widget_name in ['menubar_save_launcher']:
            widget = builder.get_object(widget_name)
            widget.set_related_action(action)
            widget.set_use_action_appearance(True)
            
        # Undo action and related widgets
        action = Gtk.Action(_('undo'), _('_Undo'), 
                            _('Undo'),
                            Gtk.STOCK_UNDO)
        action.connect('activate', self.on_undo_cb)
        self.actions['undo'] = action
        #for widget_name in ['menubar_undo', 'toolbar_undo']:
        for widget_name in ['menubar_undo']:
            widget = builder.get_object(widget_name)
            widget.set_related_action(action)
            widget.set_use_action_appearance(True)
            
        # Redo action and related widgets
        action = Gtk.Action(_('redo'), _('_Redo'), 
                            _('Redo'),
                            Gtk.STOCK_REDO)
        action.connect('activate', self.on_redo_cb)
        self.actions['redo'] = action
        #for widget_name in ['menubar_redo', 'toolbar_redo']:
        for widget_name in ['menubar_redo']:
            widget = builder.get_object(widget_name)
            widget.set_related_action(action)
            widget.set_use_action_appearance(True)
            
        # Revert action and related widgets
        action = Gtk.Action(_('revert'), _('_Revert'), 
                            _('Revert'),
                            Gtk.STOCK_REVERT_TO_SAVED)
        action.connect('activate', self.on_revert_cb)
        self.actions['revert'] = action
        #for widget_name in ['menubar_revert', 'toolbar_revert']:
        for widget_name in ['menubar_revert']:
            widget = builder.get_object(widget_name)
            widget.set_related_action(action)
            widget.set_use_action_appearance(True)
            
        # Quit action and related widgets
        action = Gtk.Action(_('quit'), _('_Quit'), 
                            _('Quit'),
                            Gtk.STOCK_QUIT)
        action.connect('activate', self.on_quit_cb)
        self.actions['quit'] = action
        for widget_name in ['menubar_quit']:
            widget = builder.get_object(widget_name)
            widget.set_related_action(action)
            widget.set_use_action_appearance(True)
            
        # Help action and related widgets
        action = Gtk.Action(_('help'), _('_Contents'), 
                            _('Help'),
                            Gtk.STOCK_HELP)
        action.connect('activate', self.on_help_cb)
        self.actions['help'] = action
        for widget_name in ['menubar_help']:
            widget = builder.get_object(widget_name)
            widget.set_related_action(action)
            widget.set_use_action_appearance(True)
            
        # About action and related widgets
        action = Gtk.Action(_('about'), _('_About'), 
                            _('About'),
                            Gtk.STOCK_ABOUT)
        action.connect('activate', self.on_about_cb)
        self.actions['about'] = action
        for widget_name in ['menubar_about']:
            widget = builder.get_object(widget_name)
            widget.set_related_action(action)
            widget.set_use_action_appearance(True)
            
        self.delete_button = builder.get_object('toolbar_delete')
                                                              
        self.view_container = builder.get_object('menulibre_window_container')
        
        self.treestore = MenuEditor.get_treestore()

                                                              
        self.set_view(Views.AUTO)
        

        
    def on_settings_group_changed(self, widget, user_data=None):
        if widget.get_active():
            self.settings_notebook.set_current_page(user_data)
        
    def on_treeview_cursor_changed(self, widget, selection):
        sel = widget.get_selection()
        if sel:
            treestore, treeiter = sel.get_selected()
            item_type = treestore[treeiter][2]
            if item_type == MenuItemTypes.SEPARATOR:
                self.editor_container.get_children()[0].hide()
                self.set_editor_name(_("Separator"))
                self.set_editor_comment("")
                self.set_editor_filename(None)
            else:
                self.editor_container.get_children()[0].show()
                
                displayed_name = treestore[treeiter][0]
                comment = treestore[treeiter][1]
                filename = treestore[treeiter][5]
                self.set_editor_image(treestore[treeiter][4])
                self.set_editor_name(displayed_name)
                self.set_editor_comment(comment)
                self.set_editor_filename(filename)
                
                if item_type == MenuItemTypes.APPLICATION:
                    self.editor_container.get_children()[0].show_all()
                    entry = MenulibreXdg.MenulibreDesktopEntry(filename)
                    self.set_editor_exec(entry['Exec'])
                    self.set_editor_path(entry['Path'])
                    self.set_editor_terminal(entry['Terminal'])
                    self.set_editor_notify(entry['StartupNotify'])
                    self.set_editor_nodisplay(entry['NoDisplay'])
                    self.set_editor_genericname(entry['GenericName'])
                    self.set_editor_tryexec(entry['TryExec'])
                    self.set_editor_onlyshowin(entry['OnlyShowIn'])
                    self.set_editor_notshowin(entry['NotShowIn'])
                    self.set_editor_mimetypes(entry['Mimetype'])
                    self.set_editor_keywords(entry['Keywords'])
                    self.set_editor_startupwmclass(entry['StartupWMClass'])
                else:
                    for widget in self.directory_hide_widgets:
                        widget.hide()
            
    def icon_name_func(self, col, renderer, treestore, treeiter, user_data):
        renderer.set_property("gicon", treestore[treeiter][3])
        pass
            
    def set_editor_image(self, gicon):
        if gicon:
            self.editor_image.set_from_gicon(gicon, self.editor_image.get_preferred_height()[0])
        else:
            self.editor_image.set_from_icon_name("application-default-icon", 48)
        
    def set_editor_name(self, text):
        if text is None:
            text = ""
        self.editor_name.set_label("<big><b>%s</b></big>" % text)
        self.editor_name.set_tooltip_markup(_("%s <i>(Click to modify.)</i>") % text)
        
    def set_editor_comment(self, text):
        if text is None:
            text = ""
        self.editor_comment.set_label(text)
        self.editor_comment.set_tooltip_markup(_("%s <i>(Click to modify.)</i>") % text)
        
    def set_editor_filename(self, filename):
        # Since the filename has changed, check if it is now writable...
        if filename is None or os.access(filename, os.W_OK):
            self.delete_button.set_sensitive(True)
            self.delete_button.set_tooltip_text("")
        else:
            self.delete_button.set_sensitive(False)
            self.delete_button.set_tooltip_text(_("You do not have permission to delete this file."))
            
        if filename is None:
            filename = ""
            
        self.editor_filename.set_label("<small><i>%s</i></small>" % filename)
        self.editor_filename.set_tooltip_text(filename)
    
    def set_editor_exec(self, text):
        set_entry_text(self.editor_exec, text)
        
    def set_editor_path(self, text):
        set_entry_text(self.editor_path, text)
        
    def set_editor_terminal(self, boolean):
        set_toggle_active(self.editor_terminal, boolean)
        
    def set_editor_notify(self, boolean):
        set_toggle_active(self.editor_notify, boolean)
        
    def set_editor_nodisplay(self, boolean):
        set_toggle_active(self.editor_nodisplay, boolean)
        
    def set_editor_genericname(self, text):
        set_entry_text(self.editor_genericname, text)
        
    def set_editor_tryexec(self, text):
        set_entry_text(self.editor_tryexec, text)
        
    def set_editor_onlyshowin(self, text):
        set_entry_text(self.editor_onlyshowin, text)
        
    def set_editor_notshowin(self, text):
        set_entry_text(self.editor_notshowin, text)
        
    def set_editor_mimetypes(self, text):
        set_entry_text(self.editor_mimetypes, text)
        
    def set_editor_keywords(self, text):
        set_entry_text(self.editor_keywords, text)
        
    def set_editor_startupwmclass(self, text):
        set_entry_text(self.editor_startupwmclass, text)
        
    def set_view(self, view_mode):
        if not view_mode:
            if session in ['gnome', 'ubuntu', 'ubuntu-2d']:
                view_mode = Views.MODERN
            else:
                view_mode = Views.CLASSIC
        builder = Gtk.Builder()
        builder.add_from_file(self.ui_file)
        try:
            self.view_container.get_children()[0].destroy()
        except:
            pass
        self.view_container.add( builder.get_object(view_mode) )
        self.editor_container = builder.get_object(view_mode+"_container")
        self.editor_container.add( builder.get_object('application_editor') )
        self.editor_image = builder.get_object('application_editor_image')
        self.editor_name = builder.get_object('application_editor_name')
        self.editor_comment = builder.get_object('application_editor_comment')
        self.editor_filename = builder.get_object('application_editor_filename')
        self.editor_exec = builder.get_object('application_editor_exec')
        self.editor_path = builder.get_object('application_editor_path')
        self.editor_terminal = builder.get_object('application_editor_terminal')
        self.editor_notify = builder.get_object('application_editor_notify')
        self.editor_nodisplay = builder.get_object('application_editor_nodisplay')
        self.editor_genericname = builder.get_object('application_editor_genericname')
        self.editor_tryexec = builder.get_object('application_editor_tryexec')
        self.editor_onlyshowin = builder.get_object('application_editor_onlyshowin')
        self.editor_notshowin = builder.get_object('application_editor_notshowin')
        self.editor_mimetypes = builder.get_object('application_editor_mimetypes')
        self.editor_keywords = builder.get_object('application_editor_keywords')
        self.editor_startupwmclass = builder.get_object('application_editor_startupwmclass')
        
        self.view_container.show_all()
        
        self.settings_notebook = builder.get_object('settings_notebook')
        
        buttons = ['categories_button', 'quicklists_button', 'advanced_button']
        for i in range(len(buttons)):
            button = builder.get_object(buttons[i])
            button.connect("clicked", self.on_settings_group_changed, i)
            button.activate()
            
        self.directory_hide_widgets = []
        for widget_name in ['details_frame', 'settings_frame', 'terminal_label', 'application_editor_terminal', 'notify_label', 'application_editor_notify']:
            self.directory_hide_widgets.append(builder.get_object(widget_name))
        
        if view_mode == Views.CLASSIC:
            treeview = builder.get_object('treeview1')
            
            col = Gtk.TreeViewColumn("Item")
            col_cell_text = Gtk.CellRendererText()
            col_cell_text.set_property("ellipsize", Pango.EllipsizeMode.END)
            col_cell_img = Gtk.CellRendererPixbuf()
            col_cell_img.set_property("stock-size", Gtk.IconSize.LARGE_TOOLBAR)
            col.pack_start(col_cell_img, False)
            col.pack_start(col_cell_text, True)
            col.add_attribute(col_cell_text, "markup", 0)
            col.set_cell_data_func(col_cell_img, self.icon_name_func, None)
            treeview.set_tooltip_column(1)

            treeview.append_column(col)
            treeview.set_model(self.treestore)
            
            treeview.connect("cursor-changed", self.on_treeview_cursor_changed, None)
            
            treeview.show_all()
            
        if view_mode == Views.MODERN:
            iconview = builder.get_object('iconview1')
            
            iconview.set_model(self.treestore)
            iconview.set_text_column(0)
            iconview.set_tooltip_column(1)
            iconview.set_pixbuf_column(4)
            
            iconview.show_all()
        
    def on_add_launcher_cb(self, widget):
        print ('add launcher')
        
    def on_save_launcher_cb(self, widget):
        print ('save launcher')
        
    def on_undo_cb(self, widget):
        print ('undo')
        
    def on_redo_cb(self, widget):
        print ('redo')
        
    def on_revert_cb(self, widget):
        print ('revert')
        
    def on_quit_cb(self, widget):
        # Emit the quit signal so the GtkApplication can handle it.
        self.emit('quit', True)
        
    def on_help_cb(self, widget):
        # Emit the help signal so the GtkApplication can handle it.
        self.emit('help', True)
        
    def on_about_cb(self, widget):
        # Emit the about signal so the GtkApplication can handle it.
        self.emit('about', True)

class Application(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self)

    def do_activate(self):
        self.win = MenulibreWindow(self)
        self.win.show_all()
        
        self.win.connect('about', self.about_cb)
        self.win.connect('help', self.help_cb)
        self.win.connect('quit', self.quit_cb)
        
        if self.win.app_menu_button:
            self.win.app_menu_button.set_menu_model(self.menu)
            self.win.app_menu_button.show_all()

    def do_startup (self):
        # start the application
        Gtk.Application.do_startup(self)
        
        if session in ['gnome', 'ubuntu', 'ubuntu-2d']: auto_view = _("Modern")
        else: auto_view = _("Classic")
        
        self.menu = Gio.Menu()
        view_menu = Gio.Menu()
        view_menu.append(_("Automatic (%s)") % auto_view, "app.switch_to_auto")
        view_menu.append(_("Modern"), "app.switch_to_modern")
        view_menu.append(_("Classic"), "app.switch_to_classic")
        self.menu.append_submenu(_("View"), view_menu)
        self.menu.append(_("Help"), "app.help")
        self.menu.append(_("About"), "app.about")
        self.menu.append(_("Quit"), "app.quit")

        if session == 'gnome':
            # Configure GMenu
            self.set_app_menu(self.menu)
            
        switch_to_auto = Gio.SimpleAction.new("switch_to_auto", None)
        switch_to_auto.connect("activate", self.switch_view, Views.AUTO)
        self.add_action(switch_to_auto)
        
        switch_to_modern = Gio.SimpleAction.new("switch_to_modern", None)
        switch_to_modern.connect("activate", self.switch_view, Views.MODERN)
        self.add_action(switch_to_modern)
        
        switch_to_classic = Gio.SimpleAction.new("switch_to_classic", None)
        switch_to_classic.connect("activate", self.switch_view, Views.CLASSIC)
        self.add_action(switch_to_classic)
        
        help_action = Gio.SimpleAction.new("help", None)
        help_action.connect("activate", self.help_cb)
        self.add_action(help_action)
        
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.about_cb)
        self.add_action(about_action)
        
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.quit_cb)
        self.add_action(quit_action)
        
    def switch_view(self, widget, data=None, view_mode=None):
        self.win.set_view(view_mode)

    def help_cb(self, widget, data=None):
        print ('help')
        pass
        
    def about_cb(self, widget, data=None):
        # Create and display the AboutDialog.
        aboutdialog = Gtk.AboutDialog()
        
        # Credits
        authors = ["Sean Davis"]
        documenters = ["Sean Davis"]
        
        # Populate the AboutDialog with all the relevant details.
        aboutdialog.set_program_name("MenuLibre")
        aboutdialog.set_logo_icon_name("alacarte")
        aboutdialog.set_copyright("Copyright \xc2\xa9 2012-2013 Sean Davis")
        aboutdialog.set_authors(authors)
        aboutdialog.set_documenters(documenters)
        aboutdialog.set_website("https://launchpad.net/menulibre")

        # Clear the window title as suggested by Gnome docs.
        aboutdialog.set_title("")

        # Connect the signal to destroy the AboutDialog when Close is clicked.
        aboutdialog.connect("response", self.about_close_cb)
        
        # Show the AboutDialog.
        aboutdialog.show()
        
    def about_close_cb(self, widget, response):
        widget.destroy()
        
    def quit_cb(self, widget, data=None):
        """Signal handler for closing the MenulibreWindow."""
        self.quit()
