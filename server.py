#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#Licensed by Alan Laughter under the GPL v3

import web
from pprint import pprint

import sys
import os
import time
import re
import json
import uuid
import urllib
import posixpath
import shutil

from utilities import dbmkr, login
from utilities.data import chomp, is_number, zero_out, log

web.config.debug = False
testing = True

urls = ("/" ,"webPage", "/(.+)" ,"webPage")

login_dbase = login.session_controller("accounts")

Server_config = open(os.path.join("config","sites_available"),"r").read().strip("\r").split("\n")

site_databases = {}

def new_site(domain):
    os.makedirs(domain)
    os.makedirs(os.path.join(domain, "pages"))
    os.makedirs(os.path.join(domain, "static", "style"))
    shutil.copy(os.path.join("config", "admin.html"), os.path.join(line, "pages"))
    shutil.copy(os.path.join("config", "large.css"), os.path.join(line, "static", "style"))
    shutil.copy(os.path.join("config", "mob.css"), os.path.join(line, "static", "style"))

for line in Server_config:
    if line != '':
        if not os.path.exists(line):
            new_site(line)
        site_databases[line] = dbmkr.database(os.path.join(line, "database"))

#testdb = dbmkr.database("test")

class MyApplication(web.application):
    def reb(self, port=80, *middleware):
        func = self.wsgifunc(*middleware)
        return web.httpserver.runsimple(func, ('0.0.0.0',port))

def notfound():
    return web.notfound("404 not found")

app = MyApplication(urls, globals())
app.notfound = notfound

class StaticMiddleware:
    """WSGI middleware for serving static files."""
    def __init__(self, app, prefix='/static/'):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        path = self.normpath(path)

        self.domain = environ["HTTP_HOST"].split(".",1)[1]

        if path.startswith(self.prefix):
            print self.domain
            print path
            environ["PATH_INFO"] = self.domain + path
            print environ["PATH_INFO"]
            return web.httpserver.StaticApp(environ, start_response)
        else:
            return self.app(environ, start_response)

    def normpath(self, path):
        path2 = posixpath.normpath(urllib.unquote(path))
        if path.endswith("/"):
            path2 += "/"
        return path2
    

