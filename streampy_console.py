import code
from code import InteractiveConsole
from streamlit.runtime.scriptrunner import add_script_run_ctx
from threading import Thread
from queue import Queue
import sys
import time
from contextlib import contextmanager
from echo import echo_generator

#Redirect writes to sdtout or sdterr to a target I/O object
@contextmanager
def redirect_outputs(target):
    stdout_fd=sys.stdout
    stderr_fd=sys.stderr
    sys.stdout=target
    sys.stderr=target
    yield
    sys.stdout=stdout_fd
    sys.stderr=stderr_fd

#The I/O object intercepting the interpreter's outputs. Redirects writes to a Queue (useful for thread communication).
class OutputInterceptor:
    def __init__(self):
        self.queue = Queue()
        self.buffer = ''

    def write(self, text):
        self.buffer += text # buffering until a line is finished
        if text.endswith('\n'):
            self.queue.put(self.buffer) # appends the line to the queue
            self.buffer = '' # resets buffer to empty
            while not self.queue.empty(): # Make sure the queue is emptied by the listening thread before continuing
                time.sleep(0.001)
            
    
    def get(self): # get a message from the queue
        msg=self.queue.get()
        return msg
    
    def put(self,msg): # put a message in the queue
        self.queue.put(msg)

    def flush(self):
        pass 

#The python interpreter in which the code typed in the input cell will be run
class Console(InteractiveConsole):

    def __init__(self,deferrer,names=None,startup=None):
        self.names=names or {} #synchronizes an optional outter namespace with the interpreter's one
        self.names['names']=self.names
        self.names['ME']=self
        self.deferrer=deferrer #keeps a reference to the deferrer in which streamlit calls will be queued
        self.is_running=False
        self.interceptor=OutputInterceptor()
        InteractiveConsole.__init__(self,self.names)
        self.inputs=[] # History of inputs
        self.results=[] # History of outputs
        if startup: # Runs an optional startup file
            self.runfile(startup)
            self.inputs.pop(-1)
            
        
    def send_in(self,name,obj): # send an object in the interpreter's namespace
        self.names[name]=obj   
    
    def send_out(self,name): # retrieve an object from the interpreter's namespace
        return self.names[name]

    def update(self,names): # updates the interpreter's namespace with a name:object dictionary
        self.names.update(names)
                  

    def runfile(self,path): # Runs a python file in the interpreter
        try:
            with open(path,'r') as f:
                source=f.read()
            self.run(source)
        except Exception as e:
            self.results.append([str(e)])

    def run_thread(self,source): 
    # The first thread, in which the code will be run.
    # All normal outputs redirected to the Interceptor's queue and translated as st.write calls by the listen_thread.
    # All streamlit function calls translated by the deferrer and appended in its pile.
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
        self.interceptor.put("#<DONE>#") # send a special message to the queue when finished

    def listen_thread(self): # second thread, listening to the outputs of the first one from the interceptor and handling them until the #<DONE># message is received.
        while True:
            output = self.interceptor.get()
            if output == "#<DONE>#":
                self.is_running=False
                break
            else:
                self.handle_output(output)


    def handle_output(self,output): # all outputs are converted to a st.text command and piled in the deferrer
        self.deferrer.text(output)
        self.results[-1].append(output)

    def run(self,source): # the main method to run code
        self.inputs.append(source)
        self.deferrer.echo=echo_generator(self.deferrer,source) # passes the input code to an echo_generator object and update the deferrer's echo attribute. useful to handle st.echo.
        self.results.append([])
        R=Thread(target=self.run_thread,args=(source,))
        add_script_run_ctx(R) # Make the thread aware of the streamlit session state
        L=Thread(target=self.listen_thread)
        add_script_run_ctx(L)

        self.deferrer.mode='streamed' #passes the deferrer in streamed mode (pauses code execution in the first thread until the deferrer's pile is emptied by the loop below)
        R.start() # start the run thread
        L.start() # start the listen thread
        while self.is_running or len(self.deferrer.pile)>0: # streams (=renders) piled widgets from the deferrer's pile in real time
            self.deferrer.stream()
            time.sleep(0.001)
        R.join()
        L.join()
        self.deferrer.mode='static' # resets the deferrer in static mode (so that it doesn't block execution when appending a widget)
        self.deferrer.echo=echo_generator(self.deferrer) # resets the echo attribute to normal file code input

    def get_result(self): # Quickly get the last output of the interpreter as a string.
        return '\n'.join(self.results[-1])
    