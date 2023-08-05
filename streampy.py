import logging
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("log")
log.setLevel(logging.DEBUG)
import os, sys
_root_path_=os.path.dirname(os.path.abspath(__file__))
if not _root_path_ in sys.path:
    sys.path.append(_root_path_)
from crypto import gen_lock, check_lock
from input import Listener
import streamlit as stl
from streampy_console import Console
from streamlit_ace import st_ace
from streamlit_deferrer import st_deferrer,KeyManager
import json
import shutil


#-------------Initialize session_state variables--------------

#shortcut
state=stl.session_state

#root folder's path of the app 
if 'root' not in state:
    state.root=_root_path_

#detects wether the app runs localy or not.
if 'mode' not in state:
    if state.root.startswith('/mount') or state.root.startswith('/app'):
        state.mode="web"
    else:
        state.mode="local"

#Username
if 'user' not in state:
    if state.mode=='web':
        state.user=""
    else:
        state.user="DefaultUser"

#User folder
if 'user_folder' not in state:
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

#Listener used to redirect stdin to a custom input widget in direct communication with the python backend
if not 'listener' in state:
    state.listener=Listener(mode=state.mode)
    state.listener.start_listening()

#the python console in which the code will be run. Initialized at user login.
if 'console' not in state:
    state.console = None

#the file currently open in the editor
if 'open_file' not in state:
    state.open_file=None

#the content of the file currently open in the editor
if 'open_file' not in state:
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
    with open(os.path.join(state.user_folder,name),'w') as f:
        f.write(state.file_content)
    state.open_file=name

#Closes the editor
def close_editor():
    state.show_editor=False

#Runs the code content open in the editor in the console  
def run_editor_content():
    code=state.file_content
    with state.console_queue:
        state.console.run(code)
    stl.experimental_rerun()

#Opens a new buffer or file in the editor
def edit(file='buffer'):
    state.show_editor=True
    state.open_file=file
    if not file=='buffer':
        if not os.path.exists(os.path.join(state.user_folder,file)):
            with open(os.path.join(state.user_folder,file),'w') as f:
                pass
        with open(os.path.join(state.user_folder,file),'r') as f:
            file_content=f.read()
    else:
        file_content=''
    state.file_content=file_content

def show_hide_history_cells():
    if 'history_cell' in st.hidden_tags:
        st.show('history_cell')
    else:
        st.hide('history_cell')

#Restarts the whole session to startup state
def restart():
    st.clear()
    state.console=Console(st,names=globals(),listener=state.listener, startup=os.path.join(state.user_folder,"startup.py"))

#Clears the console's queue
def clear():
    st.clear()

#Run some code in the python console
def process(code):
    if not (code=="" or code==None):
        with state.console_queue:
            st.ace(value=code,language='python', auto_update=True,readonly=True,theme='chrome', min_lines=2,tag="history_cell")
            state.console.run(code)

#Sets the sidebar menu
def make_menu():
   with stl.sidebar:
        stl.subheader("Menu")
        def on_open_editor_click():
            edit('buffer')
        stl.button("Open Editor",on_click=on_open_editor_click,use_container_width=True)
        def on_close_editor_click():
            close_editor()
        stl.button("Close Editor",on_click=on_close_editor_click,use_container_width=True)
        def on_restart_click():
            restart()
        stl.button("Restart Session",on_click=on_restart_click,use_container_width=True)
        def on_history_click():
            show_hide_history_cells()
        stl.button("Show/Hide history cells",on_click=on_history_click,use_container_width=True)


#Sets the welcome message header and help expander
def make_welcome():
    stl.subheader("Welcome to StreamPy interactive interpreter.")
    with stl.expander("Click here to get help."):
        with open(os.path.join(state.root,"Help.md"),'r') as f:
            stl.write(f.read())

