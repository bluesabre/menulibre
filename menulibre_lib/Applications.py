import os

from gi.repository import Gtk

stock_icons = Gtk.stock_list_ids()

home = os.getenv('HOME')

default_application = """
[Desktop Entry]
Version=1.0
Type=Application
Name=New Application
Comment=My New Application
Icon=
Exec=
Path=
Terminal=false
StartupNotify=false
Categories=
"""

class Application:
    def __init__(self, filename):
        if not os.path.isfile(filename):
            self.new(filename)
        else:
            self.new_from_file(filename)

    def new(self, filename):
        self.filename = filename
        self.icon = 'gtk-missing-image'
        self.name = 'New Application'
        self.comment = 'My New Application'
        self.command = ''
        self.path = ''
        self.terminal = False
        self.startupnotify = False
        self.categories = []
        self.actions = None
        self.id = None
        self.TreeViewPath = None
        self.original = default_application

    def new_from_file(self, filename):
        self.filename = filename
        self.id = 0

        desktop_file = open(filename, 'r')
        settings = read_desktop_file( filename, desktop_file.read() )
        desktop_file.close()
        
        self.name = settings['name']
        self.icon = settings['icon']
        self.comment = settings['comment']
        self.command = settings['command']
        self.path = settings['path']
        self.terminal = settings['terminal']
        self.startupnotify = settings['startupnotify']
        self.hidden = settings['hidden']
        self.categories = settings['categories']
        self.quicklist_format = settings['quicklist_format']
        self.actions = settings['quicklists']
        self.original = settings['text']

    def print_app(self):
        print 'Filename: %s' % str(self.filename)
        print 'Icon: %s' % str(self.icon)
        print 'Name: %s' % str(self.name)
        print 'Comment: %s' % str(self.comment)
        print 'Exec: %s' % str(self.command)
        print 'Path: %s' % str(self.path)
        print 'Terminal: %s' % str(self.terminal)
        print 'StartupNotify: %s' % str(self.startupnotify)
        print 'Hidden: %s' % str(self.hidden)
        print 'Categories: %s' % str(self.categories)
        print 'Actions: %s' % str(self.actions)
        print 'ID: %s' % str(self.id)
        print 'Quicklists: %s' % str(self.actions)

    def set_filename(self, filename):
        self.filename = filename

    def get_filename(self):
        return self.filename

    def set_icon(self, name):
        self.icon = name

    def get_icon(self):
        return self.icon

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_comment(self, comment):
        self.comment = comment

    def get_comment(self):
        return self.comment

    def set_exec(self, command):
        self.command = command

    def get_exec(self):
        return self.command

    def set_path(self, path):
        self.path = path

    def get_path(self):
        return self.path

    def set_terminal(self, terminal):
        self.terminal = terminal

    def get_terminal(self):
        return self.terminal

    def set_startupnotify(self, startupnotify):
        self.startupnotify = startupnotify

    def get_startupnotify(self):
        return self.startupnotify

    def set_categories(self, categories):
        self.categories = categories

    def get_categories(self):
        return self.categories
            
    def set_hidden(self, hidden):
        self.hidden = hidden
        
    def get_hidden(self):
        return self.hidden
        
    def set_quicklist_format(self, qformat):
        self.quicklist_format = qformat
        
    def get_quicklist_format(self):
        return self.quicklist_format

    def set_actions(self, actions):
        self.actions = actions

    def get_actions(self):
        return self.actions

    def set_id(self, id):
        self.id = id

    def get_id(self):
        return self.id

    def set_original(self, original):
        self.original = original

    def get_original(self):
        return self.original

def get_applications():
    applications = dict()
    app_counter = 1
    filenames = []
    try:
        local_apps = os.path.join( home, '.local', 'share', 'applications' )
        for filename in os.listdir( local_apps ):
            filenames.append(filename)
            if os.path.isfile( os.path.join( local_apps, filename )) and os.path.splitext( filename )[1] == '.desktop':
                app = Application(os.path.join( local_apps, filename ))
                app.id = app_counter
                app_counter += 1
                applications[app.id] = app
    except OSError:
        pass
    for filename in os.listdir('/usr/share/applications'):
        if filename not in filenames:
            if os.path.isfile( os.path.join( '/usr/share/applications', filename )) and os.path.splitext( filename )[1] == '.desktop':
                app = Application(os.path.join( '/usr/share/applications', filename ))
                app.id = app_counter
                app_counter += 1
                applications[app.id] = app
    
    
    return applications
    
defaults = {'filename': '', 'icon': 'gtk-missing-image', 'name': '', 
            'comment': '', 'command': '', 'path': '', 'terminal': False, 
            'startupnotify': False, 'hidden': False, 'categories': [], 
            'quicklists': dict(), 'quicklist_format': 'actions', 'id': 0, 
            'text': default_application}
    
def read_desktop_file(filename, contents):
    # use filename.read()
    settings = {'filename': '', 'icon': 'gtk-missing-image', 'name': '', 
            'comment': '', 'command': '', 'path': '', 'terminal': False, 
            'startupnotify': False, 'hidden': False, 'categories': [], 
            'quicklists': dict(), 'quicklist_format': 'actions', 'id': 0, 
            'text': default_application}
    settings['text'] = contents
    settings['filename'] = filename
    quicklist_key = None
    action_order = 0
    for line in contents.split('\n'):
        try:
            if line[:5] == 'Icon=':
                settings['icon'] = line[5:]
            elif line[:5] == 'Name=':
                if settings['name'] == '':
                    settings['name'] = line[5:]
                else:
                    settings['quicklists'][quicklist_key]['name'] = line[5:]
            elif line[:8] == 'Comment=':
                settings['comment'] = line[8:]
            elif line[:5] == 'Exec=':
                if settings['command'] == '':
                    settings['command'] = line[5:]
                else:
                    settings['quicklists'][quicklist_key]['command'] = line[5:]
            elif line[:5] == 'Path=':
                settings['path'] = line[5:]
            elif line[:9] == 'Terminal=':
                settings['terminal'] = 'true' in line[9:]
            elif line[:14] == 'StartupNotify=':
                settings['startupnotify'] = 'true' in line[14:]
            elif line[:10] == 'NoDisplay=':
                settings['hidden'] = 'true' in line[10:]
            elif line[:11] == 'Categories=':
                settings['categories'] = line[11:].split(';')
                try:
                    settings['categories'].remove('')
                except ValueError:
                    pass
            elif line[:8] == 'Actions=' or 'X-Ayatana-Desktop-Shortcuts' in line:
                settings['quicklist_format'], enabled = line.split('=')
                enabled = enabled.split(';')
            elif line[0] == '[' and line != '[Desktop Entry]':
                if '[desktop action ' in line.lower():
                    quicklist_key = line[16:].replace(']', '')
                elif ' shortcut group]' in line.lower():
                    quicklist_key = line[1:][:len(line)-17]
                settings['quicklists'][quicklist_key] = dict()
                settings['quicklists'][quicklist_key]['order'] = action_order
                action_order += 1
                settings['quicklists'][quicklist_key]['enabled'] = quicklist_key in enabled
        except IndexError:
            pass
    return settings
