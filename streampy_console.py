import code
from code import InteractiveConsole
import sys
from input import readline
from contextlib import contextmanager
from echo import echo_generator

#Redirect inputs/outputs to a target I/O object
@contextmanager
def redirect_IOs(target):
    stdout_fd=sys.stdout
    stderr_fd=sys.stderr
    stdin_fd=sys.stdin
    sys.stdout=target
    sys.stderr=target
    sys.stdin=target
    yield
    sys.stdout=stdout_fd
    sys.stderr=stderr_fd
    sys.stdin=stdin_fd

#The I/O object intercepting the interpreter's outputs.
class OutputsInterceptor:
    def __init__(self,console,deferrer):
        self.deferrer=deferrer
        self.console=console
        self.buffer = ''

    def write(self, text):
        self.buffer += text # buffering until a line is finished
        if text.endswith('\n'):
            self.console.results[-1].append(self.buffer)
            self.deferrer.text(self.buffer) # appends the line as a st.text widget to the deferrer's queue
            self.buffer = '' # resets buffer to empty

    def readline(self):
        if not self.buffer=='':
            self.write('\n')
        string=readline(self.console.server)
        return string

    def flush(self):
        pass 


class Console(InteractiveConsole):
#The python interpreter in which the code typed in the input cell will be run
    def __init__(self,deferrer,server,names=None,startup=None):
        self.names=names or {} #synchronizes an optional outter namespace with the interpreter's one
        self.names['names']=self.names # allows to access this names dictionary from within the console itself
        self.names['ME']=self # allows to access the console objet itself inside it's own namespace
        self.deferrer=deferrer #keeps a reference to the deferrer in which streamlit calls will be piled
        self.server=server
        self.interceptor=OutputsInterceptor(self,self.deferrer)
        InteractiveConsole.__init__(self,self.names)
        self.inputs=[] # History of inputs
        self.results=[] # History of outputs
        if startup: # Runs an optional startup file
            self.runfile(startup)
            self.inputs.pop(-1) # Removes the startup file input from history
            
        
    def send_in(self,name,obj): # send an name:object pair in the interpreter's namespace
        self.names[name]=obj   
    
    def send_out(self,name): # retrieve an object by its name from the interpreter's namespace
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
        
    def run(self,source): 
    # the main method to run code
        self.inputs.append(source) # appends the source code to input history
        self.results.append([]) # prepares a new list of results (in which the outputs of the interpreter will be appended)
        self.deferrer.echo=echo_generator(self.deferrer,source) # passes the input code to an echo_generator object and update the deferrer's echo attribute. useful to handle st.echo.
        self.deferrer.mode='streamed' #passes the deferrer in streamed mode (widgets are rendered as soon as they are appended to the deferrer's pile)
        with redirect_IOs(self.interceptor):
            try:
                #compile the code first to check the code is correct / complete
                output = code.compile_command(source,'<input>',symbol='exec')
            except Exception as e:
                print(str(e))
            else:
                #compile_command returns None if the code is incomplete
                if not output is None:
                    self.runcode(output)
                else:
                    e=SyntaxError("Incomplete code isn't allowed to be executed.")
                    print(str(e))
        self.deferrer.mode='static' # resets the deferrer in static mode (so that it waits for a refresh to render widgets)
        self.deferrer.echo=echo_generator(self.deferrer) # resets the echo attribute to normal file code input

    def get_result(self): 
    # Quickly get the last output of the interpreter as a string.
        return '\n'.join(self.results[-1])
    