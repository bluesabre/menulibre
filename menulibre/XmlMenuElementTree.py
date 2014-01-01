    #lint:disable
try:
    import xml.etree.cElementTree
    from xml.etree.cElementTree import ElementTree, Element, SubElement
except ImportError:
    import xml.etree.ElementTree
    from xml.etree.ElementTree import ElementTree, Element, SubElement
    #lint:enable


def indent(elem, level=0):
    """Indentation code taken from SOURCE to make XML output easier to read."""
    i = "\n" + level * "\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


class XmlMenuElement(Element):
    """An extension of the ElementTree.Element class which adds Menu
    constructing functionality."""

    def __init__(self, *args, **kwargs):
        """Initialize the XmlMenuElement class.  This takes all regular
        arguments for ElementTree.Element, as well as the menu_name keyword
        argument, used for setting the Menu Name property."""
        if 'menu_name' in list(kwargs.keys()):
            menu_name = kwargs['menu_name']
            kwargs.pop("menu_name", None)
        else:
            menu_name = None
        super(XmlMenuElement, self).__init__(*args, **kwargs)
        if menu_name:
            SubElement(self, "Name").text = menu_name

    def addMenu(self, menu_name):
        """Add a submenu <Menu> to this XmlMenuElement.

        Return a reference to that submenu XmlMenuElement."""
        menu = XmlMenuElement("Menu")
        self.append(menu)
        SubElement(menu, "Name").text = menu_name
        return menu

    def addMergeFile(self, filename, merge_type="parent"):
        """Add a merge file <MergeFile> to this XmlMenuElement.

        Return a reference to that merge file XmlMenuElement."""
        element = XmlMenuElement("MergeFile", type=merge_type)
        element.text = filename
        self.append(element)
        return element

    def addMerge(self, merge_type):
        """Add a merge <Merge> to this XmlMenuElement.

        Return a reference to that merge SubElement."""
        return SubElement(self, "Merge", type=merge_type)

    def addLayout(self):
        """Add a layout <Layout> to this XmlMenuElement.

        Return a reference to that layout XmlMenuElement"""
        element = XmlMenuElement("Layout")
        self.append(element)
        return element

    def addFilename(self, filename):
        """Add a filename <Filename> to this XmlMenuElement.

        Return a reference to that filename XmlMenuElement."""
        element = XmlMenuElement("Filename")
        element.text = filename
        self.append(element)
        return element


class XmlMenuElementTree(ElementTree):
    """An extension of the ElementTree.ElementTree class which simplifies the
    creation of FD.o Menus."""

    def __init__(self, menu_name, merge_file=None):
        """Initialize the XmlMenuElementTree class.  Accepts two arguments:
        - menu_name    Name of the menu (e.g. Xfce, Gnome)
        - merge_file   Merge file, used for extending an existing menu."""
        root = XmlMenuElement("Menu", menu_name=menu_name)
        if merge_file:
            root.addMergeFile(merge_file)
        super().__init__(root)

    def write(self, output_file):
        """Override for the ElementTree.write function. This variation adds
        the menu specification headers and writes the output in an
        easier-to-read format."""
        header = """<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE Menu
  PUBLIC '-//freedesktop//DTD Menu 1.0//EN'
  'http://standards.freedesktop.org/menu-spec/menu-1.0.dtd'>
"""
        copy = self.getroot()
        indent(copy)
        with open(output_file, 'w') as f:
            f.write(header)
            ElementTree(copy).write(f, encoding='unicode')

if __name__ == '__main__':
    # Test for standard menu...
    menu = XmlMenuElementTree("Xfce",
            "/etc/xdg/xdg-xubuntu/menus/xfce-applications.menu")
    root = menu.getroot()
    submenu = root.addMenu("Graphics")
    layout = submenu.addLayout()
    layout.addMerge("menus")
    for filename in ['agave.desktop', 'evince.desktop', 'gimp.desktop',
                    'gthumb-import.desktop', 'gthumb.desktop',
                    'display.im6.desktop', 'libreoffice-draw.desktop',
                    'eog.desktop', 'evince-previewer.desktop',
                    'ristretto.desktop', 'shotwell.desktop',
                    'shotwell-viewer.desktop', 'simple-scan.desktop']:
        layout.addFilename(filename)
    layout.addMerge("files")
    menu.write("test.txt")