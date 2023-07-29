# Explanation of the streamlit_deferrer.py module

This module is used to allow dynamic widget rendering, while the streamlit app is running. 

It functions by deferring streamlit module calls/context managers/outputs, each being encoded has a special helper object containing all the required information to actualy render it later.

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

Instead, std will create a st_callable object (subclass of st_object) with .name='write'. The actual call will set its .args property to ("hello",) and the object will be appended it to a list in the deferrer (the std.queue property). This is the basic idea.

You may add this way other streamlit calls, and each will be encoded as st_objects and appended to the queue, on top of previous ones.

Only when the user calls std.refresh() will every object in the queue be rendered on screen, from first to last. In our case, the callable 'write' from streamlit module will be fetched, passed argument "hello" and be actualy called, thus rendering the write widget on screen.

This way you may pile-up and postpone streamlit widgets rendering until a refresh. 

Once an object has been appended to the deferrer's queue, it will remain there (saved in the session_state, because the deferrer is). Since the streamlit script loops on itself, a new turn will start and another refresh call will be encountered, and the queued widgets will be rendered again. Therefore, your widgets will be rendered every turn of streamlit's mainloop, so that they don't disappear from screen.

This logic allows to add widgets dynamicaly to your app, while it's running!

Your app's mainloop (=your streamlit script) can thus be understood as this simplified schema:
```python
# Declare a deferrer in the session_state

# Reset the deferrer. (Sets the has_rendered property of all widgets in the queue to False, so that they will be re-rendered by the next refresh)

# Render your app's static layout using normal streamlit commands.

# Run functions populating the deferrer's queue, for dynamic widgets creation.

# Call the deferrer's refresh method to render all queued widgets.
```

The syntaxes allowed by the deferrer object are meant to mimic as closely as possible the syntaxes allowed by the streamlit module for a seamless usage.

The tricky part is implement context managment and outputs correctly.

Let's see outputs first.

For instance, you may want to write:
```python
txt=std.text_input("Enter text here:")
```
Here std will similarly create a st_callable object with .name='text_input' and .args=("Enter text here:",) and append it to its queue.
However, steamlit.text_input is supposed to return a value when called (the text content of the widget).
But this "widget" doesn't yet exist, it's just an st_callable for now, and has not been rendered yet, so there in no text to be returned!
Therefore we must make std return something for variable txt that will hold the future text content of the future text_input widget.
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

-st.column_config, st.session_state (properties supposed to return directly the corresponding streamlit object: handled by the st_direct_property function)

-st.spinner & st.progress (callables that must be rendered immediately while the python code is running : handled by the st_direct_callable class)

-st.balloons & st.snow (need to be rendered only one time to avoid having balloons/snow appearing on screen at every refresh : handled by the st_one_shot_callable class)

-st.echo (required a specific handling as its logic is peculiar compared to other widgets : see the echo_generator object in the echo.py module)

st_deferrer.mode='streamed' and st_deferrer.stream method are here to deal with rendering widgets as soon as they are appended to the deferrer. This allows for real-time rendering of widgets while StreamPy's python interpreter is running the code you inputted in the cell. In case the code execution takes a long time, you don't want to have to wait until the execution is completed to see your outputs/widgets... You want them to appear on screen at the exact moment they are produced by code execution!

For convenience I added a KeyManager class allowing to automate widget key generation and ease keys management. 

Well, I hope these explanations will help clarify a bit the intent of the code.
This is for sure one of the most challenging coding task I personaly encountered at my humble level.
I don't pretend to be an experimented python developer, and I'm sure there are lots of ways this code can be improved.
All this is still a work in progress but functionning enough to handle most common streamlit syntaxes and almost all widgets in the console.
I guess it's a bit of a hack that extends streamlit possibilities slightly beyond what they were initialy meant to be.
Especialy when dealing with interactive/dynamic widget rendering.

I invit brave developers amongst readers to help me improve it, as I intuit it can become a useful feature for streamlit users.
I also hope that some streamlit developers, with their hindsight on internal streamlit functionning, will take a look at it and hopefuly give me some feedback and hints on how to make it more robust and efficient at encapsulating streamlit's logic.

All this being said,
Happy coding! 

