import os,sys
_root_path_=os.path.dirname(os.path.abspath(__file__))
if not _root_path_ in sys.path:
    sys.path.append(_root_path_)
from restrict_module import restrict_module
restrict_module('streamlit',['secrets'])
restrict_module('os',['system'])
restrict_module('firebase_admin')
restrict_module('firebase_tools')
from crypto import gen_lock, check_lock
from input import Listener
import streamlit as stl
from firebase_tools import firebase_app_is_initialized,firebase_init_app,FirestoreDocument,FirebaseStorage
if not firebase_app_is_initialized():
    firebase_init_app(stl.secrets["firebase_credentials"])
from streampy_console import Console
from streamlit_ace import st_ace
from custom_code_editor import input_cell,editor,code_editor_output_parser
from streamlit_deferrer import st_deferrer,KeyManager
import shutil
import time
import json


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

#A boolean indicating if the user has log-out
if 'log_out' not in state:
    state.log_out=False

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

#Listener used to redirect stdin to a custom input widget in direct communication with the python backend.
#Initialized when user logs-in
if not 'listener' in state:
    state.listener=None

#the python console in which the code will be run. Initialized at user login.
if 'console' not in state:
    state.console = None

if not 'input_cell_output_parser' in st.session_state:
    st.session_state.input_cell_output_parser=code_editor_output_parser()

if not 'editor_output_parser' in st.session_state:
    st.session_state.editor_output_parser=code_editor_output_parser()

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

#dumps the entire user folder to the cloud
def dump_to_cloud():
    cloud=FirebaseStorage()
    try:
        with st.spinner("Please wait while your folder is being saved in the cloud..."):
            cloud.dump_folder_to_cloud(state.user_folder,state.user)
    except Exception as e:
        st.exception(e)
    else:
        st.success("Folder saved successfully.")

def log_out():
    state.log_out=True

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

#Opens a new buffer or file in the editor (prefilled with an optional text)
def edit(file='buffer',text=None):
    state.show_editor=True
    state.open_file=file
    if not file=='buffer':
        if not os.path.exists(os.path.join(state.user_folder,file)):
            with open(os.path.join(state.user_folder,file),'w') as f:
                pass
        if text is None:
            with open(os.path.join(state.user_folder,file),'r') as f:
                file_content=f.read()
        else:
            file_content=text
    else:
        if text is None:
            file_content=''
        else:
            file_content=text
    state.file_content=file_content

#Show/hide past input cells
def show_hide_history_cells():
    if 'history_cell' in st.hidden_tags:
        st.show('history_cell')
    else:
        st.hide('history_cell')

#Restarts the whole session to startup state
def restart():
    st.clear()
    names={
        'st':st,
        'clear':clear,
        'restart':restart,
        'edit':edit,
        'close_editor':close_editor,
        'exit':log_out,
        'quit':log_out
        }
    state.console=Console(st,names=names,listener=state.listener, startup=os.path.join(state.user_folder,"startup.py"))

#Clears the console's queue
def clear():
    st.clear()

#Run some code in the python console
def process(code):
    if not (code=="" or code==None):
        with state.console_queue:
                st.code(code,language='python',tag="history_cell")
                state.console.run(code)

#---------------------------------App layout-------------------------------------

#Sets the sidebar menu
def make_menu():
   with stl.sidebar:
        if state.mode=="web":
            stl.subheader("Session")
            stl.text(state.user)
            def on_log_out_click():
                state.log_out=True
            stl.button("Log out",on_click=on_log_out_click,use_container_width=True)
            stl.write('---')
        stl.subheader("Menu")
        def on_open_editor_click():
            edit('buffer')
        stl.button("Open editor",on_click=on_open_editor_click,use_container_width=True)
        def on_close_editor_click():
            close_editor()
        stl.button("Close editor",on_click=on_close_editor_click,use_container_width=True)
        def on_restart_click():
            restart()
        stl.button("Restart session",on_click=on_restart_click,use_container_width=True)
        def on_history_click():
            show_hide_history_cells()
        stl.button("Show/Hide history cells",on_click=on_history_click,use_container_width=True)
        
