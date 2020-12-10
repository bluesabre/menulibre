import sys
import gi

gi.require_version('Garcon', '1.0')
gi.require_version('GarconGtk', '1.0')

from gi.repository import GLib
from gi.repository import Garcon, GarconGtk


def enum(**enums):
    """Add enumarations to Python."""
    return type('Enum', (), enums)


class GarconMenuHelper(object):

    def __init__(self, filename = None):
        if (filename is not None):
            self.menu = Garcon.Menu.new_for_path(filename)
        else:
            self.menu = Garcon.Menu.new_applications()
        self.menu.load()
        #self.filename = self.menu.get_path()

class GarconMenuItemHelper(object):

    MenuItemTypes = enum(
        SEPARATOR=-1,
        APPLICATION=0,
        LINK=1,
        DIRECTORY=2,
        UNKNOWN=3,
    )

    MenuItemKeys = (
        # Key, Type, Required, Types (MenuItemType)
        ("Version", str, False, (0, 1, 2, 3)),
        ("Type", str, True, (0, 1, 2, 3)),
        ("Name", str, True, (0, 1, 2)),
        ("GenericName", str, False, (0, 1, 2)),
        ("NoDisplay", bool, False, (0, 1, 2)),
        ("Comment", str, False, (0, 1, 2)),
        ("Icon", str, False, (0, 1, 2)),
        ("Hidden", bool, False, (0, 1, 2)),
        ("OnlyShowIn", list, False, (0, 1, 2)),
        ("NotShowIn", list, False, (0, 1, 2)),
        ("DBusActivatable", bool, False, (0,)),
        ("PrefersNonDefaultGPU", bool, False, (0,)),
        ("TryExec", str, False, (0,)),
        ("Exec", str, True, (0,)),
        ("Path", str, False, (0,)),
        ("Terminal", bool, False, (0,)),
        ("Actions", list, False, (0,)),
        ("MimeType", list, False, (0,)),
        ("Categories", list, False, (0,)),
        ("Implements", list, False, (0,)),
        ("Keywords", list, False, (0,)),
        ("StartupNotify", bool, False, (0,)),
        ("StartupWMClass", str, False, (0,)),
        ("URL", str, True, (1,))
    )

    def __init__(self, menuitem):
        self.menuitem = menuitem
        self.keyfile = None
        self.data = {
            'type': '',
            'item_type': GarconMenuItemHelper.MenuItemTypes.UNKNOWN,
            'children': [],
            'file': {
                'path': '',
                'uri': '',
                'desktop_id': '',
            },
            'keys': {},
            'standard_keys': {},
            'nonstandard_keys': {},
        }
        self.load_from_menu_item()

    def load_from_menu_item(self):
        self.data['type'] = self._get_type()
        self.data['item_type'] = self._get_item_type()

        if self.data['type'] == 'Separator':
            pass

        elif self.data['type'] == 'Directory':
            for em in self.menuitem.get_elements():
                self.data['children'].append(GarconMenuItemHelper(em))

        elif self.data['type'] in ['Application', 'Link']:
            self.data['file']['path'] = self._get_from_menuitem("Filename")
            self.data['file']['uri'] = self._get_from_menuitem("URI")
            self.data['file']['desktop_id'] = self._get_from_menuitem("ID")

        for key in GarconMenuItemHelper.MenuItemKeys:
            if self.data['item_type'] not in key[3]:
                continue
            self.data['keys'][key[0]] = self._get_from_menuitem(key[0])
        
        del self.menuitem
        self.menuitem = None

    def load_from_keyfile(self):
        pass

    def load(self):
        pass

    def unload(self):
        self.menuitem = None
        self.keyfile = None

    def get_filename(self):
        gfile = self.menuitem.get_file()
        return gfile.get_path()

    def _get_type(self):
        if isinstance(self.menuitem, Garcon.MenuSeparator):
            return 'Separator'
        elif isinstance(self.menuitem, Garcon.Menu):
            return 'Directory'
        else:
            return self._get_string("Desktop Entry", "Type", "Application")
    
    def _get_item_type(self):
        typestr = self._get_type()
        if typestr == 'Separator':
            return GarconMenuItemHelper.MenuItemTypes.SEPARATOR
        elif typestr == 'Application':
            return GarconMenuItemHelper.MenuItemTypes.APPLICATION
        elif typestr == 'Link':
            return GarconMenuItemHelper.MenuItemTypes.LINK
        elif typestr == 'Directory':
            return GarconMenuItemHelper.MenuItemTypes.DIRECTORY
        else:
            return GarconMenuItemHelper.MenuItemTypes.UNKNOWN
    
    def _get_from_menuitem(self, key):
        try:
            if key == "Filename":
                gfile = self.menuitem.get_file()
                return gfile.get_path()
            elif key == "URI":
                return self.menuitem.get_uri()
            elif key == "ID":
                return self.menuitem.get_desktop_id()
            elif key == "Exec":
                return self.menuitem.get_command()
            elif key == "TryExec":
                return self.menuitem.get_try_exec()
            elif key == "Name":
                return self.menuitem.get_name()
            elif key == "GenericName":
                return self.menuitem.get_generic_name()
            elif key == "Comment":
                return self.menuitem.get_comment()
            elif key == "Icon":
                return self.menuitem.get_icon_name()
            elif key == "Path":
                return self.menuitem.get_path()
            elif key == "Hidden":
                return self.menuitem.get_hidden()
            elif key == "Terminal":
                return self.menuitem.requires_terminal()
            elif key == "NoDisplay":
                return self.menuitem.get_no_display()
            elif key == "StartupNotify":
                return self.menuitem.supports_startup_notification()
        except:
            pass
        for knownkey in GarconMenuItemHelper.MenuItemKeys:
            if knownkey[0] == key:
                knowntype = knownkey[1]
                if knowntype == str:
                    return ""
                elif knowntype == bool:
                    return False
                elif knowntype == list:
                    return []
                break
        return None

    def _get_uri(self):
        return self.menuitem.get_uri()

    def _get_desktop_id(self):
        return self.menuitem.get_desktop_id()

    def _get_exec(self):
        return self.menuitem.get_command()

    def _get_try_exec(self):
        return self.menuitem.get_try_exec()

    def _get_name(self):
        return self.menuitem.get_name()

    def _get_generic_name(self):
        return self.menuitem.get_generic_name()

    def _get_comment(self):
        return self.menuitem.get_comment()

    def _get_icon_name(self):
        return self.menuitem.get_icon_name()

    def _get_path(self):
        return self.menuitem.get_path()

    def _get_hidden(self):
        return self.menuitem.get_hidden()

    def _get_terminal(self):
        return self.menuitem.requires_terminal()

    def _get_no_display(self):
        return self.menuitem.get_no_display()

    def _get_startup_notify(self):
        return self.menuitem.supports_startup_notification()

    def _get_categories(self):
        return self._get_string_list("Desktop Entry", "Categories")

    def _get_keywords(self):
        return self._get_string_list("Desktop Entry", "Keywords")
    
    def _get_keyfile(self):
        if self.keyfile is None:
            filename = self.get_filename()
            self.keyfile = GLib.KeyFile.new()
            try:
                self.keyfile.load_from_file(
                    filename, GLib.KeyFileFlags.KEEP_COMMENTS & GLib.KeyFileFlags.KEEP_TRANSLATIONS)
            except gi.repository.GLib.Error:
                pass
        return self.keyfile
    
    def _get_boolean(self, group_name, key, default=False):
        keyfile = self._get_keyfile()
        try:
            return keyfile.get_boolean(group_name, key)
        except gi.repository.GLib.Error:
            return default
    
    def _get_double(self, group_name, key, default=0.0):
        keyfile = self._get_keyfile()
        try:
            return keyfile.get_double(group_name, key)
        except gi.repository.GLib.Error:
            return default
    
    def _get_double_list(self, group_name, key, default=[]):
        keyfile = self._get_keyfile()
        try:
            return keyfile.get_double_list(group_name, key)
        except gi.repository.GLib.Error:
            return default
    
    def _get_int64(self, group_name, key, default=0):
        keyfile = self._get_keyfile()
        try:
            return keyfile.get_int64(group_name, key)
        except gi.repository.GLib.Error:
            return default

    def _get_integer(self, group_name, key, default=0):
        keyfile = self._get_keyfile()
        try:
            return keyfile.get_integer(group_name, key)
        except gi.repository.GLib.Error:
            return default

    def _get_integer_list(self, group_name, key, default=[]):
        keyfile = self._get_keyfile()
        try:
            return keyfile.get_integer_list(group_name, key)
        except gi.repository.GLib.Error:
            return default

    def _get_string(self, group_name, key, default=""):
        keyfile = self._get_keyfile()
        try:
            return keyfile.get_string(group_name, key)
        except gi.repository.GLib.Error:
            return default

    def _get_string_list(self, group_name, key, default=[]):
        keyfile = self._get_keyfile()
        try:
            return keyfile.get_string_list(group_name, key)
        except gi.repository.GLib.Error:
            return default
    
    def _get_uint64(self, group_name, key, default=0):
        keyfile = self._get_keyfile()
        try:
            return keyfile.get_uint64(group_name, key)
        except gi.repository.GLib.Error:
            return default
    
    def _get_value(self, group_name, key, default=None):
        keyfile = self._get_keyfile()
        try:
            return keyfile.get_value(group_name, key)
        except gi.repository.GLib.Error:
            return default
    
    def _get_keys(self, group_name, default = []):
        keyfile = self._get_keyfile()
        try:
            return keyfile.get_keys(group_name)
        except gi.repository.GLib.Error:
            return default
    
    def toArray(self):
        output = {}
        for key, value in self.data.items():
            if key == 'children':
                output['children'] = []
                for child in value:
                    output['children'].append(child.toArray())
            else:
                output[key] = value
        return output



filename = "/home/bluesabre/.config/menus/xfce-applications.menu"
filename = None
menu = GarconMenuHelper(filename)
item = GarconMenuItemHelper(menu.menu)
print(item.toArray())

print("test")

sys.exit(0)
