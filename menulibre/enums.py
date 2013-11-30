#!/usr/bin/python3


def enum(**enums):
    return type('Enum', (), enums)

Views = enum(AUTO=None,
             CLASSIC='classic_view',
             MODERN='modern_view')

MenuItemTypes = enum(SEPARATOR=-1,
                     APPLICATION=0,
                     LINK=1,
                     DIRECTORY=2)
