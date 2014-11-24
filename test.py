#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import web

import sqlite3 as sql

#use database to retrieve entries, webpages should be served based on what url is used to access the server

con = sql.connect('sites.db')

with con:
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS Websites")
    cur.execute("CREATE TABLE IF NOT EXISTS Websites(sitename TEXT, body TEXT, rand INT)")
    cur.execute("INSERT INTO Websites Values('localhost','this is laughware computers', 1)")
    cur.execute("INSERT INTO Websites Values('rpchan','this is prchan smartassery', 2)")
    cur.execute("INSERT INTO Websites Values('transpositivity','no I''m not', 4)")
    
urls = ("/","index", "/(.+)", "test")

class MyApplication(web.application):
    def run(self, port=80, *middleware):
        func = self.wsgifunc(*middleware)
        return web.httpserver.runsimple(func, ('0.0.0.0', port))

class webPage:
    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def GET(self, url_extension = "home"):
        self.url_extension = url_extension
        print self.url_extension
        log = open('./log','w')
        #for x in web.ctx():
        #        print x
        print web.ctx.get('host').split(":")[0]
        return self.page()


    def page(self):
        pass

class index(webPage):
    def __init__(self):
        self.con = sql.connect('sites.db')
        self.method = web.ctx.get('method')
        print self.method
    def page(self):
        try:
            page = web.template.frender("templates/" + "{0}".format(self.url_extension) + "html")
        except:
            page = "derp"
        #page = "derp"
        #keys = web.ctx.keys()
        #for x in keys:
        #    print web.ctx[x]
        """
        with self.con:
            cur = self.con.cursor()
            print web.ctx.get('method')
            cur.execute("SELECT * FROM Websites WHERE sitename = '%s'" % (web.ctx.get('host').split(":")[0]))
            #cur.execute("SELECT * FROM Websites")
            rows = cur.fetchone()
            print rows
        page = rows[1]
        del rows"""
        return page()

class test(webPage):
    def page(self):
        try:
            page = web.template.frender("templates/" + "{0}".format(self.url_extension) + ".html")
        except:
            page = "derp"
        return page()


app = MyApplication(urls, globals())

if __name__ == "__main__":
        app.run(port = 8080)




