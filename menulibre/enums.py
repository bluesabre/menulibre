#!/usr/bin/python3


def enum(**enums):
    return type('Enum', (), enums)

MenuItemTypes = enum(SEPARATOR=-1,
                     APPLICATION=0,
                     LINK=1,
                     DIRECTORY=2)
