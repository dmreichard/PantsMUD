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

from copy import deepcopy

from mud.component import Extendable
from mud.store import store


###############################################################################
# Storable Class
###############################################################################

class Storable(object):
    """
    A mixin class which provides basic storage capabilities.
    """
    def __init__(self, key):
        """
        Initialise the storable object.
        
        Parameters:
            key - A unique string identifying the instance.
        """
        self.key = key
    
    def load(self, dump=False):
        """
        Loads this instance's data from the store.
        """
        if self.key in store:
            data = store[self.key]
        else:
            data = {}
        
        self.load_data(data)
        
        if dump and not self.key in store:
            self.dump()
    
    def dump(self):
        """
        Dumps this instance's data to the store.
        """
        data = self.dump_data()
        store[self.key] = data
    
    def load_data(self, data):
        """
        Placeholder. Should load this instance's deserialised data.
        
        Parameters:
            data - Deserialised data.
        """
        pass
    
    def dump_data(self):
        """
        Placeholder. Should return this instance's data in a form that
        can be JSON-serialised.
        """
        return {}


###############################################################################
# Object Class
###############################################################################

class Object(Storable, Extendable):
    """
    A parent class that provides automatic (de)serialisation
    capabilities. Mixes in pants.mud.component.Extendable.
    
    The load_data() and dump_data() methods of this class will use a
    list of the class' storable attributes to either load from or dump
    to a dictionary that should be JSON-serialisable. Any non-private
    attribute (that is, one that does not begin with one or more
    underscores) is considered storable. This default behaviour can be
    modified by overriding the storable() method.
    
    When loading/dumping an attribute 'foo', the existence of a method
    'load_data_foo'/'dump_data_foo' will be checked for. If found, said
    method will be called rather than setattr/getattr.
    """
    def __init__(self, key):
        Storable.__init__(self, key)
        Extendable.__init__(self)
    
    def storable(self):
        """
        Returns this instance's list of storable attributes.
        """
        return [a for a in self.__dict__ if not a.startswith('_')]
    
    def load_data(self, data):
        """
        Loads this instance's deserialised data.
        
        Parameters:
            data - Deserialised data.
        """
        attrs = self.storable()
        
        for attr in attrs:
            if not hasattr(self, attr):
                raise AttributeError("'%s' object has no attribute '%s'" %
                                 (self.__class__.__name__, key))
            
            if not attr in data:
                continue
            
            if hasattr(self, "load_data_%s" % attr):
                getattr(self, "load_data_%s" % attr)(deepcopy(data[attr]))
            else:
                setattr(self, attr, deepcopy(data[attr]))
    
    def dump_data(self):
        """
        Return this instance's data in a form that can be
        JSON-serialised.
        """
        attrs = self.storable()
        
        if not attrs:
            return {}
        
        data = {}
        for attr in attrs:
            if not hasattr(self, attr):
                raise AttributeError("'%s' object has no attribute '%s'" %
                                 (self.__class__.__name__, key))
            
            if hasattr(self, "dump_data_%s" % attr):
                value = getattr(self, "dump_data_%s" % attr)()
            else:
                value = getattr(self, attr)
            
            if not isinstance(value, (basestring, list, tuple, dict, int, float)):
                # TODO Perhaps this should be a call to log.error()
                raise ValueError("Attribute '%s' contains data that cannot be serialised." % attr)
            
            data[attr] = deepcopy(value)
        
        return data
