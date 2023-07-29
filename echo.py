"""
Adaptation of Streamlit's echo module to fit StreamPy's interactive environment
All credits to Streamlit developers.
"""

import ast
import contextlib
import textwrap
import traceback

class echo_generator:

    def __init__(self,deferrer,source_code=None):
        self.source_code=source_code
        self.deferrer=deferrer

    @contextlib.contextmanager
    def __call__(self,code_location="above"):

        from streamlit import source_util

        if code_location == "above":
            placeholder = self.deferrer.empty()

        try:
            # Get stack frame *before* running the echoed code. The frame's
            # line number will point to the `st.echo` statement we're running.
            frame = traceback.extract_stack()[-3]
            filename, start_line = frame.filename, frame.lineno

            if self.source_code is None:
                # Read the file containing the source code of the echoed statement.
                with source_util.open_python_file(filename) as source_file:
                    source_lines = source_file.readlines()
            else:
                # Read the passed source code directly
                source_lines=self.source_code.splitlines(True)

            # Use ast to parse the Python file and find the code block to display
            root_node = ast.parse("".join(source_lines))
            line_to_node_map = {}

            def collect_body_statements(node):
                if not hasattr(node, "body"):
                    return
                for child in node.body:
                    line_to_node_map[child.lineno] = child
                    collect_body_statements(child)

            collect_body_statements(root_node)

            # In AST module the lineno (line numbers) are 1-indexed,
            # so we decrease it by 1 to lookup in source lines list
            echo_block_start_line = line_to_node_map[start_line].body[0].lineno - 1
            echo_block_end_line = line_to_node_map[start_line].end_lineno
            lines_to_display = source_lines[echo_block_start_line:echo_block_end_line]

            code_string = textwrap.dedent("".join(lines_to_display))

            # draw the code string to the app.
            if code_location=="above":
                with placeholder:
                    self.deferrer.code(code_string)

            # Run the echoed code...
            yield

            
            if not code_location=="above":
                self.deferrer.code(code_string)

        except Exception as err:
            if code_location=="above":
                with placeholder:
                    self.deferrer.warning("Unable to display code. %s" % err)
            else:
                self.deferrer.warning("Unable to display code. %s" % err)

    