#Sets the welcome message header and help expander
def make_welcome():
    stl.subheader("Welcome to StreamPy interactive interpreter.")
    with stl.expander("Click here to get help."):
        with open(os.path.join(state.root,"README.md"),'r') as f:
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
    
    
    event,code=input_cell(state.input_code,key=state.input_key)
    if event=='submit':
        state.index=0
        process(code)
        state.input_key=km.gen_key()
        stl.experimental_rerun()
        #This rerun is not ideal, as it causes a blinking of the app, but sucessful at avoiding the "missing/double widget bug" appearing in some cases, for some obscur reason...
        #I guess the issue comes from the number of mainloop turns required by streamlit to "consume" the widget
        #In case a widget needs several ones, the next call to refresh will create a duplicate until the first is consumed by streamlit
        #The issue only applies for unkeyed widgets, as I somewhat managed to remove the bug for keyed ones by adding a DuplicateWidgetID exception catching in the deferrer's refresh and stream logic

    a,b=stl.columns(2,gap='small')
    with a:
        def on_previous_click():
            state.index+=1
            state.input_key=km.gen_key()
        stl.button("Previous", key='previous',on_click=on_previous_click,use_container_width=True)    
    with b:  
        def on_next_click():
            state.index-=1
            state.input_key=km.gen_key()
        stl.button("Next", key='next',on_click=on_next_click,use_container_width=True)

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
def make_editor():
    stl.subheader(f"Editing: {os.path.basename(state.open_file)}")
    empty=stl.empty()
    event,state.file_content=editor(state.file_content,key=state.editor_key)
    if event=="close":
        close_editor()
        stl.experimental_rerun()
    elif event=="open":
        def on_file_name_change():
            if not state.file_name==' ':
                state.editor_key=km.gen_key()
                edit(state.file_name)
        def get_relative_paths(folder_path):
            """Get all relative paths of files in the given folder, recursively."""
            relative_paths = []
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    rel_dir = os.path.relpath(dirpath, folder_path)
                    rel_path = os.path.join(rel_dir, filename)
                    if rel_path.startswith('./'):
                        rel_path=rel_path[2:]
                    relative_paths.append(rel_path)
            return relative_paths
        files = [' ']+get_relative_paths(state.user_folder)
        with empty:
            stl.selectbox('Select a file:',files,on_change=on_file_name_change,index=0,key='file_name')
    elif event=="delete":
        def on_yes():
            os.remove(os.path.join(state.user_folder,state.open_file))
            state.editor_key=km.gen_key()
            edit()
            with empty:
                stl.success("File deleted.")
        with empty:
            stl.selectbox('Are you sure you want to delete this file ?',['No','Yes'],on_change=on_yes,index=0,key='sure')  
    elif event=="new":
        state.editor_key=km.gen_key()
        edit()
        stl.experimental_rerun()
    elif event=="submit":
        if not state.open_file=='buffer':
            save_as(state.open_file)
            with empty:
                stl.success("File saved.")
        else:
            def on_file_name_change():
                save_as(state.file_name)
                with empty:
                    stl.success("File saved.")
            with empty:
                stl.text_input("Enter name of file:",on_change=on_file_name_change,key='file_name')
    elif event=="save_as":
        def on_file_name_change():
            save_as(state.file_name)
            with empty:
                stl.success("File saved.")
        with empty:
            stl.text_input("Enter name of file:",on_change=on_file_name_change,key='file_name')
    elif event=="rename":
        def on_file_name_change():
            os.remove(os.path.join(state.user_folder,state.open_file))
            save_as(state.file_name)
            with empty:
                stl.success("File renamed.")
        with empty:
            stl.text_input("Enter new name of file:",on_change=on_file_name_change,key='file_name')
    elif event=="run":
        run_editor_content()

#Makes the webapp login page        
def make_login(): 
    stl.subheader("Streampy - Streamlit powered Python 3 interpreter")
    stl.write("Please enter your credentials. If these are new, a new account will be created automaticly.")
    con=stl.container()
    with con:
        def on_submit_click():
            if not state.username=="" and not state.password=="":
                try:
                    doc=FirestoreDocument('Documents','Users')
                    cloud=FirebaseStorage()
                    users=doc.load()
                    if state.username in users:
                        if check_lock(state.password,users[state.username]['password']):
                            state.user=state.username
                            state.user_folder=os.path.join(state.root,"UserFiles",state.user)
                            with stl.spinner("Please wait while your folder is being uploaded from the cloud..."):
                                cloud.load_folder_from_cloud(state.user,state.user_folder)
                            if not os.path.exists(os.path.join(state.user_folder,"startup.py")):
                                shutil.copy(os.path.join(state.root,"startup.py"),os.path.join(state.user_folder,"startup.py"))
                        else:
                            stl.warning("Wrong password.")
                            time.sleep(0.5)
                    else:
                        users[state.username]={
                            'password':gen_lock(state.password,30)
                        }
                        doc.dump(users)
                        state.user=state.username
                        if not os.path.exists(os.path.join(state.root,"UserFiles",state.user)):
                            os.mkdir(os.path.join(state.root,"UserFiles",state.user))
                        state.user_folder=os.path.join(state.root,"UserFiles",state.user)
                        if not os.path.exists(os.path.join(state.user_folder,"startup.py")):
                            shutil.copy(os.path.join(state.root,"startup.py"),os.path.join(state.user_folder,"startup.py"))
                except Exception as e:
                    stl.exception(e)
                    stl.warning("Something went wrong. Please try again.")    
            else:
                stl.warning("Non-empty username and password required.")

        with stl.form("login",clear_on_submit=True):
            stl.text_input("Username:",key='username')
            stl.text_input("Password:",type="password",key='password')
            stl.form_submit_button("Submit",on_click=on_submit_click)
        stl.subheader("Latest improvements:")
        with open(os.path.join(_root_path_,"improvements.json")) as f:
            improvements=json.load(f)
        for i in range(1,7):
            stl.info(improvements[-i]) 
        

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
    if state.listener is None:
        #start the front-end listener for sdtin redirection
        state.listener=Listener(state.user,state.mode)
        state.listener.start_listening()
    if state.console is None:
        names={
            'st':st,
            'clear':clear,
            'restart':restart,
            'edit':edit,
            'close_editor':close_editor,
            'exit':log_out,
            'quit':log_out
        }
        state.console=Console(st,names=names,listener=state.listener,startup=os.path.join(state.user_folder,"startup.py"))
        os.chdir(state.user_folder)

    #Show the app's main page
    if state.show_editor==True:
        stl.set_page_config(layout="wide",initial_sidebar_state="collapsed")
        make_menu()
        console_column,editor_column=stl.columns(2)
        with console_column:
            make_console()
        with editor_column:
            make_editor()
    else:
        stl.set_page_config(layout="centered",initial_sidebar_state="collapsed")
        make_menu()
        make_console()

if state.log_out:
    if state.mode=="web":
        dump_to_cloud()
        shutil.rmtree(state.user_folder)
    state.open_file=None
    state.file_content=None
    state.show_editor=False
    state.username=""
    state.password=""
    state.user=""
    state.user_folder=""
    state.listener=None
    state.console=None
    state.deferrer.clear()
    state.log_out=False
    os.chdir(_root_path_)
    stl.experimental_rerun()