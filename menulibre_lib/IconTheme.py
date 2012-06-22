from gi.repository import Gtk
import os

import subprocess

def detect_desktop_environment():
    desktop_environment = 'generic'
    if os.environ.get('KDE_FULL_SESSION') == 'true':
        desktop_environment = 'kde'
    elif os.environ.get('GNOME_DESKTOP_SESSION_ID'):
        desktop_environment = 'gnome'
    else:
        try:
            query = subprocess.Popen('xprop -root _DT_SAVE_MODE', shell=True, stdout=subprocess.PIPE)
            info = ''.join(query.stdout.readlines())
            if ' = "xfce4"' in info:
                desktop_environment = 'xfce'
        except (OSError, RuntimeError):
            pass
    return desktop_environment

de = detect_desktop_environment()
if de == 'gnome':
    import gconf
    client = gconf.Client()
    current_theme = client.get_string('/desktop/gnome/interface/icon_theme')
elif de == 'xfce':
    query = subprocess.Popen('xfconf-query -c xsettings -p /Net/IconThemeName', shell=True, stdout=subprocess.PIPE)
    current_theme = query.stdout.read().replace('\n', '')

    
home = os.getenv('HOME')



class IconTheme(Gtk.IconTheme):
    def __init__(self, theme_name, inherited=[]):
        Gtk.IconTheme.__init__(self)
        if os.path.isdir( os.path.join(home, '.icons', theme_name) ):
            self.theme_dir = os.path.join(home, '.icons', theme_name)
        else:
            self.theme_dir = os.path.join('/usr', 'share', 'icons', theme_name)
        try:
            theme_index = open( os.path.join( self.theme_dir, 'index.theme' ), 'r' )
        except IOError:
            if os.path.isdir( os.path.join( self.theme_dir, theme_name ) ):
                self.theme_dir = os.path.join( self.theme_dir, theme_name )
                theme_index = open( os.path.join( self.theme_dir, 'index.theme' ), 'r' )
        inherited_themes = []
        for line in theme_index.readlines():
            if line[:9].lower() == 'inherits=':
                inherited_themes = line.split('=')[1].split(',')
                break
        #for theme in inherited_themes:
        #    inherited.append(theme)
        inherited.append(theme_name)
        theme_index.close()
        #self.index = dict()
        #for toplevel_folder in os.listdir(self.theme_dir):
        #    if os.path.isdir( os.path.join( self.theme_dir, toplevel_folder ) ):
        #        if toplevel_folder in ['scalable', 'symbolic']:
        #            size = 'scalable'
        #        else:
        #            try:
        #                int(toplevel_folder.split('x')[0])
        #                size = str(int(toplevel_folder.split('x')[0]))
        #            except ValueError:
        #                size = None
        #        for second_dir in os.listdir( os.path.join( self.theme_dir, toplevel_folder ) ):
        #            if second_dir in ['scalable', 'symbolic'] and not size:
        #                size = 'scalable'
        #            elif not size:
        #                size = str(int(second_dir.split('x')[0]))
        #            for filename in os.listdir( os.path.join( self.theme_dir, toplevel_folder, second_dir ) ):
        #                if os.path.isfile( os.path.join( self.theme_dir, toplevel_folder, second_dir, filename ) ) and os.path.splitext(filename)[1] != '.icon':
        #                    icon_name = os.path.splitext(filename)[0].replace('-symbolic', '')
        #                    if icon_name not in self.index.keys():
        #                        self.index[icon_name] = dict()
        #                    self.index[icon_name][size] = os.path.join( self.theme_dir, toplevel_folder, second_dir, filename )
        #print self.index
        self.inherits = []
        for theme in inherited_themes:
            if theme not in inherited:
                self.inherits.append(IconTheme(theme.replace('\n', ''), inherited))
        
    def get_stock_image(self, name, IconSize):
        unused, width, height = Gtk.icon_size_lookup(IconSize)
        for item in os.listdir(self.theme_dir): #theme_dir
            if os.path.isdir( os.path.join(self.theme_dir, item) ): #theme_dir/subfolder
                if str(height) in item or item in ['scalable', 'symbolic']:
                    for path in os.listdir( os.path.join(self.theme_dir, item) ): #theme_dir/subfolder/iconsfolder
                        for filename in os.listdir( os.path.join(self.theme_dir, item, path) ):
                            if os.path.splitext( filename )[0] == name and os.path.splitext(filename)[1] != '.icon':
                                return os.path.join(self.theme_dir, item, path, filename)
                        for filename in os.listdir( os.path.join(self.theme_dir, item, path) ):
                            if name in filename and os.path.splitext(filename)[1] != '.icon':
                                return os.path.join(self.theme_dir, item, path, filename)
                else:
                    for path in os.listdir( os.path.join(self.theme_dir, item) ):
                        os.path.join(self.theme_dir, item, path)
                        if str(height) in path or path in ['scalable', 'symbolic']:
                            for filename in os.listdir( os.path.join(self.theme_dir, item, path) ):
                                if os.path.splitext( filename )[0] == name and os.path.splitext(filename)[1] != '.icon':
                                    return os.path.join(self.theme_dir, item, path, filename)
                            for filename in os.listdir( os.path.join(self.theme_dir, item, path) ):
                                if name in filename and os.path.splitext(filename)[1] != '.icon':
                                    return os.path.join(self.theme_dir, item, path, filename)
        for theme in self.inherits:
            result = theme.get_stock_image(name, IconSize)
            if result:
                return result
        return None
        
class CurrentTheme(IconTheme):
    def __init__(self):
        IconTheme.__init__(self, current_theme)
        

                                    
if __name__=='__main__':
    theme = IconTheme('elementary-xfce-dark')
    print theme.get_stock_image('gtk-find', Gtk.IconSize.LARGE_TOOLBAR)
