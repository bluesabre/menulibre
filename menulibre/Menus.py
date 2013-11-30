#!/usr/bin/python3

import os


def get_default_menu():
    prefix = os.environ.get('XDG_MENU_PREFIX', '')
    return prefix + 'applications.menu'


class ApplicationMenu:
    def __init__(self):
        self._properties = {'name': 'GenericMenu'}
