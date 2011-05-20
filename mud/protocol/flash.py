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

from pants.network import Connection, Server


###############################################################################
# Constants
###############################################################################

#: Basic policy handshake response.
FLASH_POLICY_RESPONSE = """<cross-domain-policy>
    <allow-access-from-domain="*" ro-port="*" />
</cross-domain-policy>/x00
"""


###############################################################################
# FlashPolicyConnection Class
###############################################################################

class FlashPolicyConnection(Connection):
    """
    A basic implementation of a Flash policy connection.
    
    Reads data from the socket once. If a request for a Flash policy
    file is found, the policy file is sent. In any case, the connection
    is closed immediately after the inital data has been read. While it
    is possible that the policy request will not be contained in the
    initial data, it is highly unlikely. Closing connections is more
    intelligent than keeping them open, waiting for a policy request
    that may never arrive.
    """
    
    ##### Public Event Handlers ###############################################
    
    def handle_read(self, data):
        """
        Reads data from the socket and then closes it.
        
        If a request for a Flash policy file is received, the policy
        file is sent.
        """
        if self.flash_policy_validate(data):
            self.flash_policy_respond()
        
        self.close()
    
    ##### Flash Methods #######################################################
    
    def flash_policy_validate(self, raw_handshake):
        """
        Returns True if the given data is a valid Flash policy request.
        Otherwise, returns False.
        
        Parameters:
            raw_handshake - The raw data received by the connection.
        """
        handshake = raw_handshake.strip().split("\r\n")
        
        # Absolute minimum requirement for a handshake request.
        if "<policy-file-request/>\x00" in handshake:
            return True
        else:
            return False
    
    def flash_policy_respond(self):
        """
        Sends the Flash policy server's policy to the socket.
        """
        self.outbuf += self.server.flash_policy


###############################################################################
# FlashPolicyServer Class
###############################################################################

class FlashPolicyServer(Server):
    """
    A basic implementation of a Flash policy server.
    """
    ConnectionClass = FlashPolicyConnection
    
    def __init__(self, policy=FLASH_POLICY_RESPONSE):
        """
        Initialises the Flash policy server.
        """
        Server.__init__(self)
        
        self.flash_policy = FLASH_POLICY_RESPONSE
