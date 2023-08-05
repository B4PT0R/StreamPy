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

class SocketIOServer:

    def __init__(self):
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

class FirestoreManager:
    def __init__(self):
        # Use a service account
        self.mode='web'
        cred_dict=dict(st.secrets['firebase_credentials'])
        with open(os.path.join(_root_path_,'credentials.json'),'w') as f:
            json.dump(cred_dict,f)
        cred = credentials.Certificate(os.path.join(_root_path_,'credentials.json'))
        cred_dict=None
        os.remove(os.path.join(_root_path_,'credentials.json'))
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        self.queue=Queue()
        self.last_ID=None

    def send_message(self,content):
        doc_ref = self.db.collection('messages').document('TEST')
        message={
            'ID':datetime.now().isoformat(),
            'content':content
        }
        doc_ref.set(message, merge=True)

    def start_listening(self):

        # Create a callback on_snapshot function to capture changes
        def on_snapshot(doc_snapshot, changes, read_time):
            doc = doc_snapshot[0]
            ID=doc.to_dict().get("ID")
            if not ID==self.last_ID:
                self.last_ID=ID
                self.queue.put(doc.to_dict().get("content"))
            
        # Watch the document
        doc_ref = self.db.collection('messages').document('TEST')
        doc_watch = doc_ref.on_snapshot(on_snapshot)
        time.sleep(1)
        self.queue=Queue()

    def get_message(self):
        return self.queue.get()
    
def Listener(mode=None):
    if mode=='web':
        return FirestoreManager()
    elif mode=='local':
        return SocketIOServer()


def readline(deferrer=None,listener=None):
    if listener.mode=='web':
        file='input_web.txt'
    elif listener.mode=='local':
        file='input_local.txt'
    with open(os.path.join(_root_path_, file)) as f:
        js_code = f.read()
    deferrer.html(js_code, height=53)
    string = listener.get_message()
    return string
