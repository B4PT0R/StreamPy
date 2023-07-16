from StConsole import StConsole
import logging
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("log")
log.setLevel(logging.DEBUG)
from streamlit_ace import st_ace
from streamlit_deferrer import st_deferrer,st_output,KeyManager
import streamlit as stl
import os

state=stl.session_state

if 'key_manager' not in state:
    state.key_manager=KeyManager()
km=state.key_manager

if 'deferrer' not in state:
    state.deferrer=st_deferrer(key_manager=km)
st=state.deferrer
st.reset()

if 'open_file' not in state:
    state.open_file=None

if 'file_content' not in state:
    state.file_content=None

if 'show_editor' not in state:
    state.show_editor=False

if 'input_deferrer' not in state:
    state.input_deferrer=st_deferrer(key_manager=km)
sti=state.input_deferrer


if 'input_code' not in state:
    state.input_code = st_output(deferrer=sti,context=None)

if 'output_code' not in state:
    state.output_code = st_output(deferrer=sti,context=None)

if 'editor_key' not in state:
    state.editor_key = km.gen_key()

if 'index' not in state:
    state.index = 0

def save_as(name):
    with open(name,'w') as f:
        f.write(state.file_content)
    state.open_file=name

def close_editor():
    state.show_editor=False
    state.open_file=None
    state.file_content=None

    
def run_editor_content():
    code=state.file_content
    console.run(code)
    stl.experimental_rerun()

def edit(file):
    if not os.path.exists(file):
        with open(file,'w') as f:
            pass
    state.show_editor=True
    state.open_file=file
    with open(state.open_file,'r') as f:
        state.file_content=f.read()

def restart():
    st.clear()
    state.console=StConsole(st,startup='startup.py')
    state.console.synchronize(globals())

    
def clear():
    st.clear()

if 'console' not in state:
    state.console = StConsole(st,startup='startup.py')
console=state.console
console.synchronize(globals())



def process(code,queue):
    if not (code=="" or code==None):
        st.ace(value=code, placeholder="", language='python', auto_update=True, theme='chrome', min_lines=2, readonly=True,key=st.gen_key())
        console.run(code)


def make_menu():
   with stl.sidebar:
        stl.subheader("Menu")
        def on_open_editor_click():
            edit('new_buffer')
        stl.button("Open Editor",on_click=on_open_editor_click)
        def on_close_editor_click():
            close_editor()
        stl.button("Close Editor",on_click=on_close_editor_click)
        def on_restart_click():
            restart()
        stl.button("Restart Session",on_click=on_restart_click)



def make_welcome():
    stl.subheader("Welcome to StreamPy interactive interpreter.")
    with stl.expander("Click here to get help."):
        stl.write("""
StreamPy is a Python 3 interactive interpreter empowered by the rich input/output environment provided by Streamlit.

Usage is pretty straightforward. Quite similarly to a Jupyter Notebook, just type your python commands in the input cell and click "Run" to get the results.

Feel free to use Streamlit commands in your scripts with preloaded prefix 'st', as you would normaly do in a Streamlit script. 
The widgets will be outputted automaticly at the right place in the interactive console queue.
No need to import streamlit in your scripts, the 'st' prefix is actualy a special helper class instance that will take care of dealing with streamlit calls to render them adequetely in the console.

As an example, try to run the following snippet in the console, demonstrating the basic features of streamlit:
```python
c1,c2,c3=st.columns(3)
with c1:
    txt=st.text_input(label="Enter text here:")
with c2:
    def on_button_click():
        with placeholder:
            st.write("You entered: "+txt.value)
    st.button("Click Me!",on_click=on_button_click)
with c3:
    placeholder=st.empty()
```
It creates 3 columns, places a text_input widget in the first, a button in the second that will trigger the writing of the text content in an empty placeholder in the third column.
Type some text and click the button to see what happens.

Note that, contrary to normal Streamlit syntax, txt is not refering directly to the text content string of the text_input widget, but is rather an object placeholder for the (future!) content of this text_input. It will be actualized in real-time if the content changes, and you may retrieve its value at any time by accessing its 'value' property, as in the snippet.

Even though the Python interpreter maintains its session state, you may want to use st.session_state as you would in a Streamlit script.
To ease widget's keys managment, feel free to use the implemented key generator:
```python
my_text_input_key=st.gen_key()
st.text_input("Enter text here:",key=my_text_input_key)
``` 
This will generate a unique key for your widget's state that you may latter access via :
```python
my_text_input_state=st.session_state[my_text_input_key]
``` 
Apart from this, it's just normal Python and Streamlit commands!

Refer to [Streamlit documentation](https://docs.streamlit.io/library/api-reference) to get more informations on possible commands and how to use them. Most snippets provided in the examples will be working directly in the console (provided you skip the "import streamlit as st" line).

In the side Menu, you'll be able to open a basic text editor to edit/save longer scripts as well as running them in the console.
The Restart Session button will reinitialize the python session to its startup state.

Worth being noted: The python session runs the startup.py script at startup. Useful to import common modules, define your favorite functions or classes, or serve as an entry point to preload other chosen scripts automaticly when the session starts.

---Note for developers---

StreamPy features a special streamlit_deferrer module I designed which is crucial to manage interactivity and widget rendering in the console queue. It functions by encoding streamlit calls, piling them to a queue, and render the queue (which means actualy executing the corresponding streamlit commands) when desired. This allows handling (almost! Working on it...) all Streamlit functions and syntaxes in deferred manner for a seamless integration in the StreamPy interactive console. This is what happens under the hood when you run streamlit commands in the console using the 'st' prefix. 
The 'st' prefix preloaded in the console is a st_deferrer class instance from the streamlit_deferrer module, not streamlit module itself. So avoid importing streamlit as st or it will overwrite the prefix with normal streamlit module and break the console's functionalities.

StreamPy is only the first part of a larger project. My goal is to include an LLM agent (GPT4 / Claude2) with coding capabilities, that will have the session in context, be able to interact with the user, show/run snippets, and use streamlit widgets profitably for richer output. 

The project is mostly working but still an early prototype and have not yet been throughly tested. Some widgets/syntaxes just won't work properly (most will) and you may run into errors or undesired behaviour. If you want to report a bug or feel like contributing to the project, feel free to check the [GitHub repository](https://github.com/B4PT0R/StreamPy) or reach me out directly at bferrand.maths@gmail.com. Any contribution to the project will be met with enthusiasm and gratitude. :)

Happy testing!  
""")
 
