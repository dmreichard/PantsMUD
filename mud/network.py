###############################################################################
#
# Copyright 2011 Chris Davis and David Reichard
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
###############################################################################

###############################################################################
# Imports
###############################################################################

from mud.publisher import publisher
from mud.state import State

from pants.contrib.telnet import TelnetConnection, TelnetServer


###############################################################################
# MUDConnection Class
###############################################################################

class MUDConnection(TelnetConnection):
    def __init__(self, server, socket):
        TelnetConnection.__init__(self, server, socket)
        
        self.line_inbuf = []
        self.state_stack = []
    
    def on_connect(self):
        publisher.publish("mud.connection.connect", self)
    
    def on_read(self, data):
        try:
            self.state_stack[-1].on_read(data.rstrip('\r\n'))
        except IndexError:  # No state handler on the state stack.
            pass
    
    def on_write(self):
        try:
            self.state_stack[-1].on_write()
        except IndexError: # No state handler on the state stack.
            pass
        
    def on_close(self):
        publisher.publish("mud.connection.close", self)
        
    def push_state(self, state):
        try:
            self.state_stack[-1].on_losefocus()
        except:
            pass
        self.state_stack.append(state(self))
        self.state_stack[-1].on_gainfocus()
    
    def pop_state(self):
        try:
            return_value = self.state_stack.pop()
            return_value.on_losefocus()
            if len(self.state_stack) > 0:
                self.state_stack[-1].on_gainfocus()
        except IndexError:  # No state handler on the state stack to pop.
            return None
        return return_value

    def replace_state(self, state):
        return_value = self.pop_state()
        self.push_state(state)
        return return_value

###############################################################################
# MUDServer Class
###############################################################################

class MUDServer(TelnetServer):
    ConnectionClass = MUDConnection
