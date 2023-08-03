import streamlit.components.v1 as components
import socketio
import eventlet
from threading import Thread 
from queue import Queue

class SocketIOServer:

    def __init__(self):
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
    
    def start(self):
        if not self.is_running:
            self.server=eventlet.listen(('', 5000))
            self.server_thread = Thread(target=eventlet.wsgi.server, args=(self.server, self.app),daemon=True)
            self.server_thread.start()
            self.is_running=True


def modal_input():
    js_code = f"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
    var socket = io.connect('http://localhost:5000');
    </script>
    <input id="myInput" style="width: 100%; box-sizing: border-box; padding: 10px; border-radius: 4px;">
    <script>
    document.getElementById("myInput").addEventListener("keyup", function(event) {{
        if (event.keyCode === 13) {{
            sendMessage();
        }}
    }});

    function sendMessage() {{
        var input = document.getElementById('myInput');
        input.disabled = true;
        socket.emit('message', input.value);
    }}
    </script>
    """
    return components.html(js_code, height=53)

def readline(server=None):
    modal_input()
    string = server.queue.get()
    return string


