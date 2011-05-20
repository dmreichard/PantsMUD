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

from pants.engine import Engine

from mud.store import store


###############################################################################
# MUDEngine Class
###############################################################################

class MUDEngine(Engine):
    """
    The singleton MUD engine class.
    """
    def poll(self, poll_timeout):
        Engine.poll(self, poll_timeout)
        
        store.commit()


###############################################################################
# Initialisation
###############################################################################

#: The global mudengine object.
mudengine = MUDEngine()
