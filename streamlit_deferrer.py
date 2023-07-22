import streamlit as st
from components import COMPONENTS,ATTRIBUTES_MAPPING
# Imports custom components and a mapping of streamlit methods/attributes onto the appropriate deferred version
from streamlit.errors import DuplicateWidgetID
from contextlib import contextmanager
#import jsonpickle as jsp # optionaly implements serialization of the deferrer's queue (to save queue templates for instance)
import logging
import time
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("log")
log.setLevel(logging.DEBUG)

def instantiate(class_name, *args, **kwargs):
    cls = globals()[class_name] 
    return cls(*args, **kwargs)

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

class KeyManager:
# A simple widget key manager
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

def st_map(attr):
# Maps attributes keys to streamlit built-in or custom components objects
        try:
            return getattr(st,attr)
        except:
            if attr in COMPONENTS:
                return COMPONENTS[attr]
            else:
                raise Exception(f"Unknown streamlit attribute: {attr}")

@contextmanager
def ctx(context):
# Context manager to open/close streamlit objects as context for others at rendering time
    if not context==None:
        if isinstance(context,(st_callable,st_one_shot_callable)):
            with st_map(context.name)(*context.args,**context.kwargs):
                yield
        elif isinstance(context,(st_output,st_property,st_direct_callable)):
            if not context.value is None:
                with context.value:
                    yield
            else:
                yield None
        else:
            yield None
    else:
        yield None

def render(callable):
# Renders deferred widgets by calling streamlit / third party components and captures outputs if any
    results=st_map(callable.name)(*callable.args,**callable.kwargs)
    if not results is None:
        if isiterable(results):
            for i,result in enumerate(results):
                if i<len(callable.outputs):
                    callable.outputs[i].value=result
        else:
            callable.outputs[0].value=results

class st_object:
# Base class for deferred version of streamlit objects
# Makes them usable as context managers for other objects
    def __init__(self,deferrer,context=None):
        self.deferrer=deferrer
        self.context=context

    def __enter__(self):
        self.context = self.deferrer.current_context
        self.deferrer.current_context = self
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deferrer.current_context = self.context

class st_renderable(st_object):
# Base class for objects that need rendering
    def __init__(self,deferrer,name,context=None):
        st_object.__init__(self,deferrer,context)
        self.name=name
        self.has_rendered=False

    def render(self):
        with ctx(self.context):
            render(self)
        self.has_rendered=True

class st_callable(st_renderable):
# For most common callable objects like st.write, st.button, st.text_input...
    def __init__(self,deferrer,name,context=None):
        st_renderable.__init__(self,deferrer,name,context)
        self.iter_counter=0
        self.args=None
        self.kwargs=None
        self.outputs=[]

    def __call__(self,*args,**kwargs):
        self.args=args
        self.kwargs=kwargs
        obj=st_output(deferrer=self.deferrer,context=self.context)
        self.outputs.append(obj)
        self.deferrer.append(self) #An object is appended to the pile only when all information required to render it and route its outputs is available
        return obj

class st_unpackable_callable(st_renderable):
    # For unpackable objects like st.columns, st.tabs...
    def __init__(self,deferrer,name,context=None):
        st_renderable.__init__(self,deferrer,name,context)
        self.iter_counter=0
        self.args=None
        self.kwargs=None
        self.outputs=[]

    def __call__(self,*args,**kwargs):
        self.args=args
        self.kwargs=kwargs
        return self

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
            self.deferrer.append(self) #An object is appended to the pile only when all information required to render it and route its outputs is available
            raise StopIteration   

    def __len__(self):
        if isinstance(self.args[0],int) and self.args[0]>1:
            return self.args[0]
        elif isiterable(self.args[0]) and len(self.args[0])>1:
            return len(self.args[0])
        else:
            return 1

class st_output(st_object):
    # Placeholder object for outputs of callables
    def __init__(self,deferrer,context):
        st_object.__init__(self,deferrer,context)
        self.value=None

    def __getattr__(self,attr):
        if attr in ATTRIBUTES_MAPPING:
            obj=instantiate(ATTRIBUTES_MAPPING[attr],self.deferrer,attr,context=self)
            self.deferrer.append(obj)
            return obj
        else:
            raise AttributeError
    
class st_property(st_renderable):
    # For property-like objects such as st.sidebar
    def __init__(self,deferrer,name,context=None):
        st_renderable.__init__(self,deferrer,name,context)
        self.value=None
        self.deferrer.append(self)

    def __getattr__(self,attr):
        if attr in ATTRIBUTES_MAPPING:
            obj=instantiate(ATTRIBUTES_MAPPING[attr],self.deferrer,attr,context=self)
            return obj
        else:
            raise AttributeError



