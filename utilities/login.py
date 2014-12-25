#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#Licensed by Alan Laughter under the GPLv3

import web, sys, os, time, uuid, hashlib
from utilities import dbmkr
from pprint import pprint

import sqlite3 as sql


class session_controller(object):
    """This should be an object which is used for different types of logins,
     admin, mod, user, etc each with thier own cookie type"""


    def __init__(self, name):
        self.db = dbmkr.database(name)
        self.db.create('usersessions', "user TEXT, sessoncode TEXT")
        self.db.create('useraccounts', "user TEXT, site TEXT, type INT, password TEXT, \
            salt TEXT")

    def get_users(self):
        return [x[0] for x in self.db.__get_fields__('useraccounts')]

    def session_in(self, username, sessioncode):
        #info = self.db.select('usersessions',('user',),[username,])
        #if len(info) == 0:
        self.db.insert('usersessions', [username, sessioncode])
    
    def session_out(self, username,sessioncode):
        
        info = self.db.select('usersessions',('user',),(username,))
        for entry in xrange(len(info)):
            if info[entry][0] == username:
                if int(info[entry][1].split(":")[1]) < time.time():
                    self.db.delete('usersessions', 'name', username)
                    return 0
                if info[entry][1] == sessioncode:
                    return self.user_type(username)
        return 0
        
        #useraccounts, user, password, salt)
    def new_user(self, username, site, AccType, password):
        if username not in self.get_users():
            this_salt = uuid.uuid4().hex
            hashed_password = hashlib.sha512(password + this_salt).hexdigest()
            insert_string = username + ", " + str(AccType) + ", " + \
                hashed_password + ", " + this_salt
            self.db.insert ('useraccounts', (username, site, AccType, 
                hashed_password, this_salt))

    def check_user(self, username, site, password):
        info = self.db.select('useraccounts', ('user', 'site'), (username, site))
        if info[0][0] == username:
            if hashlib.sha512(password + info[0][4]
                ).hexdigest() == info[0][3]:
                return True
        return False

    def user_type(self, username):
        info = self.db.select('useraccounts', ('user',), (username,))
        return info[0][2]
