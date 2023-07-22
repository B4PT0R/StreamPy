# Explanation of the streamlit_deferrer.py module

This module is used to defer streamlit module calls/context managers/outputs, each being encoded has a special helper object containing all the required information to actualy deal with it later.

The logic of this module is pretty intricate so let me attempt to clarify it. 

The main object of this module is the st_deferrer class.
It is meant to stand as a "deferred" version of the streamlit module.
For example, you may declare:
```python
std=st_deferrer()
```
and then call a callable with it as you would with the steamlit module:
```python
std.write("hello")
```
but, here, the write widget won't be rendered directly.

Instead, std will create a st_callable object (subclass of st_object) with .name='write'. The actual call will set its .args property to ("hello",) and the object will be appended it to a list (the std.queue property). That's pretty much all there is to understand.

You may add this way other streamlit calls, and each will be encoded as st_objects and piled in the queue, on top of previous ones.

Only when the user calls std.refresh() will every object in the queue be rendered on screen, from first to last. In our case, the callable 'write' from streamlit module will be fetched, passed argument "hello" and be actualy called, thus rendering the write widget on screen.

This way you may pile-up and postpone streamlit widgets rendering until a refresh (useful to spawn widgets dynamicaly and avoid a blocking behaviour while the app is running its refresh loop).

The tricky part is implement context managment and outputs correctly.

Let's see outputs first.

For instance, you may want to write:
```python
txt=std.text_input("Enter text here:")
```
Here std will similarly create a st_callable object with .name='text_input' and .args=("Enter text here:",) and append it to its queue.
However, steamlit.text_input is supposed to return a value when called (the text content of the widget).
But this "widget" doesn't yet exist, it's just an st_callable for now, and has not been rendered yet, so there in no text to be returned!
Therefore we must make std return something for the variable txt that will hold the future text content of the future text_input widget.
This is what the st_output class is for. It is basicaly a placeholder object, that will receive the text content of the widget as soon as it becomes available.
It's .value property will allow to access this text content in due time, but will be None until the widget is rendered and the text content actualy exists.

Second tricky thing: implement context management coherently.
For instance you may want to write:
```python
with std.empty():
    std.write("Hello")
```
The output returned by std.empty() must terefore be usable as a context manager (implement __enter__ and __exit__ methods adequately).
Any st_object must as well have a memory of this context to be able to take it into account at the moment of rendering...
That's what the .context attribute and the ctx context manager (used at rendering time) are for.

Things become even trickier when having to handle syntaxes such as :
```python
    c1,c2=std.columns(2)
    with c1:
        std.write("column1")
    with c2:
        std.write("column2")
```
But it's basicaly a generalization of the first two examples, except we need to unpack 2 st_outputs after the call of std.columns.
That's why some st_object must implement an __iter__ method (to allow unpacking of the outputs) : thus the st_unpackable_callable class.

Each st_output object (c1,c2) must also receive it's value (an actual streamlit column) from the same callable at rendering time.
That's why every st_callable keeps a list of its ouputs in order to allow proper routing of outputs at rendering time. 

Some other streamlit syntaxes such as :
```python
with std.sidebar:
    #do something
```
or,
```python
e=std.empty()
e.write("hello")
```
require further logic : namely implementing property-like syntax via the st_property object in the first, and implementing __getattr__  method for st_outputs in the second.

Some special streamlit attributes require special handling for a smooth integration in the console flow, such as:

-streamlit.column_config, streamlit.session_state (which are supposed to return directly the corresponding streamlit object: st_direct_property)

-streamlit.spinner & streamlit.progress (must be rendered immediately while the python code is running : st_direct_callable)

-streamlit.balloons & streammlit.snow (need to be rendered only one time to avoid having balloons/snow appearing on screen at every refresh : st_one_shot_callables)

The st_deferrer.stream method is here to help with rendering widgets in real-time while they are piled in the deferrer by the python interpreter running in a separate thread.

For convenience I added a KeyManager class allowing to automate widget key generation and ease keys management. 

Well, I hope these explanations will help clarify a bit the intent of the code.
This is for sure one of the most challenging coding task I personaly encountered at my humble level.
I don't pretend to be an experimented python developer, and I'm sure there are lots of ways this code can be improved.
All this is still a work in progress but functionning enough to handle most common streamlit syntaxes and almost all widgets in the console.
I guess it's a bit of a hack that extends streamlit possibilities slightly beyond what they were initialy meant to be.
Especialy when dealing with interactive rendering and threads (a thread fills the std pile, the main application calls std.stream to render the widgets).

I invit brave developers amongst readers to help me improve it, as I intuit it can become a useful feature for streamlit users.
I also hope that some streamlit developers, with their hindsight on internal streamlit functionning, will take a look at it and hopefuly give me some feedback and hints on how to make it more robust and efficient at encapsulating streamlit's logic.

All this being said,
Happy coding! 

