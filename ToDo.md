-Find a way to avoid rerunning the main script when hitting the run button (Did this to work around a refresh bug - some widgets don't update adequately after the console has run the code and streamed widgets creation).

The rerunning results in an unpretty blinking of the app after the code has finished running.

-Find a way to implement seamlessly st.progress and st.spinner in the streamlit_deferrer module.

So far they're not working properly.

-Implement some special streamlit calls that should'nt be queued as st_callables but rather being executed and returned directly. For instance st.column_config...
Mostly there using the st_direct_exec_callable class, still need to route some functions to this class for proper handling.

-Test thoroughly if every streamlit widget/command/syntax work properly and seamlessly.
Most basic widgets/commands/syntaxes already work, but there might be issues to adress with some special ones.

-Commenting the code : Lazy me !
