
-Implement some special streamlit calls that should'nt be queued as st_callables but rather being executed and returned directly. For instance st.column_config...
Mostly there using the st_direct_exec_callable class, still need to route some functions to this class for proper handling.

-Test thoroughly if every streamlit widget/command/syntax work properly and seamlessly.
Most basic widgets/commands/syntaxes already work, but there might be issues to adress with some special ones.

-Comment the code : Lazy me !
