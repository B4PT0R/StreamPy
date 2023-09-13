import os,sys
_root_=os.path.dirname(os.path.abspath(__file__))
if not _root_ in sys.path:
    sys.path.append(_root_)
from restrict_module import restrict_module
restrict_module('streamlit',['secrets'])
restrict_module('os',['system'])
restrict_module('firebase_admin')
restrict_module('firebase_tools')
restrict_module('google_search_tools')
from crypto import encrypt,decrypt,gen_lock, check_lock
from input import Listener
import streamlit as stl
from firebase_tools import firebase_app_is_initialized,firebase_init_app,FirestoreDocument,FirebaseStorage
if not firebase_app_is_initialized():
    firebase_init_app(stl.secrets["firebase_credentials"])
from google_search_tools import get_google_search
google_search=get_google_search(stl.secrets["google_custom_search"]["API_KEY"],stl.secrets["google_custom_search"]["CX"])
from streampy_console import Console
from custom_code_editor import input_cell,editor,code_editor_output_parser
from streamlit_mic_recorder import speech_to_text
from streamlit_TTS import text_to_speech 
from streamlit_deferrer import st_deferrer,KeyManager
import shutil
import time
import json
import io

#------------------------shortcuts--------------------------

state=stl.session_state

def root_join(*args):
    return os.path.join(_root_,*args)

def user_join(*args):
    return os.path.join(state.user_folder,*args)

#-------------Initialize session_state variables--------------

def initialize_state(state):
    #detects wether the app runs localy or not.
    if 'mode' not in state:
        if True:#_root_.startswith('/mount') or _root_.startswith('/app'):
            state.mode="web"
        else:
            state.mode="local"

    #Username
    if 'user' not in state:
        if state.mode=='web':
            state.user=""
        else:
            state.user="DefaultUser"

    #Password
    if 'password' not in state:
        state.password=None

    if 'page' not in state:
        state.page="login"

    #A boolean indicating if the user's session has been initialized
    if 'session_has_initialized' not in state:
        state.session_has_initialized=False

    #A boolean indicating if the user has log-out
    if 'log_out' not in state:
        state.log_out=False

    #User folder
    if 'user_folder' not in state:
        state.user_folder=""

    #Useful to generate unique keys for widgets
    if 'key_manager' not in state:
        state.key_manager=KeyManager()

    #Main streamlit commands deferrer for the console queue (allows using streamlit commands directly in the input cell)
    if 'deferrer' not in state:
        state.deferrer=st_deferrer(key_manager=state.key_manager)

    #Listener used to redirect stdin to a custom input widget in direct communication with the python backend.
    #Initialized when user logs-in
    if not 'listener' in state:
        state.listener=None

    #the python console in which the code will be run. Initialized at user login.
    if 'console' not in state:
        state.console = None

    #the AI assistant. Initialized at user login.
    if 'pandora' not in state:
        state.pandora=None

    if not 'input_cell_output_parser' in state:
        state.input_cell_output_parser=code_editor_output_parser()

    if not 'editor_output_parser' in state:
        state.editor_output_parser=code_editor_output_parser()

    #the file currently open in the editor
    if 'open_file' not in state:
        state.open_file=None

    #the content of the file currently open in the editor
    if 'open_file' not in state:
        state.file_content=None

    #whether to show the editor or not
    if 'show_editor' not in state:
        state.show_editor=False

    #The current key of the python input cell (changing the key allows to reset the input cell to empty, otherwise the last text typed remains)
    if 'input_key' not in state:
        state.input_key = state.key_manager.gen_key()

    if 'recorder_key' not in state:
        state.recorder_key=state.key_manager.gen_key()

    #The current key of the pandaora input cell (changing the key allows to reset the input cell to empty, otherwise the last text typed remains)
    if 'pandora_input_key' not in state:
        state.pandora_input_key = state.key_manager.gen_key()

    if 'prompt' not in state:
        state.prompt=None

    #The code displayed in the input cell
    if 'input_code' not in state:
        state.input_code = ''

    #The code outputted by the input cell
    if 'output_code' not in state:
        state.output_code = ''

    #The current key of the editor ace widget
    if 'editor_key' not in state:
        state.editor_key = state.key_manager.gen_key()

    #A variable allowing access to the console queue container from anywhere
    if 'console_queue' not in state:
        state.console_queue=None

    #A variable allowing access to the editor's container from anywhere
    if 'console_queue' not in state:
        state.editor_container=None

    #The current input history index
    if 'index' not in state:
        state.index = 0

