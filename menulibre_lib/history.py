#!/bin/python

class History:
    def __init__(self, parent):
        self.undo = []
        self.redo = []
        self.registry = dict()
        self.parent = parent
        
    def register(self, widget, setter_func):
        self.registry[widget] = setter_func
        
    def add_event(self, path, widget, old_data, new_data):
        #print 'History ADD: \'%s\', \'%s\', \'%s\', \'%s\'' % (path.to_string(), str(name), str(old_data), str(new_data))
        self.parent.enable_save()
        self.redo = []
        self.undo.append( [path, widget, old_data, new_data] )
        self.parent.set_undo_enabled(True)
        self.parent.set_redo_enabled(False)
        
    def Undo(self):
        self.parent.ignore_undo = True
        path, name, old_data, new_data = self.undo.pop()
        self.parent.set_cursor_by_path(path)
        self.redo.append( [path, name, old_data, new_data] )
        func = self.registry[name]
        self.parent.set_redo_enabled(True)
        if not len( self.undo ):
            self.parent.set_undo_enabled(False)
        returned = func( old_data )
        self.parent.ignore_undo = False
        return returned
        
    def Redo(self):
        self.parent.ignore_undo = True
        path, name, old_data, new_data = self.redo.pop()
        self.parent.set_cursor_by_path(path)
        self.undo.append( [path, name, old_data, new_data] )
        func = self.registry[name]
        self.parent.set_undo_enabled(True)
        if not len( self.redo ):
            self.parent.set_redo_enabled(False)
        returned = func( new_data )
        self.parent.ignore_undo = False
        return returned
