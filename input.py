import os
import firebase_admin
from firebase_admin import credentials, firestore
import time
from datetime import datetime
import socketio
import eventlet
from threading import Thread 
from queue import Queue
import streamlit as st
import json
_root_path_=os.path.dirname(os.path.abspath(__file__))

#This module is for implementing stdin redirection

class SocketIOListener:
    #SocketIO server/listener for local communication between streamlit and the front-end input widget

    def __init__(self,session_id):
        self.session_id=session_id
        self.mode='local'
        self.queue=Queue()
        self.sio = socketio.Server(cors_allowed_origins='*')
        self.app = socketio.WSGIApp(self.sio)
        @self.sio.on('connect')
        def connect(sid, environ):
            pass
        @self.sio.on('message')
        def message(sid, data):
            self.queue.put(data)
        self.server_thread=None
        self.server = None
        self.is_running=False
    
    def start_listening(self):
        if not self.is_running:
            self.server=eventlet.listen(('', 5000))
            self.server_thread = Thread(target=eventlet.wsgi.server, args=(self.server, self.app),daemon=True)
            self.server_thread.start()
            self.is_running=True

    def get_message(self):
        return self.queue.get()


def firebase_check_app_initialized():
    try:
        firebase_admin.get_app()
    except ValueError:
        return False
    else:
        return True

def firebase_admin_init_app(cred):
    try:
        return firebase_admin.get_app()
    except ValueError:
        pass
    cred_dict=dict(st.secrets['firebase_credentials'])
    with open(os.path.join(_root_path_,'credentials.json'),'w') as f:
        json.dump(cred_dict,f)
    app=firebase_admin.initialize_app(firebase_admin.credentials.Certificate(os.path.join(_root_path_,'credentials.json')))
    os.remove(os.path.join(_root_path_,'credentials.json'))
    return app                                  
    



class FirestoreListener:
    #Firestore listener to implement the same thing when the app is served on streamlit's cloud 
    def __init__(self,session_id):
        self.mode='web'
        self.session_id=session_id
        firebase_admin_init_app(st.secrets['firebase_credentials'])
        self.db = firestore.client()
        self.queue=Queue()
        self.last_ID=None
        doc_ref = self.db.collection('messages').document(self.session_id)
        if not doc_ref.get().exists:
            doc_ref.set({'ID': '', 'content': ''})

    def send_message(self,content):
        doc_ref = self.db.collection('messages').document(self.session_id)
        message={
            'ID':datetime.now().isoformat(),
            'content':content
        }
        doc_ref.set(message)

    def start_listening(self):

        # Create a callback on_snapshot function to capture changes
        def on_snapshot(doc_snapshot, changes, read_time):
            doc = doc_snapshot[0]
            message=doc.to_dict()
            ID=message.get("ID")
            if not ID==self.last_ID:
                self.last_ID=ID
                self.queue.put(message.get("content"))
            
        # Watch the document
        doc_ref = self.db.collection('messages').document(self.session_id)
        doc_watch = doc_ref.on_snapshot(on_snapshot)
        time.sleep(1)
        self.queue=Queue()

    def get_message(self):
        return self.queue.get()
    
def Listener(session_id,mode=None):
    if mode=='web':
        return FirestoreListener(session_id)
    elif mode=='local':
        return SocketIOListener(session_id)

#to redirect stdin.readline to a custom widget on the front end
def readline(deferrer=None,listener=None):
    #different html code for the input widget depending on the situation
    if listener.mode=='web':
        file='input_web.html'
    elif listener.mode=='local':
        file='input_local.html'
    with open(os.path.join(_root_path_, file),'r') as f:
        html_code = f.read()
    #render the widget
    deferrer.html(html_code.replace('#SESSION_ID#',listener.session_id), height=53)
    #wait for the output of the widget
    string = listener.get_message() 
    return string
