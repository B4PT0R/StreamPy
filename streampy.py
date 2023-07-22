import logging
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("log")
log.setLevel(logging.DEBUG)
import streamlit as stl
from streampy_console import Console
from streamlit_ace import st_ace
from streamlit_deferrer import st_deferrer,KeyManager
import json
import shutil
import os

#-------------Initialize session_state variables--------------

state=stl.session_state #shortcut

#Username
if 'user' not in state:
    state.user=""

#User folder
if 'user' not in state:
    state.user_folder=""

#Useful to generate unique keys for widgets
if 'key_manager' not in state:
    state.key_manager=KeyManager()
km=state.key_manager

#Main streamlit commands deferrer for the console queue (allows using streamlit commands directly in the input cell)
if 'deferrer' not in state:
    state.deferrer=st_deferrer(key_manager=km)
st=state.deferrer
st.reset()

#Declares the python console in which the code will be run.
if 'console' not in state:
    state.console = None
console=state.console

#the file currently open in the editor
if 'open_file' not in state:
    state.open_file=None

#the content of the file open in the editor
if 'file_content' not in state:
    state.file_content=None

#whether to show the editor or not
if 'show_editor' not in state:
    state.show_editor=False

#The current key of the input cell (changing the key allows to reset the input cell to empty, otherwise the last text typed remains)
if 'input_key' not in state:
    state.input_key = km.gen_key()

#The code displayed in the input cell
if 'input_code' not in state:
    state.input_code = ''

#The code outputted by the input cell
if 'output_code' not in state:
    state.output_code = ''

#The current key of the editor ace widget
if 'editor_key' not in state:
    state.editor_key = km.gen_key()

#A variable allowing access to the console queue container from anywhere
if 'console_queue' not in state:
    state.console_queue=None

#A variable allowing access to the editor's container from anywhere
if 'console_queue' not in state:
    state.editor_container=None

#The current input history index
if 'index' not in state:
    state.index = 0

#------------------------------Main functions-------------------------------------

#Save the content of the editor as... 
def save_as(name):
    with open(state.user_folder++name,'w') as f:
        f.write(state.file_content)
    state.open_file=name

#Closes the editor
def close_editor():
    state.show_editor=False
    state.open_file=None
    state.file_content=None

#Runs the code content open in the editor in the console  
def run_editor_content():
    code=state.file_content
    with state.console_queue:
        console.run(code)
    stl.experimental_rerun()

#Opens a new buffer or file in the editor
def edit(file):
    state.show_editor=True
    state.open_file=file
    if not file=='buffer':
        if not os.path.exists(state.user_folder+file):
            with open(state.user_folder+file,'w') as f:
                pass
        with open(state.user_folder+state.open_file,'r') as f:
            state.file_content=f.read()
    else:
        state.file_content=''

#Restarts the whole session to startup state
def restart():
    st.clear()
    state.console=Console(st,names=globals(),startup=state.user_folder+'startup.py')


#Clears the console's queue
def clear():
    st.clear()

#Run some code in the python console
def process(code):
    if not (code=="" or code==None):
        with state.console_queue:
            console.run(code)

#Sets the sidebar menu
def make_menu():
   with stl.sidebar:
        stl.subheader("Menu")
        def on_open_editor_click():
            edit('buffer')
        stl.button("Open Editor",on_click=on_open_editor_click)
        def on_close_editor_click():
            close_editor()
        stl.button("Close Editor",on_click=on_close_editor_click)
        def on_restart_click():
            restart()
        stl.button("Restart Session",on_click=on_restart_click)


#Sets the welcome message header and help expander
def make_welcome():
    stl.subheader("Welcome to StreamPy interactive interpreter.")
    with stl.expander("Click here to get help."):
        with open("Help.md",'r') as f:
            stl.write(f.read())

#Sets the input cell part 
def make_input():
    n=len(console.inputs)
    if state.index<=0:
        state.index=0
    elif state.index>n:
        state.index=n

    if n==0 or state.index==0:
        state.input_code=""
    else:   
        state.input_code=console.inputs[n-state.index]
    
    state.output_code = st_ace(value=state.input_code, placeholder="", language='python', auto_update=True,theme='chrome', min_lines=2, key=state.input_key)
    a,_,b,_,c=stl.columns([1,3,1,3,1],gap='small')
    with a:
        def on_previous_click():
            state.index+=1
            state.input_key=km.gen_key()
        stl.button("Prev.", key='previous',on_click=on_previous_click)
    with b:
        def on_run_click():
            state.index=0
            process(state.output_code)
            state.input_key=km.gen_key()
        stl.button("Run",key='run_button',on_click=on_run_click)
    with c:  
        def on_next_click():
            state.index-=1
            state.input_key=km.gen_key()
        stl.button("Next", key='next',on_click=on_next_click)
    if state.run_button:
        stl.experimental_rerun() 
        # Not ideal, as it causes a blinking of the app, but sucessful at avoiding the "missing/double widget bug" appearing in some cases, for some obscur reason...
        #I guess the issue comes from the number of mainloop turns required by streamlit to "consume" the widget
        #In case a widget needs several ones, the next call to refresh will create a duplicate until the first is consumed by streamlit
        #The issue only applies for unkeyed widgets, as I somewhat managed to remove the bug for keyed ones by adding a DuplicateWidgetID exception catching in the deferrer's refresh and stream logic


