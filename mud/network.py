###############################################################################
#
# Copyright 2011 Chris Davis
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

from pants.publisher import publisher

from mud.protocol.telnet import TelnetConnection, TelnetServer


###############################################################################
# MUDConnection Class
###############################################################################

class MUDConnection(TelnetConnection):
    def __init__(self, server, socket):
        TelnetConnection.__init__(self, server, socket)
        
        self.line_inbuf = []
    
    def handle_connect(self):
        publisher.publish("mud.connection.connect", self)
    
    def handle_read(self, data):
        TelnetConnection.handle_read(self, data.replace('\r', ''))
        
        while '\n' in self.inbuf:
            line, self.inbuf = self.inbuf.split('\n', 1)
            
            self.line_inbuf.append(line)
        
        publisher.publish("mud.connection.read", self)
    
    def handle_close(self):
        publisher.publish("mud.connection.close", self)


###############################################################################
# MUDServer Class
###############################################################################

class MUDServer(TelnetServer):
    ConnectionClass = MUDConnection
