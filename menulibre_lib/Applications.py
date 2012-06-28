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
        self.icon = ('stock', 'gtk-missing-image')
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
        self.changes = {'filename': None, 'icon': None, 'name': None, 'comment': None, 
                        'command': None, 'path': None, 'terminal': None, 'startupnotify': None, 'categories': None,
                        'actions': None, 'id': None, 'TreeViewPath': None, 'original': None}

    def new_from_file(self, filename):
        self.filename = filename
        self.icon = ('stock', 'gtk-missing-image')
        self.name = ''
        self.comment = ''
        self.command = ''
        self.path = ''
        self.terminal = False
        self.startupnotify = False
        self.categories = []
        self.actions = dict()
        self.id = 0
        self.TreeViewPath = None
        self.original = ''
        self.changes = {'filename': None, 'icon': None, 'name': None, 'comment': None, 
                        'command': None, 'path': None, 'terminal': None, 'startupnotify': None, 'categories': None,
                        'actions': None, 'id': None, 'TreeViewPath': None, 'original': None}

        desktop_file = open(filename, 'r')
        contents = desktop_file.readlines()
        desktop_file.close()
        group_count = 0
        quicklist_key = None
        self.original = ''.join(contents)
        action_order = 0
        for line in contents:
            line = line.rstrip()
            try:
                if line[0] == '[':
                    if group_count > 0:
                        if '[desktop action ' in line.lower():
                            quicklist_key = line[16:].replace(']', '')
                        elif ' shortcut group]' in line.lower():
                            quicklist_key = line[1:][:len(line)-17]
                        else:
                            print "Trouble line: %s" % str(line)
                        self.actions[quicklist_key]['order'] = action_order
                        action_order += 1
                    group_count += 1
                else:
                    if line[:5].lower() == 'name=':
                        if group_count > 1:
                            self.actions[quicklist_key]['name'] = line[5:]
                        else:
                            self.name = line[5:]
                    elif line[:5].lower() == 'icon=':
                        icon = line[5:]
                        if icon in stock_icons:
                            self.icon = ('stock', icon)
                        else:
                            if os.path.splitext(icon)[0] != icon:
                                self.icon = ('file', icon)
                            else:
                                self.icon = ('theme', icon)
                    elif line[:8].lower() == 'comment=':
                        self.comment = line[8:]
                    elif line[:5].lower() == 'exec=':
                        if group_count > 1:
                            self.actions[quicklist_key]['command'] = line[5:]
                        else:
                            self.command = line[5:]
                    elif line[:5].lower() == 'path=':
                        self.path = line[5:]
                    elif line[:9].lower() == 'terminal=':
                        if line[9:] == 'true':
                            self.terminal = True
                        else:
                            self.terminal = False
                    elif line[:14].lower() == 'startupnotify=':
                        if line[14:] == 'true':
                            self.startupnotify = True
                        else:
                            self.startupnotify = False
                    elif line[:11].lower() == 'categories=':
                        categories = line[11:]
                        self.categories = categories.split(';')
                        try:
                            self.categories.remove('')
                        except ValueError:
                            pass
                    elif line[:8].lower() == 'actions=':
                        self.actions = dict()
                        self.actions['#format'] = 'actions'
                        for key in line[8:].split(';'):
                            if key != '':
                                self.actions[key] = {'enabled': True}
                    elif line[:28].lower() == 'x-ayatana-desktop-shortcuts=':
                        self.actions = dict()
                        self.actions['#format'] = 'x-ayatana-desktop-shortcuts'
                        for key in line[28:].split(';'):
                            if key != '':
                                self.actions[key] = {'enabled': True}
            except IndexError:
                pass

    def print_app(self):
        print 'Filename: %s' % str(self.filename)
        print 'Icon: %s' % str(self.icon)
        print 'Name: %s' % str(self.name)
        print 'Comment: %s' % str(self.comment)
        print 'Exec: %s' % str(self.command)
        print 'Path: %s' % str(self.path)
        print 'Terminal: %s' % str(self.terminal)
        print 'StartupNotify: %s' % str(self.startupnotify)
        print 'Categories: %s' % str(self.categories)
        print 'Actions: %s' % str(self.actions)
        print 'ID: %s' % str(self.id)
        print 'TreeViewPath: %s' % str(self.TreeViewPath)
        #print 'Original: %s' % str(self.original)
        print 'Changes: %s' % str(self.changes)


    def revert(self):
        for key in self.changes.keys():
            self.changes[key] = None

    def set_filename(self, filename):
        self.changes['filename'] = filename

    def get_filename(self):
        if self.changes['filename']:
            return self.changes['filename']
        else:
            return self.filename

    def set_icon(self, type, name):
        self.changes['icon'] = (type, name)

    def get_icon(self):
        if self.changes['icon']:
            return self.changes['icon']
        else:
            return self.icon

    def set_name(self, name):
        self.changes['name'] = name

    def get_name(self):
        if self.changes['name']:
            return self.changes['name']
        else:
            return self.name

    def set_comment(self, comment):
        self.changes['comment'] = comment

    def get_comment(self):
        if self.changes['comment']:
            return self.changes['comment']
        else:
            return self.comment

    def set_exec(self, command):
        self.changes['command'] = command

    def get_exec(self):
        if self.changes['command']:
            return self.changes['command']
        else:
            return self.command

    def set_path(self, path):
        self.changes['path'] = path

    def get_path(self):
        if self.changes['path']:
            return self.changes['path']
        else:
            return self.path

    def set_terminal(self, terminal):
        self.changes['terminal'] = terminal

    def get_terminal(self):
        if self.changes['terminal']:
            return self.changes['terminal']
        else:
            return self.terminal

    def set_startupnotify(self, startupnotify):
        self.changes['startupnotify'] = startupnotify

    def get_startupnotify(self):
        if self.changes['startupnotify']:
            return self.changes['startupnotify']
        else:
            return self.startupnotify

    def set_categories(self, categories):
        self.changes['categories'] = categories

    def get_categories(self):
        if self.changes['categories']:
            return self.changes['categories']
        else:
            return self.categories

    def set_actions(self, actions):
        self.changes['actions'] = actions

    def get_actions(self):
        if self.changes['actions']:
            return self.changes['actions']
        else:
            return self.actions

    def set_id(self, id):
        self.changes['id'] = id

    def get_id(self):
        if self.changes['id']:
            return self.changes['id']
        else:
            return self.id

    def set_TreeViewPath(self, path):
        self.changes['path']

    def get_TreeViewPath(self):
        if self.changes['TreeViewPath']:
            return self.changes['TreeViewPath']
        else:
            return self.TreeViewPath

    def set_original(self, original):
        self.changes['original'] = original

    def get_original(self):
        if self.changes['original']:
            return self.changes['original']
        else:
            return self.original

def get_applications():
    applications = dict()
    app_counter = 1
    for filename in os.listdir('/usr/share/applications'):
        if os.path.isfile( os.path.join( '/usr/share/applications', filename )) and os.path.splitext( filename )[1] == '.desktop':
            app = Application(os.path.join( '/usr/share/applications', filename ))
            app.id = app_counter
            app_counter += 1
            applications[app.id] = app
    local_apps = os.path.join( home, '.local', 'share', 'applications' )
    for filename in os.listdir( local_apps ):
        if os.path.isfile( os.path.join( local_apps, filename )) and os.path.splitext( filename )[1] == '.desktop':
            app = Application(os.path.join( local_apps, filename ))
            app.id = app_counter
            app_counter += 1
            applications[app.id] = app
    return applications
