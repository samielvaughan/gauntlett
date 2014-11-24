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
        self.db.create('useraccounts', "user TEXT, type INT, password TEXT, \
            salt TEXT")
        self.users = [x[0] for x in self.db.__get_fields__('useraccounts')]

    def get_users(self):
        return self.users

    def session_in(self, username, sessioncode):
        info = self.db.select('usersessions', ('user',), [username,])
        if username not in info:
            self.db.insert('usersessions', [username, sessioncode])
    
    def session_out(self, username,sessioncode):
        
        info = self.db.select('usersessions',('user',),(username,))
        print "=================="
        print info
        print "=================="
        for entry in xrange(len(info)):
            if info[0] == username:
                if int(info[1].split(":")[1]) < time.time():
                    self.db.delete('usersessions', 'name', username)
                    return 0
                if info[entry]['sessioncode'] == sessioncode:
                    return self.user_type(username)
        return 0
        
        #useraccounts, user, password, salt)
    def new_user(self, username, AccType, password):
        if username not in self.users:
            this_salt = uuid.uuid4().hex
            hashed_password = hashlib.sha512(password + this_salt).hexdigest()
            insert_string = username + ", " + str(AccType) + ", " + \
                hashed_password + ", " + this_salt
            self.db.insert ('useraccounts', (username, AccType, 
                hashed_password, this_salt))

    def check_user(self, username, password):
        info = self.db.select('useraccounts', ('user',), (username,))
        for entry in xrange(len(info)):
            if info[0][0] == username:
                return hashlib.sha512(password + info[0][3]
                    ).hexdigest() == info[0][2]
        return False

    def user_type(self, username):
        info = self.db.select('useraccounts', ('user',), (username,))
        return info[1]