#Displays the whole console queue
def make_console():
    welcome=stl.container()        
    queue=stl.container()
    state.console_queue=queue
    input=stl.container()

    with welcome:
        make_welcome()   

    with queue:
        st.refresh()

    with input:
        make_input()

#Displays the editor (could be simplified, reorganized, but I somewhat struggled with widget refreshing. This mess is the result of this struggle :) )
def make_editor(editor_column):
    stl.subheader(f"Editing: {os.path.basename(state.open_file)}")
    c1,c2,c3,c4,c5,c6,c7,c8=stl.columns([5,5,5,6,6,5,5,5])
    with c1:
        new_butt=stl.button("New")
    with c2:
        open_butt=stl.button("Open")
    with c3:
        save_butt=stl.button("Save")
    with c4:
        save_as_butt=stl.button("Save as")
    with c5:
        rename_butt=stl.button("Rename")
    with c6:
        delete_butt=stl.button("Delete")
    with c7:
        run_butt=stl.button("Run")
    with c8:
        close_butt=stl.button("Close")
    if close_butt:
        close_editor()
        stl.experimental_rerun()
    elif open_butt:
        def on_file_name_change():
            if not state.file_name==' ':
                edit(state.file_name)
        #stl.text_input("Enter name of file:",on_change=on_file_name_change,key='file_name')
        basenames = [' ']+[os.path.basename(f) for f in os.listdir(state.user_folder)]
        stl.selectbox('Select a file:',basenames,on_change=on_file_name_change,index=0,key='file_name')
    elif delete_butt:
        def on_yes():
            os.remove(state.user_folder+state.open_file)
            edit('buffer')
            state.editor_key=km.gen_key()
            with editor_column:
                stl.success("File deleted.")
        stl.selectbox('Are you sure you want to delete this file ?',['No','Yes'],on_change=on_yes,index=0,key='sure')  
    elif new_butt:
        edit('buffer')
        state.editor_key=km.gen_key()
        stl.experimental_rerun()
    else:
        if save_butt:
            if not state.open_file=='buffer':
                save_as(state.open_file)
                stl.success("File saved.")
            else:
                def on_file_name_change():
                    save_as(state.file_name)
                    with editor_column:
                        stl.success("File saved.")
                stl.text_input("Enter name of file:",on_change=on_file_name_change,key='file_name')
        elif save_as_butt:
            def on_file_name_change():
                save_as(state.file_name)
                with editor_column:
                    stl.success("File saved.")
            stl.text_input("Enter name of file:",on_change=on_file_name_change,key='file_name')
        elif rename_butt:
            def on_file_name_change():
                os.remove('./UserFiles/'+state.open_file)
                save_as(state.file_name)
                with editor_column:
                    stl.success("File renamed.")
            stl.text_input("Enter new name of file:",on_change=on_file_name_change,key='file_name')
        state.file_content=st_ace(value=state.file_content, placeholder="", language='python', auto_update=True,theme='chrome', min_lines=15, key=state.editor_key)
        if run_butt:
            run_editor_content()
        
def make_login(): 
    stl.subheader("Welcome to Streampy!")
    stl.write("Please enter your credentials. If these are new, a new account will be created automaticly.")
    con=stl.container()
    with con:
        def on_submit_click():
            if not state.username=="" and not state.password=="":
                with open("users.json",'r') as f:
                    users=json.load(f)
                if state.username in users:
                    if users[state.username]==state.password:
                        state.user=state.username
                        state.user_folder="./UserFiles/"+state.user+'/'
                        state.console=Console(st,names=globals(),startup=state.user_folder+'startup.py')
                    else:
                        st.warning("Wrong password.")
                else:
                    users[state.username]=state.password
                    with open("users.json",'w') as f:
                        json.dump(users,f)
                    state.user=state.username
                    os.mkdir("./UserFiles/"+state.user)
                    state.user_folder="./UserFiles/"+state.user+"/"
                    shutil.copy("./startup.py",state.user_folder+"startup.py")
                    state.console=Console(st,names=globals(),startup=state.user_folder+'startup.py')
            else:
                st.warning("Non-empty username and password required")

        stl.text_input("Username (ABCabc123_):",key='username')
        stl.text_input("Password:",key='password')
        stl.button("Submit",on_click=on_submit_click)
        stl.warning("This log-in is very basic and provides almost no security. It's only provided as a demo to let you have a personal folder in the StreamPy App. Please don't use an important password or store important/private data in your folder.")



#-----------------------------Main app session's logic-------------------------
if state.user=="":
    stl.set_page_config(layout="centered",initial_sidebar_state="collapsed")
    make_login()
else:
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







