-Test thoroughly if every streamlit widget/command/syntax work properly and seamlessly.
Most basic widgets/commands/syntaxes already work, but there may be issues to adress with some special ones.

-Adress the "missing/double widget bug" appearing in some cases (without using experimental_rerun would be neat!).

-Implement automatic key attribution for compatible widgets in case the user doesn't provide any (avoid weird widget's behavior)

-Improve the editor functionalities (open several files in tabs)

-Improve robustness via adequate exception handling

-Find a way to intercept whenever the Python's interperter is waiting for an input in stdin via a text_input widget (would allow to use 'input' command seamlessly) 
