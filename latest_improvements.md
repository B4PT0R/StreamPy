# Improvements

Below are past problems that are now correctly handled :

- correct implementation of st.snow, st.balloons, st.spinner, st.progress, st.echo, st.column_config, st.session_state

- avoid st.write's logic to fail on objects implementing __getattr__ method.

- The python interpreter doesn't run code in a thread anymore. (I realized the threaded logic was not necessary to implement real-time rendering of widgets, while the interpreter is running code. Caused useless complexity and problems to interact dynamicaly with the session_state.) This makes the overall logic saner and way less likely to cause bugs.

- Detect automaticly whether the app runs localy or on the Streamlit's cloud server. (useful to decide if user authentication is necessary)

- automatic unique key attribution for compatible widgets in case the user doesn't provide any.

- possibility to hide/show dynamicly the past input cells in the console queue.

- Implemented stdin redirection to a custom javascript widget in the app. Allows to use python 'input' command (and run any script using this feature).

- Improve security by restricting access to some modules/attributes for code run by the user from the interactive interpreter

- Provide cloud storage for user files.





