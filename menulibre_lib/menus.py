#!/usr/bin/python

import os

class Applications:
    def __init__(self):
        self.id = 0
        self.ids = {}
        self.Applications = {'AudioVideo': [], 'Development': [], 'Education': [], 'Game': [], 'Graphics': [], 'Network': [], 'Office': [], 'Settings': [], 'System': [], 'Utility': [], 'Other': [], 'WINE': []}
        for item in os.listdir('/usr/share/applications'):
            if '.desktop' in item and os.path.isfile( os.path.join('/usr/share/applications', item)):
                app = DesktopFile(os.path.join('/usr/share/applications', item), self.id)
                for category in app.get_categories():
                    if category in self.Applications.keys():
                        self.Applications[category].append(app)
                    if 'wine' in category.lower():
                        self.Applications['WINE'].append(app)
                self.id += 1
        usrapps = os.path.join( os.getenv('HOME'), '.local', 'share', 'applications' )
        if os.path.isdir(usrapps):
            for item in os.listdir(usrapps):
                if '.desktop' in item and os.path.isfile( os.path.join(usrapps, item)):
                    app = DesktopFile(os.path.join(usrapps, item), self.id)
                    for category in app.get_categories():
                        if category in self.Applications.keys():
                            self.Applications[category].append(app)
                    self.id += 1
        for category in self.Applications.keys():
            self.Applications[category].sort()
        self.update_ids()
                    
    def get_categories(self):
        categories = []
        for item in self.DesktopFiles:
            for cat in item.get_categories():
                if cat not in categories and cat[:2] != 'X-':
                    categories.append(cat)
        categories.sort()
        return categories
        
    def update_ids(self):
        self.ids = {}
        for key in self.Applications.keys():
            for appindex in range(len(self.Applications[key])):
                appid = self.Applications[key][appindex].id
                self.ids[appid] = [key, appindex]
                
    def get_app_by_id(self, id):
        cat, index = self.ids[id]
        return self.Applications[cat][index]
        

class DesktopFile:
    def __init__(self, filename, id=None):
        self.filename = filename
        self.id = id
        self.original, contents = self.open(filename)
        self.DesktopFile = dict()
        lastAppended = None
        for line in contents:
            try:
                if line[0] == '#':
                    pass
                elif line[0] == '[':
                    self.DesktopFile[line.lower()] = dict()
                    lastAppended = line.lower()
                else:
                    try:
                        key, value = line.split('=', 1)
                    except:
                        print line
                    if key.lower() in ['actions', 'x-ayatana-desktop-shortcuts']:
                        self.DesktopFile['$UnityQuicklists'] = {'format': key.lower(), 'original_format': key, 'enabled': value}
                    else:
                        self.DesktopFile[lastAppended][key.lower()] = value
            except IndexError:
                pass
    
    def open(self, filename):
        if not os.path.isfile(filename):
            pass
        fileobject = open(filename, 'r')
        original = contents = fileobject.readlines()
        for lineno in range(len(contents)):
            contents[lineno] = contents[lineno].rstrip().lstrip()
        fileobject.close()
        return original, contents
    
    def get_name(self):
        try:
            return self.DesktopFile['[desktop entry]']['name']
        except KeyError:
            return ''
            
    def get_comment(self):
        try:
            return self.DesktopFile['[desktop entry]']['comment']
        except KeyError:
            return ''
    
    def get_icon(self):
        return self.DesktopFile['[desktop entry]']['icon']
        
    def get_exec(self):
        try:
            return self.DesktopFile['[desktop entry]']['exec']
        except KeyError:
            return ''
        
    def get_path(self):
        try:
            return self.DesktopFile['[desktop entry]']['path']
        except KeyError:
            return ''
        
    def get_categories(self):
        try:
            categories = self.DesktopFile['[desktop entry]']['categories']
            return categories.split(';')
        except KeyError:
            return []
            
    def get_terminal(self):
        try:
            showinterminal = self.DesktopFile['[desktop entry]']['terminal']
            return showinterminal.lower() == 'true'
        except:
            return False
            
    def get_startupnotify(self):
        try:
            notify = self.DesktopFile['[desktop entry]']['startupnotify']
            return notify.lower() == 'true'
        except:
            return False
            
    def get_hidden(self):
        try:
            hidden = self.DesktopFile['[desktop entry]']['nodisplay']
            return hidden.lower() == 'true'
        except:
            return False
            
    def get_quicklists(self):
        quicklists = []
        try:
            list_format = self.DesktopFile['$UnityQuicklists']['format']
            enabled = self.DesktopFile['$UnityQuicklists']['enabled'].lower().split(';')
            for key in self.DesktopFile.keys():
                if key not in ['[desktop entry]', '$UnityQuicklists']:
                    if list_format == 'actions':
                        list_name = key.replace('[desktop action ', '').replace(']', '')
                    else:
                        list_name = key.replace('[', '').replace(' shortcut group]', '')
                    list_enabled = list_name in enabled
                    name = self.DesktopFile[key]['name']
                    command  = self.DesktopFile[key]['exec']
                    quicklists.append( [list_enabled, name, command] )
        except KeyError:
            pass
        return quicklists
            
    def get_id(self):
        return self.id
    
if __name__=='__main__':
    a = Applications()
    
