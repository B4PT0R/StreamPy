import code
from code import InteractiveConsole
from streamlit.runtime.scriptrunner import add_script_run_ctx
from threading import Thread
from queue import Queue
import sys
import time
from contextlib import contextmanager

@contextmanager
def redirect_outputs(target):
    stdout_fd=sys.stdout
    stderr_fd=sys.stderr
    sys.stdout=target
    sys.stderr=target
    yield
    sys.stdout=stdout_fd
    sys.stderr=stderr_fd

class OutputInterceptor:
    def __init__(self):
        self.queue = Queue()
        self.buffer = ''

    def write(self, text):
        self.buffer += text
        if text.endswith('\n'):
            self.queue.put(self.buffer)
            self.buffer = ''
            while not self.queue.empty():
                time.sleep(0.001)
            
    
    def get(self):
        output=self.queue.get()
        return output
    
    def put(self,msg):
        self.queue.put(msg)

    def flush(self):
        pass 


class Console(InteractiveConsole):

    def __init__(self,deferrer,names=None,startup=None):
        self.names=names or {}
        self.names['names']=self.names
        self.names['ME']=self
        self.deferrer=deferrer
        self.is_running=False
        self.interceptor=OutputInterceptor()
        InteractiveConsole.__init__(self,self.names)
        self.inputs=[]
        self.results=[]
        if startup:
            self.runfile(startup)
            self.inputs.pop(-1)
            
        
    def send_in(self,name,obj):
        self.names[name]=obj   
    
    def send_out(self,name):
        return self.names[name]

    def update(self,names):
        self.names.update(names)
                  

    def runfile(self,path):
        try:
            with open(path,'r') as f:
                source=f.read()
            self.run(source)
        except Exception as e:
            self.results.append([str(e)])

    def run_thread(self,source):
        self.is_running=True
        with redirect_outputs(self.interceptor):
            try:
                output = code.compile_command(source,'<input>',symbol='exec')
            except Exception as e:
                print(str(e))
            else:
                if not output is None:
                    self.runcode(output)
                else:
                    e=SyntaxError("Incomplete code isn't allowed to be executed.")
                    print(str(e))
        self.interceptor.put("#<DONE>#")

    def listen_thread(self):
        while True:
            output = self.interceptor.get()
            if output == "#<DONE>#":
                self.is_running=False
                break
            else:
                self.handle_output(output)


    def handle_output(self,output):
        self.deferrer.text(output)
        self.results[-1].append(output)

    def run(self,source):
        self.inputs.append(source)
        self.results.append([])
        R=Thread(target=self.run_thread,args=(source,))
        add_script_run_ctx(R)
        L=Thread(target=self.listen_thread)
        add_script_run_ctx(L)

        self.deferrer.mode='streamed'
        R.start()
        L.start()
        while self.is_running or len(self.deferrer.pile)>0:
            self.deferrer.stream()
            time.sleep(0.001)
        R.join()
        L.join()
        self.deferrer.mode='static'

    def get_result(self):
        return '\n'.join(self.results[-1])
    
    def print_result(self):
        for line in self.results[-1]:
            print(line)