def make_input(queue):
    sti.clear()
    n=len(console.inputs)
    if state.index<=0:
        state.index=0
        state.input_code.value=""
    elif state.index>n:
        state.index=n
        state.input_code.value=console.inputs[n-state.index]
    else:
        state.input_code.value=console.inputs[n-state.index]
    state.output_code = sti.ace(value=state.input_code.value, placeholder="", language='python', auto_update=True,theme='chrome', min_lines=2, key=state.editor_key)
    a,_,b,_,c=sti.columns([1,3,1,3,1],gap='small')
    with a:
        def on_previous_click():
            state.index+=1
            state.editor_key=sti.gen_key()
        sti.button("Prev.", key='previous',on_click=on_previous_click)
    with b:
        def on_run_click():
            state.index=0
            process(state.output_code.value,queue)
            state.editor_key=sti.gen_key()
        sti.button("Run",key='run_button',on_click=on_run_click)
    with c:  
        def on_next_click():
            state.index-=1
            state.editor_key=sti.gen_key()
        sti.button("Next", key='next',on_click=on_next_click)

    sti.refresh()

    if state.run_button:
        stl.experimental_rerun() #This needs to be removed

def make_console():
    welcome=stl.container()        
    queue=stl.container()
    input=stl.container()

    with welcome:
        make_welcome()   

    with queue:
        st.refresh()

    with input:
        make_input(queue)

def make_editor(editor_column):
    stl.subheader(f"Editing: {os.path.basename(state.open_file)}")
    c1,c2,c3,c4,c5,c6=stl.columns([5,5,5,5,5,5])
    with c1:
        new_butt=stl.button("New")
    with c2:
        open_butt=stl.button("Open")
    with c3:
        save_butt=stl.button("Save")
    with c4:
        save_as_butt=stl.button("Save as")
    with c5:
        run_butt=stl.button("Run")
    with c6:
        close_butt=stl.button("Close")
    if close_butt:
        close_editor()
        stl.experimental_rerun()
    elif open_butt:
        def on_file_name_change():
            if os.path.exists(state.file_name):
                edit(state.file_name)
            else:
                with editor_column:
                    stl.warning("This file doesn't exist!")
        stl.text_input("Enter name of file:",on_change=on_file_name_change,key='file_name')
    elif new_butt:
        def on_file_name_change():
            if not os.path.exists(state.file_name):
                edit(state.file_name)
            else:
                with editor_column:
                    stl.warning("This file already exists!")
        stl.text_input("Enter name of file:",on_change=on_file_name_change,key='file_name')
    else:
        if save_butt:
            save_as(state.open_file)
        if save_as_butt:
            def on_file_name_change():
                save_as(state.file_name)
            stl.text_input("Enter name of file:",on_change=on_file_name_change,key='file_name')
        state.file_content=st_ace(value=state.file_content, placeholder="", language='python', auto_update=True,theme='chrome', min_lines=15, key='editor')
        if run_butt:
            run_editor_content()
        


if state.show_editor==True:
    stl.set_page_config(layout="wide",initial_sidebar_state="collapsed")
    make_menu()
    console_column,editor_column=stl.columns(2)
    with console_column:
        make_console()
    with editor_column:
        make_editor(editor_column)
else:
    stl.set_page_config(layout="centered",initial_sidebar_state="collapsed")
    make_menu()
    make_console()







