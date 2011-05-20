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

import weakref


###############################################################################
# Globals
###############################################################################

#: The central component registry.
_class_components = {}


###############################################################################
# Extendable Class
###############################################################################

class Extendable(object):
    """
    A mixin class which provides persistent component functionality.
    
    An extendable class can have component classes added to it. Each
    instance of the extendable class will have its own, unique instance
    of each component class that has been added. This is particularly
    useful for modular, loosely-coupled designs.
    """
    def __init__(self):
        """
        Initialises the extendable object.
        """
        self.components = {}
    
    def __getattr__(self, key):
        """
        Called when attribute 'key' cannot be found on the object. If a
        component named 'key' exists, it will be returned. Otherwise, an
        AttributeError will be raised.
        
        Parameters:
            key - The name of an attribute.
        """
        try:
            return self.components[key]
        except KeyError:
            raise AttributeError("'%s' object has no attribute '%s'" % (
                                 self.__class__.__name__, key))
    
    @classmethod
    def add_component(cls, ComponentClass, name=None):
        """
        Add a component to this class.
        
        Parameters:
            ComponentClass - The class object that will be used to
                instantiate this component.
            name - An optional string argument specifying the name of
                this component. If not provided, it will default to
                ComponentClass.__name__.lower()
        """
        if not name:
            name = ComponentClass.__name__.lower()
        
        if not cls in _class_components:
            _class_components[cls] = {}
        
        _class_components[cls][name] = ComponentClass
    
    def load_data_components(self, data={}):
        """
        Creates components for this instance and loads relevant data.
        
        Parameters:
            data - A dictionary containing this instance's component
                data.
        """
        cls = self.__class__
        
        if not cls in _class_components:
            return
        
        for name, Component in _class_components[cls].iteritems():
            component = Component(self)
            
            if name in data:
                component.load_data(data[name])
            
            self.components[name] = component
    
    def dump_data_components(self):
        """
        Returns a dictionary containing this instance's component data.
        """
        data = {}
        
        for name, component in self.components.iteritems():
            data[key] = component.dump_data()
        
        return data


###############################################################################
# Component Class
###############################################################################

class Component(object):
    def __init__(self, owner):
        """
        Initialises the component.
        
        Parameters:
            owner - A reference to the object this component is attached
                to.
        """
        self._owner = weakref.ref(owner)
    
    @property
    def owner(self):
        """
        The object that this component is attached to.
        """
        return self._owner()
    
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
