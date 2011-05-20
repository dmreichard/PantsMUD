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

import json
import os
import sqlite3
import UserDict

from mud.publisher import publisher

from mud.shared import log


###############################################################################
# Constants
###############################################################################

SCHEMA = """CREATE TABLE pants_data (
    key TEXT UNIQUE PRIMARY KEY NOT NULL,
    data TEXT NOT NULL
);"""


###############################################################################
# Exceptions
###############################################################################

class NotConnectedError(Exception):
    pass


###############################################################################
# Store Class
###############################################################################

class Store(UserDict.DictMixin):
    """
    A subclass of UserDict.DictMixin which stores JSON-serialised data
    in an SQLite backend.
    
    This class is similar to Python's Shelf class except that it uses
    JSON to serialise data, maps data to a string key and stores the key
    -value pair in an SQLite database. The SQLite database is
    automatically commited whenever it is modified.
    """
    def __init__(self):
        self.connected = False
        self.con = None
        self.dirty = False # Do we need to commit?
    
    ##### Control #############################################################
    
    def connect(self, filename=":memory:"):
        """
        Connect the store to a database file.
        
        If the core is already connected, its current connection will be
        closed. If no filename is specified, a temporary in-memory
        database will be created. 
        """
        if self.connected:
            self.close()
        
        if filename == ":memory:" or not os.path.exists(filename):
            new_store = True
        else:
            new_store = False
        
        self.con = sqlite3.connect(filename)
        self.connected = True
        
        if new_store:
            cur = self.con.cursor()
            cur.execute(SCHEMA)
        
        publisher.subscribe("pants.engine.stop", self.close)
    
    def commit(self, override=False):
        """
        Commit any unsaved changes to the store.
        
        Parameters:
            override - If True, store will be committed even if it is
                not flagged as dirty. Defaults to False.
        """
        if not self.connected:
            raise NotConnectedError("Store is not connected.")
        elif not override and not self.dirty:
            return
        
        self.con.commit()
        self.dirty = False
    
    def close(self):
        """
        Close the store's database connection.
        """
        if not self.connected:
            raise NotConnectedError("Store is not connected.")
        
        try:
            publisher.unsubscribe("pants.engine.stop", self.close)
        except AttributeError:
            # close() is called from __del__ - in certain cases, the
            # publisher will get GC'd before the store, causing this
            # call to produce a rather baffling AttributeError which we
            # can safely ignore.
            pass
        
        self.commit()
        self.con.close()
        self.con = None
        self.connected = False
    
    ##### Magic Methods #######################################################
    
    def __del__(self):
        if not hasattr(self, "connected") or not self.connected:
            return
        
        self.close()
    
    def __len__(self):
        if not self.connected:
            raise NotConnectedError("Store is not connected.")
        
        return len(self.keys())
    
    def __contains__(self, pattern):
        if not self.connected:
            raise NotConnectedError("Store is not connected.")
        
        try:
            self.select(pattern).next()
        except StopIteration:
            return False # No keys? Return False.
        
        return True # One or more keys? Return True.
    
    def __getitem__(self, key):
        if not self.connected:
            raise NotConnectedError("Store is not connected.")
        
        # TODO Improve this method.
        sql = "SELECT data FROM pants_data WHERE key=?"
        cur = self.con.cursor()
        cur.execute(sql, (key,))
        row = cur.fetchone() # Keys are unique, there can only be one row.
        
        if not row: # Row is None if there are no rows.
            # TODO Log this?
            raise KeyError(repr(key))
        
        raw_data, = row
        
        return json.loads(raw_data)
    
    def __setitem__(self, key, data):
        if not self.connected:
            raise NotConnectedError("Store is not connected.")
        
        raw_data = json.dumps(data)
        
        sql = "SELECT * FROM pants_data WHERE key=?"
        cur = self.con.cursor()
        cur.execute(sql, (key,))
        # Hacky.
        row = cur.fetchone() # Keys are unique, there can only be one.
        
        if not row: # Row is None if there are no rows.
            sql = "INSERT INTO pants_data (key, data) VALUES (?, ?)"
            cur.execute(sql, (key, raw_data))
        else:
            sql = "UPDATE pants_data SET data=? WHERE key=?"
            cur.execute(sql, (raw_data, key))
        
        self.dirty = True # We need to commit.
    
    def __delitem__(self, key):
        if not self.connected:
            raise NotConnectedError("Store is not connected.")
        
        sql = "DELETE FROM pants_data WHERE key=?"
        cur = self.con.cursor()
        cur.execute(sql, (key,))
    
    def __iter__(self):
        for key in self.iterkeys():
            yield key
    
    ##### Interface ###########################################################
    
    def has_key(self, key):
        """
        Test for the presence of a key in the store.
        """
        if not self.connected:
            raise NotConnectedError("Store is not connected.")
        
        return self.__contains__(key)
    
    def get(self, key, default=None):
        """
        Return the value of key if key exists in the store, otherwise
        return the supplied default value.
        """
        if not self.connected:
            raise NotConnectedError("Store is not connected.")
        
        try:
            return self[key]
        except KeyError:
            return default
    
    def keys(self):
        """
        Return a copy of the store's list of keys.
        """
        if not self.connected:
            raise NotConnectedError("Store is not connected.")
        
        return list(self.iterkeys())
    
    def iterkeys(self):
        """
        Return an iterator over the store's keys.
        """
        if not self.connected:
            raise NotConnectedError("Store is not connected.")
        
        sql = "SELECT key FROM pants_data"
        cur = self.con.cursor()
        cur.execute(sql)
        
        row = cur.fetchone()
        while row:
            key, = row
            yield key
            row = cur.fetchone()
    
    def select(self, pattern="%"):
        """
        Return an iterator over all keys which match the given
        pattern.
        """
        if not self.connected:
            raise NotConnectedError("Store is not connected.")
        
        sql = "SELECT key FROM pants_data WHERE key LIKE ?"
        
        cur = self.con.cursor()
        cur.execute(sql, (pattern,))
        
        row = cur.fetchone()
        while row:
            key, = row
            yield key
            row = cur.fetchone()


###############################################################################
# Initialisation
###############################################################################

#: The global store object.
store = Store()
