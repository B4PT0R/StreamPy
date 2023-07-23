# StreamPy
Streamlit-based interactive python console

StreamPy is a Python 3 interactive interpreter empowered by the rich input/output environment provided by Streamlit.

To use it, first install the required packages via pip.
```bash
$ pip install streamlit, streamlit-ace
```

Then copy [this repository](https://github.com/B4PT0R/StreamPy) to a local folder, cd to this folder and run :
```bash
$ streamlit run streampy.py 
```
A local web-server will launch and the app will open in your web-browser.

Alternatively, the app is available in demo mode [here](https://streampy.streamlit.app/) if you wanna try.

Usage is pretty straightforward. Just type your python commands/scripts in the input cell and click "Run" to get the results.

Feel free to use Streamlit commands in your scripts with preloaded prefix 'st', as you would normaly do in a Streamlit script. 
The widgets will be outputted automaticly at the right place in the interactive console queue.

No need to import streamlit in your scripts, the 'st' prefix preloaded in the console is a special helper object that will take care of dealing with streamlit calls adequately. Importing streamlit as 'st' would overwrite this object and break the app's functionning.

As an example, try to run the following snippet in the console, demonstrating the basic features of streamlit:
```python
c1,c2,c3=st.columns(3)
with c1:
    txt=st.text_input(label="Enter text here:")
with c2:
    def on_button_click():
        with placeholder:
            st.write("You entered: "+txt.value)
    st.button("Click Me!",on_click=on_button_click)
with c3:
    placeholder=st.empty()
```
It creates 3 columns, places a text_input widget in the first, a button in the second that will trigger the writing of the text content in an empty placeholder in the third column.
Type some text and click the button to see what happens.

Note that, contrary to normal Streamlit syntax, txt is not refering directly to the text content string of the text_input widget, but is rather an object placeholder for the (future!) content of this text_input. It will be actualized in real-time if the content changes, and you may retrieve its value at any time by accessing its 'value' property, as in the snippet.

Even though the Python interpreter maintains its session state, you may want to use st.session_state as you would in a Streamlit script.

To ease widget's keys managment, feel free to use the implemented key generator:
```python
my_text_input_key=st.gen_key()
st.text_input("Enter text here:",key=my_text_input_key)
``` 
This will generate a unique key for your widget's state that you may latter access via :
```python
my_text_input_state=st.session_state[my_text_input_key]
``` 
Apart from this, it's just normal Python and Streamlit commands!

Refer to [Streamlit documentation](https://docs.streamlit.io/library/api-reference) to get more informations on possible commands and how to use them. Most snippets provided in the examples will be working directly in the console (provided you skip the "import streamlit as st" line and use the .value attribute to access widgets outputs).

In the side Menu, you'll be able to open a basic text editor to edit/save longer scripts as well as running them in the console.
The 'Restart Session' button will reinitialize the python session to its startup state.

Worth being noted: The python session runs the startup.py script (found in the /UserFiles folder) at startup. Useful to import common modules, define your favorite functions or classes, or serve as an entry point to preload other chosen scripts automaticly when the session starts.

---Note for developers---

StreamPy features a special streamlit_deferrer module I designed which is crucial to manage interactivity and widget rendering in the console queue. It functions by encoding streamlit calls, piling them to a queue, and render the queue (which means actualy executing the corresponding streamlit commands) when appropriate. This allows running (almost...) all Streamlit functions and syntaxes interactively for a seamless integration in the StreamPy interactive console. This is what happens under the hood when you run streamlit commands in the console using the 'st' prefix. 
The 'st' prefix preloaded in the console is a st_deferrer class instance from the streamlit_deferrer module, not streamlit module itself. 
Beware that importing streamlit as st in your scripts will overwrite the prefix with normal streamlit module and break the console's functionalities.

For more details on how it works, check the streamlit_deferrer_explanation.md file in the repo or the module's code directly.

StreamPy is only the first part of a larger project. My goal is to include an LLM agent (GPT4) with coding capabilities, that will have the session in context (including user inputs in the console as well as feedbacks from the interpreter), will be able to run code, interact with the editor and use streamlit widgets profitably for richer output and interactivity. This python-specialized LLM agent is almost finished and working fine, it just needed this kind of interactive interface to leverage its full potential, so stay tuned !

The project is mostly working but still an early prototype and have not yet been thoroughly tested. Some widgets/syntaxes may not work properly (most will) and you may run into errors or undesired behaviour. If you want to report a bug or feel like contributing to the project, feel free to check the [GitHub repository](https://github.com/B4PT0R/StreamPy) or reach me out directly at bferrand.maths@gmail.com. Any contribution to the project will be met with enthusiasm and gratitude. :)

Happy testing!