#Sets the input cell part 
def make_input():
    n=len(state.console.inputs)
    if state.index<=0:
        state.index=0
    elif state.index>n:
        state.index=n

    if n==0 or state.index==0:
        state.input_code=""
    else:   
        state.input_code=state.console.inputs[n-state.index]
    
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
        #pass
        #Not ideal, as it causes a blinking of the app, messes with st.snow and st.balloons, but sucessful at avoiding the "missing/double widget bug" appearing in some cases, for some obscur reason...
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
    c1,c2,c3,c4,c5,c6,c7,c8=stl.columns(8)
    with c1:
        new_butt=stl.button("New",use_container_width=True)
    with c2:
        open_butt=stl.button("Open",use_container_width=True)
    with c3:
        save_butt=stl.button("Save",use_container_width=True)
    with c4:
        save_as_butt=stl.button("Save as",use_container_width=True)
    with c5:
        rename_butt=stl.button("Rename",use_container_width=True)
    with c6:
        delete_butt=stl.button("Delete",use_container_width=True)
    with c7:
        run_butt=stl.button("Run",use_container_width=True)
    with c8:
        close_butt=stl.button("Close",use_container_width=True)
    if close_butt:
        close_editor()
        stl.experimental_rerun()
    elif open_butt:
        def on_file_name_change():
            if not state.file_name==' ':
                edit(state.file_name)
        basenames = [' ']+[os.path.basename(f) for f in os.listdir(state.user_folder)]
        stl.selectbox('Select a file:',basenames,on_change=on_file_name_change,index=0,key='file_name')
    elif delete_butt:
        def on_yes():
            os.remove(os.path.join(state.user_folder,state.open_file))
            edit()
            state.editor_key=km.gen_key()
            with editor_column:
                stl.success("File deleted.")
        stl.selectbox('Are you sure you want to delete this file ?',['No','Yes'],on_change=on_yes,index=0,key='sure')  
    elif new_butt:
        edit()
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
                os.remove(os.path.join(state.user_folder,state.open_file))
                save_as(state.file_name)
                with editor_column:
                    stl.success("File renamed.")
            stl.text_input("Enter new name of file:",on_change=on_file_name_change,key='file_name')
        
        state.file_content=st_ace(value=state.file_content, placeholder="", language='python', auto_update=True,theme='chrome', min_lines=15, key=state.editor_key)
        if run_butt:
            run_editor_content()

#Makes the webapp login        
def make_login(): 
    stl.subheader("Welcome to Streampy!")
    stl.write("Please enter your credentials. If these are new, a new account will be created automaticly.")
    con=stl.container()
    with con:
        def on_submit_click():
            if not state.username=="" and not state.password=="":
                try:
                    with open(os.path.join(state.root,"users.json"),'r') as f:
                        users=json.load(f)
                    if state.username in users:
                        if check_lock(state.password,users[state.username]):
                            state.user=state.username
                            state.user_folder=os.path.join(state.root,"UserFiles",state.user)
                        else:
                            stl.warning("Wrong password.")
                    else:
                        users[state.username]=gen_lock(state.password,30)
                        with open(os.path.join(state.root,"users.json"),'w') as f:
                            json.dump(users,f)
                        state.user=state.username
                        os.mkdir(os.path.join(state.root,"UserFiles",state.user))
                        state.user_folder=os.path.join(state.root,"UserFiles",state.user)
                        shutil.copy(os.path.join(state.root,"startup.py"),os.path.join(state.user_folder,"startup.py"))
                except Exception as e:
                    #stl.exception(exception=e)
                    stl.warning("Something went wrong. Please try again.")    
            else:
                stl.warning("Non-empty username and password required")

        with stl.form("login",clear_on_submit=True):
            stl.text_input("Username (ABCabc123_):",key='username')
            stl.text_input("Password:",type="password",key='password')
            stl.form_submit_button("Submit",on_click=on_submit_click)
        stl.warning("This log-in is very basic and provides little security. It is only meant to let you have a personal folder in the StreamPy app so that you may test it comfortably. Your password is protected (it is stored strongly encrypted) but the content of your folder is not. A malvolent user could sneak in and access this content. Please don't store sensitive data in your folder!")
        stl.warning("The app is still a work in progress and will be rebuilt frequently. As a result, files stored in your folder will be lost. It is therefore recommended that you copy/paste your scripts to local files if you want to save them in the long run. Sorry for the inconvenience.")


#-----------------------------Main app session's logic-------------------------
if state.user=="":
    #Ask for credentials
    stl.set_page_config(layout="centered",initial_sidebar_state="collapsed")
    make_login()
else:
    #Initialize the user's session
    if state.user_folder=="":
        state.user_folder=os.path.join(state.root,"UserFiles",state.user)
        os.chdir(state.user_folder)
    if state.console is None:
        state.console=Console(st,names=globals(),listener=state.listener,startup=os.path.join(state.user_folder,"startup.py"))
    
    #Forces the interpreter's cwd to the user's folder
    if state.mode=="web":
        os.chdir(state.user_folder)

    #Show the app's main page
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
