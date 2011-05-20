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

from pants import *
from mud import *
from mud.protocol import flash, telnet, websocket

import log


###############################################################################
# Initialisation
###############################################################################

if __name__ == "__main__":
    # Connect to the storage database.
    store.connect("pantsmud.db")
    
    # Create our servers.
    f = flash.FlashPolicyServer()
    f.listen(port=3999)
    t = telnet.TelnetServer()
    t.listen(port=4000)
    w = websocket.WebSocketServer()
    w.listen(port=4001)
    
    # Start the engine.
    mudengine.start()
