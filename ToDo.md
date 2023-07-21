-Test thoroughly if every streamlit widget/command/syntax work properly and seamlessly.
Most basic widgets/commands/syntaxes already work, but there are issues to adress with some special ones.

-Adress the "missing widget bug" appearing in some cases. (First find a snippet that reproduces the bug)

-Implement automatic key attribution for compatible widgets in case the user doesn't provide any (avoid weird widget's behavior)

-Use a special components.py module to ease implementing user-chosen third party streamlit components.

-Problems encountered with the _repr_html_ callback when using st.write on objects implementing _getattr_
(_repr_html_ gets handled by _getattr_ which prevents streamlit to proceed with default html representation of the object) 

