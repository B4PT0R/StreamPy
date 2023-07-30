# StreamPy
Streamlit-based interactive python console

StreamPy is a web-based Python 3 interactive interpreter empowered by the rich input/output environment provided by Streamlit.
It is meant to upgrade the classic terminal-based Python REPL by incorporating modern-era interactivity and visualization possibilities.

To use it on your local machine, first clone [this repository](https://github.com/B4PT0R/StreamPy) to a local folder, cd to this folder and install the requirements :
```bash
$ pip install -r requirements.txt
```

You can now run StreamPy:
```bash
$ streamlit run streampy.py 
```
A local web-server will launch and the app will open in your web-browser.

Alternatively, the app is available as a test version online if you wanna try:
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streampy.streamlit.app/)

Usage is pretty straightforward. Just type your python commands/scripts in the input cell and click "Run" to get the results.

The main feature of StreamPy is the possibility to run Streamlit commands in the input cell as you would normaly do in a Streamlit script. 
The widgets will be outputted dynamicaly in the interactive console queue.

No need to import streamlit, the 'st' prefix preloaded in the console namespace is a special helper object that will take care of dealing with Streamlit calls adequately. Beware that importing streamlit as 'st' would overwrite this object and break the app's functionality.

For example, try to run the following snippets in the console, demonstrating the basic features of StreamPy and Streamlit:

```python
import matplotlib.pyplot as plt
import numpy as np

arr = np.random.normal(1, 1, size=100)
fig, ax = plt.subplots()
ax.hist(arr, bins=20)

st.pyplot(fig)
```

```python
import pandas as pd

data_df = pd.DataFrame(
    {
        "sales": [
            [0, 4, 26, 80, 100, 40],
            [80, 20, 80, 35, 40, 100],
            [10, 20, 80, 80, 70, 0],
            [10, 100, 20, 100, 30, 100],
        ],
    }
)

st.data_editor(
    data_df,
    column_config={
        "sales": st.column_config.LineChartColumn(
            "Sales (last 6 months)",
            width="medium",
            help="The sales volume in the last 6 months",
            y_min=0,
            y_max=100,
         ),
    },
    hide_index=True,
)
```
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
Let's discuss this last one. It creates 3 columns, places a text_input widget in the first, a button in the second that will trigger the writing of the text content in an empty placeholder in the third column.
Type some text and click the button to see what happens.

Note that, contrary to normal Streamlit syntax, txt is not refering directly to the text content string of the text_input widget, but is rather an object placeholder for the (future!) content of this text_input. It will be actualized in real-time if the content changes, and you may retrieve its value at any time by accessing its .value property, as in the snippet.

Even though the Python interpreter maintains its session state, you can still use st.session_state as you would in a Streamlit script.

To ease widget's keys managment, feel free to use the implemented key generator:
```python
my_text_input_key=st.gen_key()
st.text_input("Enter text here:",key=my_text_input_key)
``` 
This will generate a unique key for your widget's state that you may latter access via :
```python
my_text_input_state=st.session_state[my_text_input_key]
```

If you don't provide any key for your widget, a unique key will be attributed to it automaticly, but you will loose the possibility to know which.

All renderable widgets also implement a tag property. The tag defaults to the name of corresponding streamlit attribute.
For instance, a st.text_input object will be associated to the tag='text_input' by default. If you want to, you may choose the tag to which your widget is associated by adding a tag kwarg to its arguments when calling it:
```python
st.text_input("Enter text",tag='mytextinput')
```

This is useful to hide/show some widgets/groups of widgets dynamicaly in the console queue. For this purpose you may use:
```python
st.hide(tag)
st.show(tag)
```
This will hide/show all widgets with the chosen tag.

Apart from this, it's just normal Python and Streamlit commands!

Refer to [Streamlit documentation](https://docs.streamlit.io/library/api-reference) to get more informations on possible commands and how to use them. Most snippets provided in the examples will be working directly in the console (provided you skip the "import streamlit as st" line and use the .value attribute to access widgets outputs).

These shortcut functions are predeclared in the console's namespace:

-clear() - clears the console's queue

-restart() - restarts python session to its startup state

-edit(file='buffer') - opens a file in the editor. Just calling edit() will open an unnamed text buffer.

-close_editor() - closes the editor.

In the side Menu, you'll be able to open a basic text editor to edit/save longer scripts as well as running them in the console.
The 'Restart Session' button will reinitialize the python session to its startup state.
The 'Show/Hide history cells' button makes possible to choose whether to see or not the past input cells in the console's queue.

Worth being noted: The python session runs a startup.py script at startup. You can customize this file to your likings (accessible via the "Open" button of the editor). Useful to import common modules, define your favorite functions or classes, or serve as an entry point to preload other chosen scripts automaticly when the session starts.

---Note for developers---

StreamPy features a special streamlit_deferrer module which is crucial to manage dynamic widget rendering in the console queue. It functions by encoding streamlit calls, piling them to a queue, and render the queue (which means actualy executing the corresponding streamlit commands) when appropriate. This allows to deal with (almost...) all Streamlit functions and syntaxes interactively for a seamless integration in the StreamPy interactive console. 

For more details on how it works, check the streamlit_deferrer_explanation.md file in the repo and the module's code.

The project is mostly working but still an early prototype and have not yet been thoroughly tested. Some widgets/syntaxes may not work properly (most will) and you may run into errors or undesired behaviour. If you want to report a bug or feel like contributing to the project, feel free to check the [GitHub repository](https://github.com/B4PT0R/StreamPy) or reach me out directly at bferrand.maths@gmail.com. Any contribution to the project will be met with enthusiasm and gratitude. :)

StreamPy is only the first part of a larger project. My goal is to include an LLM agent with coding capabilities, that will have the session in context (including user inputs in the console as well as feedbacks from the interpreter), will be able to run code, interact with the editor and use streamlit widgets profitably for richer output and interactivity. So stay tuned!

Happy testing!
