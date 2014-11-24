#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#Licensed by Alan Laughter under the GPL v3

#3rd party imports
import web
from pprint import pprint

#built-in imports
import sys
import os
import time
import re
import json
import uuid

#personal imports
from utilities import dbmkr, login
from utilities.data import chomp, is_number, zero_out, log
from defpages import admin_login, admin_panel, admin_post

#retrieving the domain names
#the domain must be a fully qualified domain name
config_lines = open(os.path.join("config","sites_available"),"r"
    ).read().strip("\r").split("\n")

#website databases and login databases
site_databases = {}
site_login = {}

#generating the default configuration
for line in config_lines:
    if line != "":
        #creates the database for the website if it doesn't exist
        site_databases[line] = dbmkr.database(os.path.join
            ("config", line))

        #create the table for the pages if it doesn't exist
        #and assigns T/F value to is_made
        #the table has the columns page method perm keywords content cookie
        #example: index GET 0 {'login':['user','pass']} "<html>" "cookiedough"
        is_made = site_databases[line].create("pages", "page TEXT, \
            method TEXT, perm TINYINT, keywords TEXT, content TEXT, \
            cookie TEXT")

        #if the table wasn't made it creates the default webpages
        if not is_made:

            site_databases[line].insert("pages", ["index", "GET" , 0,
                "None", "No page added yet", "cookeddough"])

            site_databases[line].insert("pages", ["admin", "GET" , 0, 
                "None", admin_login, "cookeddough"])

            site_databases[line].insert("pages", ["admin", "POST", 0, 
                json.dumps({'type':'login','cookie':'cookeddough',
                'keywords':['username','password']}), admin_post, 
                "cookeddough"])

            site_databases[line].insert("pages", ["admin", "GET" , 3, 
                "None", admin_panel, "cookeddough"])
        #connects the login object to the site database
        site_login[line] = login.session_controller(
            os.path.join("config", line))

        #adds, if doesn't exist, a default admin user
        site_login[line].new_user("admin",3,"password")

urls = ("/" ,"pages", "/(.+)" ,"pages")

class MyApplication(web.application):
    def reb(self, port=80, *middleware):
        func = self.wsgifunc(*middleware)
        return web.httpserver.runsimple(func, ('0.0.0.0',port))

#404 page
def notfound():
    with open(os.path.join('config','log') , 'a') as log:
        log.write(web.ctx.get('host').split(':')[0] + '\n')
    with open(os.path.join('config','bans'),'r') as bans:
        if web.ctx['ip'] in bans.read():
            raise web.seeother('/banned')
    return web.notfound("404 not found")

#the actual webserver application
class webPage:
    def __init__(self):
        #gets any web input, post forms and the like
        self.input = web.input()

        #gets the domain name by stripping the link of non-esential information
        self.domain = re.sub("https?://|www.","",web.ctx.get('host')
            ).split("/",1)[0]

        #gets the method 
        self.method = web.ctx.get('method')

        #creates the method handler pages based on the page prototype
        self.GET     = self.__Page_Front__
        self.POST    = self.__Page_Front__
        self.HEAD    = self.__Page_Front__
        self.PUT     = self.__Page_Front__
        self.DELETE  = self.__Page_Front__
        self.OPTIONS = self.__Page_Front__
        self.CONNECT = self.__Page_Front__

    #makes the method hander functions, it wont work without this, I don't know why
    def GET(    self, FullURL = "index"):
        pass
    def POST(   self, FullURL = "index"):
        pass
    def HEAD(   self, FullURL = "index"):
        pass
    def PUT(    self, FullURL = "index"):
        pass
    def DELETE( self, FullURL = "index"):
        pass
    def OPTION( self, FullURL = "index"):
        pass
    def CONNECT(self, FullURL = "index"):
        pass      

    #checks if the IP is banned using a file, needs to be a table in the database
    def __banned__(self):
        log(web.ctx.get('host').split(':')[0])
        banned_list = open(os.path.join('config','bans'),'r')
        if web.ctx['ip'] in banned_list.read():
            banned_list.close()
            return True
        else:
            banned_list.close()
            return False

    #sets a cookie according to the specifications
    #currently only allows different names, the time is set to one week
    #creates a session in the login object
    def __set_cookie__(self, cookiename, name):
        expiration = "%.0f" % (time.time() + 604800)
        session_code = str(uuid.uuid4().hex).strip(":")
        login_bit = session_code + ":" + expiration
        site_login[self.domain].session_in(name, login_bit)

        full_bit = unicode(name + ":" + login_bit)
        web.setcookie(cookiename, full_bit, 604800)

    #The webpage hander itself
    def __Page_Front__(self, FullURL = "index"):
        #if banned shows only ban
        if self.__banned__():
            raise web.seeother('/banned')

        #tries to retrieve the webpage, returns 404 otherwise
        try:
            #the fullurl is passed as an argument to the webpage
            self.URL = FullURL

            #retrieves all webpages matching the page and method currently used
            #it will have multiple pages if there are pages for different
            #permissions like  login page and the actual logged in page
            this_page = site_databases[self.domain].select("pages", 
                ("page", "method"), (self.URL,self.method))
            try:
                #tries to create a dictionary from the keywords if any
                arguments = json.loads(this_page[0][3])
            except:
                arguments = {}
    
            try:
                #creates a short list of the username and cookie session number
                self.info = web.cookies().get(this_page[0][5]).split(":",1)
            #uses that information to Qa1
                self.perm = site_login[self.domain].session_out(self.info[0]
                    , self.info[1])
            except:
                self.perm = 0
    
            print "self.perm =", self.perm
    
            if "type" in arguments.keys():
                if arguments['type'] == 'login':
                    #username and password are obtained from the keywords
                    #this is too locked in and needs to be locked in
                    username = self.input()[arguments['keywords'][0]]
                    password = self.input()[arguments['keywords'][1]]
                    #sets the login cookie if login credentials are correct
                    if site_login[self.domain].check_user(username,password):
                       self.__set_cookie__(arguments['cookie'],web.input()
                           [arguments['keywords'][0]])

            #gets the current page from the list of available pages
            #based on permissions
            current_page = []
            for page in this_page:
                if page[2] == self.perm:
                    current_page = page
                    break
            #templates the page so it can be used and then returns the page
            page = web.template.Template(current_page[4])
            return page()
        except:
            #404s the page if page retrival doesn't work
            return notfound()


app = MyApplication(urls, globals())
app.notfound = notfound

if __name__ == "__main__":
    app.run()
