#!/usr/bin/python3

def enum(**enums):
    return type('Enum', (), enums)
    
Views = enum(AUTO=None, 
             CLASSIC='classic_view', 
             MODERN='modern_view')
             
MenuItemTypes = enum(APPLICATION=0,
                     DIRECTORY=1,
                     SEPARATOR=2)