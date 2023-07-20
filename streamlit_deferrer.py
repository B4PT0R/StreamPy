"""
This module is used to defer streamlit module calls/context managers/outputs, each being encoded has a special helper object containing all the required information to actualy deal with it later.
The logic of this module is pretty intricate so let me attempt to clarify it. 
The main object of this module is the st_deferrer class.
It is meant to stand as a "deferred" version of the streamlit module.
For example, you may declare:
    std=st_deferrer()
and then make streamlit calls with it as you would with the steamlit module:
    std.write("hello")
but, here, the write widget won't be rendered directly.
Instead, std will create a st_callable object with .name='write' and .args=("hello",) and append it to its queue. That's pretty much it.
You may pile this way other streamlit calls, and each will be encoded as st_objects and piled in the queue, on top of previous ones.
Only when the user calls std.refresh() will every object in the queue be "executed" in order, from first to last (the callable 'write' from streamlit module will be passed argument "hello" and be actualy called, thus rendering the widget on screen). 
This way you may postpone streamlit widgets rendering.
The tricky part is implement context managment and outputs correctly...
Let's see outputs first.
For instance, you may want to write:
    txt=std.text_input("Enter text here:")
Here std will similarly create a st_callable object with .name='text_input' and .args=("Enter text here:",) and pile it to its queue.
steamlit.text_input is supposed to return a value when called (the text content of the widget).
But this "widget" only exists in an encoded form in std, namely a st_callable for now, and has not been rendered yet, so there in no text to be returned!
Therefore we must make std return something named txt. Something that will hold the future text content of the future text_input widget.
This is what the st_output class is for. It is basicaly a placeholder object, that will receive the text content of the widget as soon as it becomes available.
It's .value property will allow to access this text content in due time, but will be None until the widget is rendered and the text content actualy exists.
There is more to it, but let's leave that for now.
Second tricky thing: implement context management coherently.
For instance you may want to write:
    with std.empty():
        std.write("Hello")
The output returned by std.empty() must terefore be usable as a context manager (implement __enter__ and __exit__ methods adequately).
Any st_object must as well have a memory of this context to be able to take it into account at the moment of rendering...
That's what the .context attribute and the ctx context manager (used at rendering time) are for.

Things become even trickier when having to handle syntaxes such as :
    c1,c2=std.columns(2)
    with c1:
        std.write("column1")
    with c2:
        std.write("column2")
But it's basicaly a generalization of the first two examples, except we need to unpack 2 st_outputs after the call of std.columns.
That's why some st_callables must implement an __iter__ method (to allow unpacking of the outputs).
Each st_output object (c1,c2) must also receive it's value (an actual streamlit column) from the same callable at rendering time. 

Some other streamlit syntaxes such as :
    with std.sidebar:
        #do something
or,
    e=std.empty()
    e.write("hello")
require further logic : implementing property-like syntax via the st_property object in the first, and __getattr__  method for st_outputs in the second.

Some special streamlit functions require special handling for a smooth integration in the console flow, such as:
    streamlit.column_config (which is supposed to return directly so that its result can be passed as argument immediately)
    streamlit.spinner & streamlit.progress (must be executed while the python code is running : st_direct_exec_callables)
    streamlit.balloons & streammlit.snow (to avoid having balloons/snow appearing on screen at every refresh : st_one_shot_callables are only rendered one time)

The st_deferrer.stream method is here to help with rendering widgets in real-time while they are piled by the python interpreter running in a separate thread.

For convenience I added a KeyManager class allowing to automate widget key generation to avoid DuplicateWidgetID errors. 

Another nice feature is, once a queue has been constituted, in can be serialized using jsonpickle and saved in a file to serve as a template.
Useful to save/load parts of your app, and reuse them later in other projects.  

Well, I hope these explanations will help clarify a bit the intent of the code bellow.
This is for sure one of the most challenging coding task I personaly encountered at my humble level.
I don't pretend to be an experimented python developer, and I'm sure there are lots of ways this code can be improved.
All this is still a work in progress but functionning enough to handle most common streamlit syntaxes and almost all widgets in the console.
I guess it's a bit of a hack that extends streamlit possibilities slightly beyond what they were initialy meant to be.
Especialy when dealing with interactive rendering and threads (a thread fills the std pile, another calls std.stream to render the widgets).
I invit brave developers amongst readers to help me improve it, as I intuit it can become a very useful feature for streamlit users.
I also hope that some streamlit developers, with their hindsight on internal streamlit functionning, will take a look at it and hopefuly give me some feedback and hints on how to make it more robust and efficient at encapsulating streamlit's logic.
All this being said,
Happy coding! 
"""

import streamlit as st
from streamlit.errors import DuplicateWidgetID
from streamlit_ace import st_ace
from contextlib import contextmanager
import jsonpickle as jsp
import logging
import time
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("log")
log.setLevel(logging.DEBUG)

def wait_until(condition):
    while not condition:
        time.sleep(0.005)

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
            if attr=='ace':
                return st_ace
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
            self.append(obj)
            return obj
        elif attr in ['spinner','progress']:
            obj=st_direct_exec_callable(self,attr,context=self.current_context)
            return obj
        elif attr in ['sidebar']:
            obj=st_property(self,attr,context=self.current_context)
            self.append(obj)
            return obj
        elif attr in ['column_config']:
            return st.column_config
        else:
            obj=st_callable(self,attr,context=self.current_context)
            self.append(obj)
            return obj

    def append(self,obj):
        self.pile.append(obj)
        if self.mode=='streamed':
            wait_until(len(self.pile)==0)

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
