#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#Licensed by Alan Laughter under the GPLv3

import web, sys, os, time, uuid, hashlib
from pprint import pprint

import sqlite3 as sql

class database(object):
    """ This is the database handler class
        A new object is to be created for each database
        tables are to be made and handled by pre-written static strings

    """
    def __init__(self, current_database):
        """This connects to the database
        """
        self.con = sql.connect(current_database, check_same_thread=False)
        self.StatCom = {"create":"CREATE TABLE IF NOT EXISTS %s (%s)",
                        "drop"  :"DROP TABLE IF EXISTS %s"           ,
                        "new"   :"CREATE TABLE %s (%s)"              ,
                        "insert":"INSERT INTO %s VALUES (%s)"        ,
                        "select":"SELECT * FROM %s %s"               ,
                        "selmax":"SELECT MAX(%s) from %s"            ,
                        "delete":"DELETE FROM %s WHERE %s=?"         ,
                        "update":"UPDATE %s SET %s WHERE %s = ?"     ,
                        "tables":"SELECT name FROM sqlite_master where type='table';"}

    def __sanitize__(self, s, errors="strict"):
        """ This sanitizes any user created information
        """
        #copied from https://stackoverflow.com/questions/6514274/
        #how-do-you-escape-strings-for-sqlite-table-column-names-in-python
        try:
            encodable = s.encode("utf-8",errors).decode("utf-8")

            nul_index = encodable.find("\x00")

            if nul_index >= 0:
                error = UnicodeEncodeError("NUL-terminated utf-8", encodable,
                    nul_index, nul_index + 1, "NUL not allowed")
                error_handler = codecs.lookup_error(errors)
                replacement, _ = error_handler(error)
                encodable = encoable.replace("\x00",replacement)

            return encodable.replace("\"","\"\"")
        except:
            return s

    def __parameters__(self, length):
        return ",".join(["?"] * length)
    
    def __get_fields__(self, table):
        table = "`%s`" % (table)
        with self.con:
            cur = self.con.cursor()
            command = "SELECT * FROM %s" % (table,)
            rows = cur.execute(command)
        return rows            

    def __execute__(self, command):
        try:
            with self.con:
                cur = self.con.cursor()
                cur.execute(command)
            return True
        except:
            return False

    def tables(self):
        try:
            with self.con:
                cur = self.con.cursor()
                cur.execute(self.StatCom["tables"])
            return cur.fetchall()[0]
        except:
            return []

    def create(self, table, columns):
        table = "`%s`" % (table)

        """ this creates tables if they do not exist
            it makes new databases and reconnects with old ones
        """
        
        
        columns = self.__sanitize__(columns)
        with self.con:
            cur = self.con.cursor()
            if table not in self.tables():
                print self.StatCom["create"] % (table, columns)
                cur.execute(self.StatCom["create"] % (table, columns))
                return True
            return False
        #except:
        #    return False

    def recreate(self, table, columns):
        table = "`%s`" % (table)

        """ This destroys old databases and recreates them
        """
        try:
            columns = self.__sanitize__(columns)
            with self.con:
                cur = self.con.cursor()
                self.drop(table)
                cur.execute(self.StatCom["new"] % (table, columns))
            return True
        except:
            return False

    def insert(self, table, columns):
        table = "`%s`" % (table)

        """ Insert into columns, after it sanitizes the inputs            
        """
        try:
            new_columns = []
            #for column in columns:
            #    new_columns.append(self.__sanitize__(column))
            #columns = tuple(new_columns)
            insertion_string = self.StatCom["insert"] % (table, 
                self.__parameters__(len(columns)))
            with self.con:
                cur = self.con.cursor()
                cur.execute(insertion_string, columns)
            return True
        except:
            return False

    def selmax(self, table, column):
        table = "`%s`" % (table)

        #try:
        with self.con:
            cur = self.con.cursor()
            command = self.StatCom["selmax"] % (table, column)
            cur.execute(command)
            row = cur.fetchall()
            del cur
        return row
        #except:
        #    return []

    def select_all(self, table):
        table = "`%s`" % (table)

        try:
            with self.con:
                cur = self.con.cursor()
                command = "SELECT * FROM %s" % (table)
                cur.execute(command)
                rows = cur.fetchall()
            return rows
        except:
            return []

    def select(self, table, keys, keywords):
        table = "`%s`" % (table)

        """This returns information from the database in the 
            form of a list of tuples
        """
        try:
            #keywords = self.__sanitize__(keywords)
            with self.con:
                cur = self.con.cursor()

                selections = "WHERE %s=? " % keys[0]
                for key in range(0,len(keys)-1):
                    selections += "and %s=? " % (keys[key+1])
                command = self.StatCom["select"] % (table, selections)
                print command
                cur.execute(command, keywords)
                row = cur.fetchall()
                del cur                    
            return row
        except:
            return []

    def query_first(self, table, key, keyword):
        table = "`%s`" % (table)

        try:
            return self.select(table, key, keyword)[0]
        except:
            return []

    def query_last(self, table, key, keyword):
        table = "`%s`" % (table)

        rows = self.select(table, key, keyword)
        return rows[len(rows)-1]

    def drop(self, table):
        table = "`%s`" % (table)

        """this drops whole tables"""
        try:
            with self.con:
                cur = self.con.cursor()
                cur.execute(self.StatCom["drop"] % (table))
            return True
        except:
            return False

    def delete(self, table, key, keyword):
        table = "`%s`" % (table)

        try:
            with self.con:
                cur = self.con.cursor()
                print self.StatCom["delete"] % (table, key)
                cur.execute(self.StatCom["delete"] % (table, key), keyword)
            return True
        except:
            return False
    