initialize_state(state)
st=state.deferrer
km=state.key_manager
st.reset()

#------------------------------Main functions-------------------------------------

#dumps the entire user folder to the cloud
def dump_to_cloud():
    cloud=FirebaseStorage()
    try:
        cloud.dump_folder_to_cloud(state.user_folder,state.user)
    except Exception as e:
        st.exception(e)

def log_out():
    state.log_out=True

#Save the content of the editor as... 
def save_as(file):
    with open(file,'w') as f:
        f.write(state.file_content)
    state.open_file=file

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
def edit(file='buffer',text=None,wait=False):
    state.show_editor=True
    state.open_file=file
    if not file=='buffer':
        if text is None:
            if not os.path.exists(file):
                file_content=""
            else:
                with open(file,'r') as f:
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
    if not state.APIkey=="":
        from Pandora_web import Pandora
        class Utils:
            pass
        utils=Utils()
        utils.edit=edit
        utils.google_search=google_search
        state.pandora=Pandora(state.user_folder,state.console,utils)
        state.pandora.user=state.user
        state.console.send_in('pandora',state.pandora)

#Clears the console's queue
def clear():
    st.clear()

#Run some code in the python console
def run(code):
    if not (code=="" or code==None):
        with state.console_queue:
                st.code(code,language='python',tag="history_cell")
                state.console.run(code)

def prompt_pandora(prompt):
    with state.console_queue:
        with st.chat_message(name='user'):
            st.write(prompt)
        code=f"""
pandora.prompt(\"\"\"
{prompt}
\"\"\")
"""
        state.console.run(code)

def talk_to_pandora(audio):
    text=speech_to_text(audio)
    prompt_pandora(text)

def prepare_user_folder():
    if not os.path.exists(state.user_folder):
        os.mkdir(state.user_folder)
    if not os.path.exists(user_join('startup.py')):
        shutil.copy(root_join("startup.py"),user_join("startup.py"))
    if not os.path.exists(user_join('Pandora')):
        os.mkdir(user_join('Pandora'))
    if not os.path.exists(user_join('Pandora','memory.json')):
        shutil.copy(root_join('Pandora','memory.json'),user_join('Pandora','memory.json'))
    
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
        def on_settings_click():
            state.page='settings'
        stl.button("Settings",on_click=on_settings_click,use_container_width=True)
        
#Sets the welcome message header and help expander
def make_welcome():
    stl.subheader("Welcome to StreamPy interactive interpreter.")
    with stl.expander("Click here to get help."):
        with open(root_join("README.md"),'r') as f:
            stl.write(f.read())

#Sets the python input cell part 
def make_python_input():
    n=len(state.console.inputs)
    if state.index<=0:
        state.index=0
    elif state.index>n:
        state.index=n

    if n==0 or state.index==0:
        state.input_code=""
    else:   
        state.input_code=state.console.inputs[n-state.index]
    
    event,code=input_cell(state.input_code,lang='python',key=state.input_key,focus=True)
    if event=='submit':
        state.index=0
        run(code)
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

