class MenulibreInitException(Exception):
    def __init__(self, section, details):
        self.section = section
        self.details = details
        
    def __str__(self):
        details_string = ""
        if len(self.details) > 1:
            for detail in self.details[1:]:
                details_string += detail + "\n"
        msg = """
MenuLibre failed to initialize...  Please report a bug with the following 
details at https://bugs.launchpad.net/menulibre

Section: %s
Exception: %s

Additional Details: %s""" % (self.section, self.details[0], details_string)
        return repr(msg)
