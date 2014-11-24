import web
import sys, os, time, re, json

#data handling functions

def chomp(s):
    return s[:-1] if s.endswith('\n') else s


def is_number(self,s):
    try:
        float(s)
        return True
    except:
        return False

def zero_out(self, fill, integer):
    return '%0*d' % (fill, integer)

def log(info):
    with open(os.path.join('config','log'),'a') as log:
        log.write(info + '\n')
    pass