#Sets the pandora input cell part 
def make_pandora_input():
    event,prompt=input_cell('',key=state.pandora_input_key,lang='text',focus=True)
    a,b,c,d=stl.columns(4)
    with a:
        prev=stl.button("Previous",use_container_width=True)
    with b:
        keep_going=stl.button("Keep going!",use_container_width=True)
    with c:
        text = speech_to_text("Talk to Pandora","Stop recording",language='fr',just_once=True,use_container_width=True)
    with d:
        next=stl.button("Next",use_container_width=True)
    if keep_going:
        prompt_pandora("Keep going!")
        stl.experimental_rerun()
    if text:
        prompt_pandora(text)
        stl.experimental_rerun()
    if event=='submit':
        prompt_pandora(prompt)
        state.pandora_input_key=km.gen_key()
        stl.experimental_rerun()
        #This rerun is not ideal, as it causes a blinking of the app, but sucessful at avoiding the "missing/double widget bug" appearing in some cases, for some obscur reason...
        #I guess the issue comes from the number of mainloop turns required by streamlit to "consume" the widget
        #In case a widget needs several ones, the next call to refresh will create a duplicate until the first is consumed by streamlit
        #The issue only applies for unkeyed widgets, as I somewhat managed to remove the bug for keyed ones by adding a DuplicateWidgetID exception catching in the deferrer's refresh and stream logic

def make_input():
    if not state.APIkey=="":
        tab1,tab2=stl.tabs(["Run python code","Ask Pandora"])
        with tab1:
            make_python_input()
        with tab2:
            make_pandora_input()
    else:
        make_python_input()

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

#Displays the editor
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
                edit(user_join(state.file_name))
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
            os.remove(state.open_file)
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
                save_as(user_join(state.file_name))
                with empty:
                    stl.success("File saved.")
            with empty:
                stl.text_input("Enter name of file:",on_change=on_file_name_change,key='file_name')
    elif event=="save_as":
        def on_file_name_change():
            save_as(user_join(state.file_name))
            with empty:
                stl.success("File saved.")
        with empty:
            stl.text_input("Enter name of file:",on_change=on_file_name_change,key='file_name')
    elif event=="rename":
        def on_file_name_change():
            os.remove(state.open_file)
            save_as(user_join(state.file_name))
            with empty:
                stl.success("File renamed.")
        with empty:
            stl.text_input("Enter new name of file:",on_change=on_file_name_change,key='file_name')
    elif event=="run":
        run_editor_content()

def make_sign_up():
    def on_submit_click():
        if not state.sign_up_username=="" and not state.sign_up_password=="" and not state.sign_up_confirm_password=="" and not state.email=="" and state.sign_up_password==state.sign_up_confirm_password:
            try:
                doc=FirestoreDocument('Documents','Users')
                users=doc.load()
                emails=[users[user].get('email') for user in users]
                if not state.sign_up_username in users and not state.email in emails:
                    state.user=state.sign_up_username
                    state.password=state.sign_up_password
                    state.APIkey=None
                    users[state.user]={
                        'password':gen_lock(state.password,30),
                        'email':state.email,
                        'OpenAI_API_key':None
                    }
                    doc.dump(users)
                else:
                    stl.warning("This username / email adress is already taken.")
                
            except Exception as e:
                stl.exception(e)
                stl.warning("Something went wrong. Please try again.")    
        else:
            stl.warning("Non-empty username email and password required.")

    with stl.form("sign_up",clear_on_submit=True):
        stl.text_input("Username:",key='sign_up_username')
        stl.text_input("E-mail:",key='email')
        stl.text_input("Password:",type="password",key='sign_up_password')
        stl.text_input("Confirm password:",type="password",key='sign_up_confirm_password')
        stl.form_submit_button("Submit",on_click=on_submit_click)

def make_sign_in():
    def on_submit_click():
        if not state.sign_in_username=="" and not state.sign_in_password=="":
            try:
                doc=FirestoreDocument('Documents','Users')
                users=doc.load()
                if state.sign_in_username in users:
                    if check_lock(state.sign_in_password,users[state.sign_in_username]['password']):
                        state.user=state.sign_in_username
                        state.password=state.sign_in_password
                        if users[state.user].get('OpenAI_API_key'):
                            state.APIkey=decrypt(users[state.user]['OpenAI_API_key'],state.password)
                        else:
                            state.APIkey=None                       
                    else:
                        stl.warning("Wrong password.")
                        time.sleep(0.5)
                else:
                    stl.warning("This username doesn't exist in the database.")

            except Exception as e:
                stl.exception(e)
                stl.warning("Something went wrong. Please try again.")    
        else:
            stl.warning("Non-empty username and password required.")

    with stl.form("login",clear_on_submit=True):
        stl.text_input("Username:",key='sign_in_username')
        stl.text_input("Password:",type="password",key='sign_in_password')
        stl.form_submit_button("Submit",on_click=on_submit_click)