class webPage:
    def __init__(self):
        self.input=web.input()

        self.domain = web.ctx.env["HTTP_HOST"].split(".",1)[1]
        self.var = {}

        if len(login_dbase.get_users()) == 0:
            self.var["perm"] = 6
        else:
            try:
                self.cookie = web.cookies().get(self.domain + "cookie").split(":",1)
                self.var["perm"] = login_dbase.session_out(self.cookie[0],self.cookie[1])

            except:
                self.var["perm"] = 0
        print self.var["perm"]

    def __set_cookie__(self, cookiename, name):
        expiration = "%.0f" % (time.time() + 604800)
        session_code = str(uuid.uuid4().hex).strip(":")
        login_bit = session_code + ":" + expiration
        login_dbase.session_in(name, login_bit)

        full_bit = unicode(name + ":" + login_bit)
        web.setcookie(cookiename, full_bit, 604800)

    def GET(self, FullURL = "index"):
        self.var["db"] = site_databases[self.domain].select_all(FullURL)
        self.var["query"] = web.input
        self.var["pages"] = os.listdir(os.path.join(self.domain, "pages"))
        #print self.var["query"]["id"]
        if testing:
            page = web.template.frender(os.path.join(self.domain, "pages", FullURL + ".html"))
            return page(self.var)
        else:
            try:
                page = web.template.frender(os.path.join(self.domain, "pages", FullURL + ".html"))
                try:
                    return page(self.var)
                except TypeError as e:
                    print "Type Error({0}): {1}".format(e.errno, e.strerror)
                    return page()
            except:
                print "unexpected Error:", sys.exc_info()[0]
                return notfound()

 
    def POST(self, FullURL = "index"):

        if "username" in self.input.keys():
            username = self.input["username"]
            password = self.input["password"]
            if login_dbase.check_user(username, self.domain,password):
                self.__set_cookie__(self.domain + "cookie",username)
            raise web.seeother(FullURL)

        elif "newuser" in self.input.keys() and self.var["perm"] >= 4:
            username = self.input["user"]
            password = self.input["password"]
            site = self.input["site"]
            if site not in Server_config:
                open(os.path.join("config","sites_available"),"w").write(line + "\n")
            permissions = self.input["permissions"]
            login_dbase.new_user(username, site, permissions,password)
            raise web.seeother(FullURL)

        elif "fileupload" in self.input.keys() and self.var["perm"] >= 4:

            pages = ["html", "xml", "xhtml"]
            style = ["css", "js"]
            images= ["png", "jpg", "gif", "jpeg", "tiff", "rif",
                     "bmp", "ppm", "pbm", "pnm", "webp", "webm",
                     "bpg", "ico" ]

            x = web.input(myfile={})
            if 'myfile' in x:
                filepath=x.myfile.filename.replace('\\','/')
                filename=filepath.split('/')[-1]
                filetype = filename.split(".")[1]
                if filetype.lower() in pages:
                    filedir = "pages"
                elif filetype.lower() in style:
                    filedir = os.path.join("static","style")
                elif filetype.lower() in images:
                    filedir = os.path.join("static","images")
                else:
                    filedir = os.path.join("static","files")
                if not os.path.exists(os.path.join(self.domain, filedir)):
                    os.makedirs(os.path.join(self.domain, filedir))
                fout = open(os.path.join(self.domain, filedir, filename), 'w')
                fout.write(x.myfile.file.read())
                fout.close()
            raise web.seeother(FullURL)
        elif "page_submission" in self.input.keys() and self.var["perm"] >= 4:
            items = self.input.keys()
            items.remove("page_submission")
            print site_databases[self.domain].tables()
            if FullURL not in site_databases[self.domain].tables():
                table_items = ""
                for item in range(len(items)):
                    if isinstance(self.input[items[item]], basestring):
                        table_items += "%s TEXT ," % (items[item])
                    elif isinstance(self.input[item], int):
                        table_items += "%s INT ," % (items[item])
                    else:
                        table_items += "%s BLOB ," % (items[item])
                table_items += "date INT"
                print table_items
                print site_databases[self.domain].create(FullURL, table_items)
            columns = []
            for key in items:
                columns.append(self.input[key])
            columns.append("%.0f" % (time.time()))
            site_databases[self.domain].insert(FullURL, columns)
            raise web.seeother(FullURL)
        elif "getpage" in self.input.keys() and self.var["perm"] >= 4:
            self.var["page"] = [self.input["page"],open(os.path.join(self.domain, "pages", self.input["page"])).read()]
            self.var["db"] = site_databases[self.domain].select_all(FullURL)
            self.var["query"] = web.input
            self.var["pages"] = os.listdir(os.path.join(self.domain, "pages"))
            #print self.var["query"]["id"]
            if testing:
                page = web.template.frender(os.path.join(self.domain, "pages", FullURL + ".html"))
                return page(self.var)
            else:
                try:
                    page = web.template.frender(os.path.join(self.domain, "pages", FullURL + ".html"))
                    try:
                        return page(self.var)
                    except TypeError as e:
                        print "Type Error({0}): {1}".format(e.errno, e.strerror)
                        return page()
                except:
                    print "unexpected Error:", sys.exc_info()[0]
                    return notfound()
            
        elif "pageupdate" in self.input.keys() and self.var["perm"] >= 4:
            open(os.path.join(self.domain, "pages", self.input["pagename"]), 'w').write(self.input["editor"])
            raise web.seeother(FullURL)
        else:
            raise web.seeother(FullURL)
            


if __name__ == "__main__":
    wsgifunc = app.wsgifunc()
    wsgifunc = StaticMiddleware(wsgifunc)
    wsgifunc = web.httpserver.LogMiddleware(wsgifunc)
    server = web.httpserver.WSGIServer(("0.0.0.0", 80), wsgifunc)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()