class st_direct_callable:
    # Resolves streamlit call directly without appending to the queue
    # useful for st.spinner, st.progress...
    def __init__(self,deferrer,name,context):
        self.deferrer=deferrer
        self.name=name
        self.context=context
        self.value=None

    def __call__(self,*args,**kwargs):
        self.value=st_map(self.name)(*args,**kwargs)
        return self.value

def st_direct_property(deferrer,name,context):
    # Returns a streamlit property directly without appending to the queue
    # Useful for st.column_config, st.session_state...
    return st_map(name)    

class st_one_shot_callable(st_renderable):
    # For callables that need to be rendered only once
    # such as st.balloons, st.snow...
    def __init__(self,deferrer,name,context=None):
        st_renderable.__init__(self,deferrer,name,context)
        self.outputs=[]


    def __call__(self,*args,**kwargs):
        self.args=args
        self.kwargs=kwargs
        obj=st_output(deferrer=self.deferrer,context=self.context)
        self.outputs.append(obj)
        self.deferrer.append(self)
        return obj

    def render(self):
        super().render()
        self.deferrer.remove(self)

class st_deferrer:
    """
    Main class, mimicking the streamlit module behaviour in a deferred manner  
    Wraps streamlit attrs into deferred versions
    Holds pile/queue of deferred objects
    Renders all deferred objects in the queue on call to refresh, or streams them one by one in real-time from the pile
    Keeps the current context required for widget rendering 
    """

    def __init__(self,key_manager=None,mode='static'):
        if key_manager==None:
            self.key_manager=KeyManager()
        else:
            self.key_manager=key_manager
        self.mode=mode
        self.queue=[]
        self.pile=[]
        self.current_context=None
    
    def gen_key(self):
        return self.key_manager.gen_key()

    def __getattr__(self,attr):
        #instantiate the adequate st_object subtype corresponding to the attribute according to ATTRIBUTES_MAPPING
        #Refer to the components.py module to see how ATTRIBUTES_MAPPING is defined
        if attr in ATTRIBUTES_MAPPING:
            obj=instantiate(ATTRIBUTES_MAPPING[attr],self,attr,context=self.current_context)
            return obj #The object itself will deal with its appending to the deferrer's queue once all information required to render it is available (such as call arguments, outputs etc...)
        else:
            raise AttributeError

    def append(self,obj):
        #appends an object to the deferrer's pile
        self.pile.append(obj)
        if self.mode=='streamed':
            #Makes sure a widget appended to the pile is rendered before continuing
            #The 'streamed' mode is useful when working with threads
            while len(self.pile)>0:
                time.sleep(0.001)

    def remove(self,obj):
        #removes an object from the deferrer's pile/queue (useful for st_one_shot_callable objects)
        if obj in self.pile:
            self.pile.remove(obj)
        if obj in self.queue:
            self.queue.remove(obj)

    def stream(self):
        #renders the first object found in the pile, then moves it to the queue
        #useful for real-time rendering when working with threads
        if not len(self.pile)==0:
            obj=self.pile.pop(0)
            if not obj.has_rendered:
                try:
                    obj.render()
                except DuplicateWidgetID:
                    #Some widgets take several mainloop turns to be consumed by streamlit and leave screen
                    #This avoids to attempt rerendering them while they are still active  
                    pass
            self.queue.append(obj)

    def refresh(self):
        #renders every object in the queue (to refresh the whole app display), then renders objects still in the pile, if any.
        for obj in self.queue:
            if not obj.has_rendered:
                try:
                    obj.render()
                except DuplicateWidgetID:
                    pass
        while len(self.pile)>0:
            self.stream()
        

    def reset(self):
        #Supposed to be called at the beginning of the streamlit main app script (understood as the mainloop of the app)
        #widgets need to be rendered every turn of the mainloop, otherwise these widgets will disappear from the app's display.
        #This resets all objects in the queue to a non-rendered state so that the next call to refresh will render them all again
        for obj in self.queue:
            obj.has_rendered=False

    def clear(self):
        self.queue=[]
        self.pile=[] 
"""
    #optionaly implements serialized dumps/loads of the queue
    def dump(self):
        queue=self.queue.copy()
        serialized_queue=jsp.encode(queue)
        return serialized_queue
    
    def load(self,serialized_queue):
        decoded_queue=jsp.decode(serialized_queue)
        self.queue=decoded_queue
"""