#Makes the webapp login page        
def make_login():
    stl.subheader("Streampy - Streamlit powered Python 3 interpreter")
    tab1,tab2=stl.tabs(["Sign-in","Sign-up"])
    with tab1:
        make_sign_in()
    with tab2:
        make_sign_up()
    with stl.container():
        stl.subheader("Latest improvements:")
        with open(os.path.join(_root_,"improvements.json")) as f:
            improvements=json.load(f)
        for i in range(1,7):
            stl.info(improvements[-i]) 

def make_settings():
    def on_submit():
        state.page="default"
        pass
    with stl.form("settings"):
        stl.subheader("Settings")
        stl.write("This is an empty settings page!")
        stl.form_submit_button("Submit",on_click=on_submit)

def make_OpenAI_API_request():
    stl.subheader("OpenAI API key")
    stl.write("To interact with Pandora (the AI assistant), you need to provide a valid OpenAI API key. This API key will be stored safely encrypted in the database, in such a way that you only can use it (not even me). If you don't provide any, Streampy will still work as a mere python console, but without the possibility to interact with the assistant.")
    def on_submit():
        state.APIkey=state.APIkey_input
        doc=FirestoreDocument('Documents','Users')
        users=doc.load()
        users[state.user].update({'OpenAI_API_key':encrypt(state.APIkey,key=state.password)})
        doc.dump(users)
        
    with stl.form("OpenAI_API_Key",clear_on_submit=True):
        stl.text_input("Please enter your OpenAI API key (leave blank if you don't want to):",type="password",key="APIkey_input")
        stl.form_submit_button("Submit",on_click=on_submit)

#Initialize the user's session
def initialize_session():
    #Initialize the user's session
    with stl.spinner("Please wait while your session is being initialized..."):
        if state.user_folder=="":
            state.user_folder=root_join("UserFiles",state.user) 
        cloud=FirebaseStorage()
        cloud.load_folder_from_cloud(state.user,state.user_folder)
        prepare_user_folder()
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
        if not state.APIkey=="" and state.pandora is None:
            from Pandora_web import Pandora
            class Utils:
                pass
            utils=Utils()
            utils.edit=edit
            utils.google_search=google_search
            state.pandora=Pandora(state.user_folder,state.console,utils)
            state.pandora.user=state.user
            state.console.send_in('pandora',state.pandora)
    state.session_has_initialized=True
    stl.experimental_rerun()

def do_log_out():
    with stl.spinner("Please wait while you're being logged-out of your session..."):
        if state.mode=="web":
            dump_to_cloud()
            shutil.rmtree(state.user_folder)
        state.open_file=None
        state.file_content=None
        state.show_editor=False
        state.user=""
        state.password=""
        state.APIkey=None
        state.user_folder=""
        state.listener=None
        state.console=None
        state.deferrer.clear()
        state.log_out=False
        state.pandora=None
        state.session_has_initialized=False
        os.chdir(_root_)
        time.sleep(2)
    stl.experimental_rerun()

#-----------------------------Main app session's logic-------------------------

if state.user=="":
    #Ask for credentials
    stl.set_page_config(layout="centered",initial_sidebar_state="collapsed")
    make_login()
elif state.APIkey is None:
    stl.set_page_config(layout="centered",initial_sidebar_state="collapsed")
    make_OpenAI_API_request()
elif not state.session_has_initialized:
    stl.set_page_config(layout="centered",initial_sidebar_state="collapsed")
    #Initialize the session
    initialize_session()
elif state.log_out:
    stl.set_page_config(layout="centered",initial_sidebar_state="collapsed")
    do_log_out()
elif state.page=="settings":
    stl.set_page_config(layout="centered",initial_sidebar_state="collapsed")
    make_settings()
else:
    #Show the app's main page
    if state.show_editor:
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
    