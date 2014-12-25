class _var:
    #class ConstError(TypeError): pass
    def __setattr__(self,name,value):
        #if self.__dict__.has_key(name):
        #    del self.__dict__[name]
        self.__dict__[name]=value
import sys
sys.modules[__name__]=_var()
