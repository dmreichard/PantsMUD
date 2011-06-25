class State(object):
    name = "Default State"
    
    def __init__(self, connection):
        self.connection = connection
        
    def on_gainfocus(self):
        pass
    def on_losefocus(self):
        pass
    def on_readline(self, line):
        pass
    def on_write(self):
        pass