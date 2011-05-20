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

import hashlib
import string
import struct

from pants.network import Connection, Server


###############################################################################
# WebSocketConnection Class
###############################################################################

class WebSocketConnection(Connection):
    """
    A basic implementation of a WebSocket connection.
    
    A WebSocketConnection object is capable of parsing WebSocket
    handshake requests, building responses to those requests as well as
    reading, writing, decoding and encoding data transmitted over the
    connection.
    
    This is an implementation of version 76 of the draft WebSocket
    protocol. This is not a final draft, and both the handshake and the
    data framing will be changed in future revisions. The version of the
    protocol that this implementation is based off is available at:
    
        http://tools.ietf.org/html/draft-hixie-thewebsocketprotocol-76
    """
    def __init__(self, server, socket):
        Connection.__init__(self, server, socket)
        
        self.handshake = False # Is the WebSocket handshake complete?
        self.inbuf = ""
        self.packet_inbuf = [] # Received packets.
    
    ##### General Methods #####################################################
    
    def send(self, data):
        """
        Sends data to the socket.
        
        If a handshake has been performed the handshake is UTF-8 encoded
        and wrapped between 0x00 and 0xFF bytes, as specified in the
        WebSocket Protocol. Otherwise, it is sent to the socket "raw".
        
        Parameters:
            data - A string containing the data to be sent to the
                socket.
        """
        if self.handshake:
            data = data.decode("latin1").encode("utf-8")
            self.write(data)
        else:
            self.write(data)
    
    ##### Public Event Handlers ###############################################
    
    def handle_read(self, data):
        """
        Reads data from the socket.
        
        If a handshake has not yet been performed, treats the data as a
        handshake request. Otherwise, treats it as regular data and
        processes it.
        """
        if self.handshake:
            self.inbuf += data
            self.websocket_process_inbuf()
        elif self.websocket_process_handshake(data) is False:
            self.close()
    
    ##### WebSocket Methods ###################################################
    
    def websocket_process_inbuf(self):
        """
        Reads whole packets from the raw inbuf and appends them to the
        packet inbuf.
        """
        packet_start = self.inbuf.find('\x00')
        packet_end = self.inbuf.find('\xFF')
        
        while packet_start != -1 and packet_end != -1:
            if packet_start > packet_end:
                # TODO Malformed packet. Raise a better exception here.
                raise Exception("Encounteres malformed WebSocket packet.")
            
            packet = self.inbuf[packet_start:packet_end+1]
            processed_packet = packet[1:-1].decode("UTF-8").encode("latin1")
            
            # Anything before the packet_start point is ignored.
            self.inbuf = self.inbuf[packet_end+1:]
            
            self.packet_inbuf.append(processed_packet)
            
            packet_start = self.inbuf.find('\x00')
            packet_end = self.inbuf.find('\xFF')
    
    def websocket_process_handshake(self, raw_handshake):
        """
        Processes a WebSocket handshake request and sends a response.
        
        Returns True if the request was valid, False otherwise.
        
        Parameters:
            raw_handshake - A string containing a WebSocket handshake
                request.
        """
        # Split handshake into lines.
        handshake = raw_handshake.split("\r\n")
        
        # Validate basic form.
        handshake = self.websocket_validate_handshake(handshake)
        if handshake is False:
            return False
        else:
            path, final_bytes, raw_fields = handshake
        
        # Validate fields.
        fields = self.websocket_validate_fields(raw_fields)
        if fields is False:
            return False
        
        # Build response.
        response = self.websocket_build_response(path, final_bytes, fields)
        if response is False:
            return False
        
        # Send response.
        self.send(response)
        self.handshake = True
        
        return True
    
    def websocket_validate_handshake(self, handshake):
        """
        Validates the basic form of a WebSocket handshake request.
        
        Returns False if the handshake form is invalid, otherwise
        returns the path, final eight bytes and raw fields present in
        the handshake as a tuple.
        
        Parameters:
            handshake - A list of strings, each string being a line of
                a WebSocket handshake request.
        """
        if len(handshake) < 3:
            # We are validating the three mandatory NON-FIELD lines.
            return False
        
        # Validate the header.
        header = handshake.pop(0)
        get, path, http = header.split()
        if not get == "GET":
            # Not a GET request?
            return False
        elif not http == "HTTP/1.1":
            # Not HTTP 1.1?
            return False
        elif not path.startswith('/'):
            # Invalid path.
            return False
        
        # Validate the final 8 bytes.
        blank, final_bytes = handshake[-2:]
        if blank != '':
            # Not blank?
            return False
        elif len(final_bytes) != 8:
            # Invalid final bytes.
            return False
        
        # Return the lines containing fields.
        return path, final_bytes, handshake[:-2]
    
    def websocket_validate_fields(self, raw_fields):
        """
        Validates the existence and value of mandatory fields within the
        handshake request.
        
        Return False if the fields are invalid.
        
        Parameters:
            raw_fields - A string containing the fields present in the
                handshake request.
        """
        fields = {}
        
        permitted = string.ascii_letters + string.digits + string.punctuation
        permitted = set(permitted.replace(':','')) # Colon not permitted.
        
        for raw_field in raw_fields:
            sep = raw_field.find(": ")
            if sep != -1:
                name, value = raw_field.split(": ", 1)
                if set(name) - permitted:
                    # Broken handshake
                    return False
                fields[name] = value
            else:
                # Broken handshake.
                return False
        
        # Validate field existence.
        if not "Upgrade" in fields:
            return False
        elif not "Connection" in fields:
            return False
        elif not "Host" in fields:
            return False
        elif not "Origin" in fields:
            return False
        elif not "Sec-WebSocket-Key1" in fields:
            return False
        elif not "Sec-WebSocket-Key2" in fields:
            return False
        
        # Validate field values.
        if not fields["Upgrade"].lower() == "websocket":
            return False
        elif not fields["Connection"].lower() == "upgrade":
            return False
        
        return fields
    
    def websocket_build_response(self, path, final_bytes, fields):
        """
        Returns a valid response to a WebSocket handshake.
        
        Returns False if a valid response cannot be built.
        
        Parameters:
            path - The resource being accessed. Typically /.
            final_bytes - The final eight bytes of the handshake
                request.
            fields - A dictionary containing the fields present in the
                handshake request.
        """
        host, port = fields["Host"].split(':')
        resource_name = path
        
        location = "ws://%s:%s%s" % (host, port, resource_name)
        origin = fields["Origin"]
        if "Sec-WebSocket-Protocol" in fields:
            subprotocol = fields["Sec-WebSocket-Protocol"]
        key1 = fields["Sec-WebSocket-Key1"]
        key2 = fields["Sec-WebSocket-Key2"]
        
        challenge_response = self.websocket_build_challenge_response(key1, key2, final_bytes)
        if challenge_response is False:
            return False
        
        # Build the response string.
        response = "HTTP/1.1 101 WebSocket Protocol Handshake\r\n"
        response += "Upgrade: WebSocket\r\n"
        response += "Connection: Upgrade\r\n"
        response += "Sec-WebSocket-Location: " + location + "\r\n"
        response += "Sec-WebSocket-Origin: " + origin + "\r\n"
        if "Sec-WebSocket-Protocol" in fields:
            response += "Sec-WebSocket-Protocol: " + subprotocol + "\r\n"
        response += "\r\n"
        response += challenge_response + "\r\n"
        
        return response
    
    def websocket_build_challenge_response(self, key1, key2, final_bytes):
        """
        Returns the response to the challenge in a WebSocket handshake.
        
        Returns False if a valid response cannot be built.
        
        Parameters:
            key1 - The contents of the Sec-WebSocket-Key1 field.
            key2 - The contents of the Sec-WebSocket-Key2 field.
            final_bytes - The final eight bytes of the handshake.
        """
        def build_num(key):
            """
            Returns the integer "hidden" within a key.
            """
            n = 0
            s = 0
            
            for c in key:
                if c.isdigit():
                    n = (n * 10) + int(c)
                elif c.isspace():
                    s += 1
            
            if n > 4294967295:
                raise ValueError
            elif s < 1:
                raise ValueError
            
            return n / s
        
        try:
            num1 = build_num(key1)
            num2 = build_num(key2)
        except ValueError:
            return False
        
        challenge = struct.pack(">II", num1, num2) + final_bytes
        
        return hashlib.md5(challenge).digest()


###############################################################################
# WebSocketServer Class
###############################################################################

class WebSocketServer(Server):
    """
    A basic implementation of a WebSocket server.
    """
    ConnectionClass = WebSocketConnection
