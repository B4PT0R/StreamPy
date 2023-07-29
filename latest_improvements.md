# Improvements

Below are past problems that are now correctly handled :

- correct implementation of st.spinner, st.progress, st.echo, st.column_config, st.session_state

- avoid st.write's logic to fail on objects implementing __getattr__ method.

- The python interpreter doesn't run code in a thread anymore. (I realized the threaded logic was not necessary to implement real-time rendering of widgets, while the interpreter is running code. Caused useless complexity and problems to interact dynamicaly with the session_state.) This makes the overall logic saner and way less likely to cause bugs.

- Detect automaticly whether the app runs localy or on the Streamlit's cloud server. (useful to decide if user authentication is necessary)



