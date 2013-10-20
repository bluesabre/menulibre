#!/usr/bin/python
import locale
from locale import gettext as _
locale.textdomain('menulibre')

from gi.repository import Gtk, Gio, GLib, GObject

import sys
import os

def enum(**enums):
    return type('Enum', (), enums)
    
Views = enum(AUTO=None, CLASSIC='classic_view', MODERN='modern_view')
session = os.getenv("DESKTOP_SESSION")

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
        
        # Initialize the GtkApplicationWindow.
        Gtk.Window.__init__(self, title=window_title, application=app)
        self.set_wmclass(_("MenuLibre"), _("MenuLibre"))
        self.set_title(window_title)
        self.set_icon_name(window_icon)
        window_contents.reparent(self)
        
        # Configure Global Menu and AppMenu
        self.app_menu_button = None
        if session not in ['gnome', 'ubuntu', 'ubuntu-2d']:
            # Create the AppMenu button on the rightside of the toolbar
            self.app_menu_button = Gtk.MenuButton()
            self.app_menu_button.set_relief(Gtk.ReliefStyle.NONE)
            
            # Use the classic "cog" image for the button.
            image = Gtk.Image.new_from_icon_name("document-properties", 
                                                 Gtk.IconSize.LARGE_TOOLBAR)
            self.app_menu_button.set_image(image)
            self.app_menu_button.show()
            
            # Pack the AppMenu button.
            placeholder = builder.get_object('app_menu_holder')
            placeholder.add(self.app_menu_button)
            
        #builder.get_object('menubar').set_visible(session in ['ubuntu', 
        #                                                      'ubuntu-2d'])
        
        self.actions = {}
        
        # Add Launcher action and related widgets
        action = Gtk.Action(_('add_launcher'), _('_Add Launcher...'), 
                            _('Add Launcher...'),
                            Gtk.STOCK_NEW)
        action.connect('activate', self.on_add_launcher_cb)
        self.actions['add_launcher'] = action
        for widget_name in ['menubar_new_launcher', 'toolbar_new']:
            widget = builder.get_object(widget_name)
            widget.set_related_action(action)
            widget.set_use_action_appearance(True)
            
        # Save Launcher action and related widgets
        action = Gtk.Action(_('save_launcher'), _('_Save'), 
                            _('Save'),
                            Gtk.STOCK_SAVE)
        action.connect('activate', self.on_save_launcher_cb)
        self.actions['save_launcher'] = action
        for widget_name in ['menubar_save_launcher', 'toolbar_save']:
            widget = builder.get_object(widget_name)
            widget.set_related_action(action)
            widget.set_use_action_appearance(True)
            
        # Undo action and related widgets
        action = Gtk.Action(_('undo'), _('_Undo'), 
                            _('Undo'),
                            Gtk.STOCK_UNDO)
        action.connect('activate', self.on_undo_cb)
        self.actions['undo'] = action
        for widget_name in ['menubar_undo', 'toolbar_undo']:
            widget = builder.get_object(widget_name)
            widget.set_related_action(action)
            widget.set_use_action_appearance(True)
            
        # Redo action and related widgets
        action = Gtk.Action(_('redo'), _('_Redo'), 
                            _('Redo'),
                            Gtk.STOCK_REDO)
        action.connect('activate', self.on_redo_cb)
        self.actions['redo'] = action
        for widget_name in ['menubar_redo', 'toolbar_redo']:
            widget = builder.get_object(widget_name)
            widget.set_related_action(action)
            widget.set_use_action_appearance(True)
            
        # Revert action and related widgets
        action = Gtk.Action(_('revert'), _('_Revert'), 
                            _('Revert'),
                            Gtk.STOCK_REVERT_TO_SAVED)
        action.connect('activate', self.on_revert_cb)
        self.actions['revert'] = action
        for widget_name in ['menubar_revert', 'toolbar_revert']:
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
                                                              
        self.view_container = builder.get_object('menulibre_window_container')
                                                              
        self.set_view(Views.AUTO)
        
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
        container = builder.get_object(view_mode+"_container")
        container.add( builder.get_object('application_editor') )
        self.view_container.show_all()
        
    def on_add_launcher_cb(self, widget):
        print 'add launcher'
        
    def on_save_launcher_cb(self, widget):
        print 'save launcher'
        
    def on_undo_cb(self, widget):
        print 'undo'
        
    def on_redo_cb(self, widget):
        print 'redo'
        
    def on_revert_cb(self, widget):
        print 'revert'
        
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
        print 'help'
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
