import streamlit as st
from components import ImportComponents
COMPONENTS=ImportComponents()
from streamlit.errors import DuplicateWidgetID
from contextlib import contextmanager
import jsonpickle as jsp
import logging
import time
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("log")
log.setLevel(logging.DEBUG)


class KeyManager:
    def __init__(self):
        self.keys=[]

    def gen_key(self):
        i=0
        while ((key:='key_'+str(i)) in self.keys):
            i+=1
        self.keys.append(key)
        return key
    
    def dispose(self,key):
        if key in self.keys:
            self.keys.remove(key)


def isiterable(obj):
    try:
        it=iter(obj)
    except:
        return False
    else:
        if isinstance(obj,str):
            return False
        else:
            return True

def st_map(attr):
        try:
            return getattr(st,attr)
        except:
            if attr in COMPONENTS:
                return COMPONENTS[attr]
            else:
                raise Exception(f"Unknown streamlit attribute: {attr}")

@contextmanager
def ctx(context):
    if not context==None:
        if isinstance(context,(st_callable,st_one_shot_callable)):
            with st_map(context.name)(*context.args,**context.kwargs):
                yield
        elif isinstance(context,(st_output,st_property,st_direct_exec_callable)):
            with context.value:
                yield
    else:
        yield None


def call(callable):
    results=st_map(callable.name)(*callable.args,**callable.kwargs)
    if not results is None:
        if isiterable(results):
            for i,result in enumerate(results):
                if i<len(callable.outputs):
                    callable.outputs[i].value=result
        else:
            callable.outputs[0].value=results

class st_object:

    def __init__(self,deferrer,context=None):
        self.deferrer=deferrer
        self.context=context

    def __enter__(self):
        self.context = self.deferrer.current_context
        self.deferrer.current_context = self
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deferrer.current_context = self.context

class st_executable(st_object):

    def __init__(self,deferrer,name,context=None):
        st_object.__init__(self,deferrer,context)
        self.name=name
        self.has_exec=False

    def exec(self):
        with ctx(self.context):
            call(self)
        self.has_exec=True

class st_callable(st_executable):
    def __init__(self,deferrer,name,context=None):
        st_executable.__init__(self,deferrer,name,context)
        self.iter_counter=0
        self.args=None
        self.kwargs=None
        self.outputs=[]

    def __call__(self,*args,**kwargs):
        self.args=args
        self.kwargs=kwargs
        if self.name in ['columns','tabs']:
            return self
        else:
            obj=st_output(deferrer=self.deferrer,context=self.context)
            self.outputs.append(obj)
            self.deferrer.append(self)
            return obj

    def __iter__(self):
        return self

    def __next__(self):
        if self.iter_counter<len(self):
            obj=st_output(deferrer=self.deferrer,context=self.context)
            self.outputs.append(obj)
            self.iter_counter+=1
            return obj 
        else:
            self.iter_counter=0
            self.deferrer.append(self)
            raise StopIteration   

    def __len__(self):
        if isinstance(self.args[0],int) and self.args[0]>1:
            return self.args[0]
        elif isiterable(self.args[0]) and len(self.args[0])>1:
            return len(self.args[0])
        else:
            return 1

class st_output(st_object):

    def __init__(self,deferrer,context):
        st_object.__init__(self,deferrer,context)
        self.value=None

    def __getattr__(self,attr):
        obj=st_callable(self.deferrer,attr,context=self)
        self.deferrer.append(obj)
        return obj
    
class st_property(st_executable):

    def __init__(self,deferrer,name,context=None):
        st_executable.__init__(self,deferrer,name,context)
        self.value=None
        self.deferrer.append(self)

    def __getattr__(self,attr):
        obj=st_callable(self.deferrer,attr,context=self)
        self.deferrer.append(obj)
        return obj


class st_direct_exec_callable:

    def __init__(self,deferrer,name,context):
        self.deferrer=deferrer
        self.name=name
        self.context=context

    def __call__(self,*args,**kwargs):
        return st_map(self.name)(*args,**kwargs)
    

class st_one_shot_callable(st_executable):

    def __init__(self,deferrer,name,context=None):
        st_executable.__init__(self,deferrer,name,context)
        self.outputs=[]


    def __call__(self,*args,**kwargs):
        self.args=args
        self.kwargs=kwargs
        obj=st_output(deferrer=self.deferrer,context=self.context)
        self.outputs.append(obj)
        self.deferrer.append(self)
        return obj

    def exec(self):
        super().exec()
        self.deferrer.remove(self)

class st_deferrer:
    
    def __init__(self,key_manager=None,mode='static'):
        if key_manager==None:
            self.key_manager=KeyManager()
        else:
            self.key_manager=key_manager
        self.mode=mode
        self.queue=[]
        self.pile=[]
        self.session_state=st.session_state
        self.current_context=None
    
    def gen_key(self):
        return self.key_manager.gen_key()

    def __getattr__(self,attr):
        if attr in ['balloons','snow','experimental_rerun']:
            obj=st_one_shot_callable(self,attr,context=self.current_context)
            return obj
        elif attr in ['spinner','progress']:
            obj=st_direct_exec_callable(self,attr,context=self.current_context)
            return obj
        elif attr in ['sidebar']:
            obj=st_property(self,attr,context=self.current_context)
            return obj
        elif attr in ['column_config']:
            return st.column_config
        else:
            obj=st_callable(self,attr,context=self.current_context)
            return obj

    def append(self,obj):
        self.pile.append(obj)
        if self.mode=='streamed':
            while len(self.pile)>0:
                time.sleep(0.005)

    def remove(self,obj):
        if obj in self.pile:
            self.pile.remove(obj)
        if obj in self.queue:
            self.queue.remove(obj)

    def stream(self):
        if not len(self.pile)==0:
            obj=self.pile.pop(0)
            if not obj.has_exec:
                #log.debug("In stream : "+obj.name)
                try:
                    obj.exec()
                except DuplicateWidgetID:
                    pass
            self.queue.append(obj)

    def refresh(self):
        for obj in self.queue:
            if not obj.has_exec:
                #log.debug("In refresh : "+obj.name)
                try:
                    obj.exec()
                except DuplicateWidgetID:
                    pass
        while len(self.pile)>0:
            self.stream()
        

    def reset(self):
        for obj in self.queue:
            obj.has_exec=False

    def clear(self):
        self.queue=[]
        self.pile=[] 

    def dump(self):
        queue=self.queue.copy()
        encoded_queue=jsp.encode(queue)
        return encoded_queue
    
    def load(self,serialized_queue):
        decoded_queue=jsp.decode(serialized_queue)
        self.queue=decoded_queue
