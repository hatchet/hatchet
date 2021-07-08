from __future__ import print_function
from IPython.core.magic import Magics, magics_class, line_magic
from IPython.display import HTML, Javascript, display
import os

"""
   File: roundtrip.py
   Purpose: Pass data between Jupyter Python cells and
   Javascript variables.
   Hatchet-specific.
"""


@magics_class
class Roundtrip(Magics):

    # Note to self: Custom magic classes MUST call parent's constructor
    def __init__(self, shell):
        super(Roundtrip, self).__init__(shell)
        self.id_number = 0
        # Clean up namespace function
        display(
            HTML(
                "<script>function cleanUp() { argList =[]; element = null; cell_idx = -1}</script>"
            )
        )

    inputType = {
        "js": "text/javascript",
        "csv": "text/csv",
        "html": "text/html",
        "json": "text/json",
        "css": "text/css",
    }
    codeMap = {}

    @line_magic
    def loadVisualization(self, line):
        # Get command line args for loading the vis
        args = line.split(" ")
        name = "roundtripTreeVis" + str(self.id_number)
        path = ""
        if '"' in args[0]:
            path = args[0].replace('"', "")
        elif "'" in args[0]:
            path = args[0].replace("'", "")
        else:
            # Path is a variable from the nb namespace
            path = self.shell.user_ns[args[0]]

        visToFileMapping = {
            "literal_tree": "roundtripTree.js",
            "boxplot": "boxplot.js"
        }

        fileAndPath = os.path.join(path, visToFileMapping[args[1]])
        javascriptFile = open(fileAndPath).read()

        # Source input files
        # Set up the object to map input files to what javascript expects
        argList = "<script> var argList = []; var elementTop = null; var cell_idx = -1;</script>"

        displayObj = display(HTML(argList), display_id=True)

        data = self.shell.user_ns[args[1]]
        displayObj.update(Javascript('argList.push("' + str(path) + '")'))
        displayObj.update(Javascript('argList.push("' + str(data) + '")'))


        dataValidation = {
            "literal_tree": self._validate_literal_tree,
            "boxplot": self._validate_boxplot
        }

        dataValidation[args[1]](data)

        # Get curent cell id
        self.codeMap[name] = javascriptFile

        preRun = """
        // Grab current context
        elementTop = element.get(0);"""
        displayObj.update(Javascript(preRun))

        self.runVis(name, javascriptFile)
        self.id_number += 1

    def _validate_literal_tree(self, data):
        # Check that users provided a tree literal
        if not isinstance(data, list):
            print(
                """The argument is not a tree literal or it is not a valid Python list. Please check that you have provided a list of nodes and nested children of the following form to loadVisualization:
                    literal_tree = [{
                        "frame": {"name": "foo", "type": "function"},
                        "metrics": {"time (inc)": 130.0, "time": 0.0},
                        "children":[ . . . ]
                    },
                    {
                        "frame": {"name": "bar", "type": "function"},
                        "metrics": {"time (inc)": 30.0, "time": 0.0},
                        "children":[ . . . ]
                    }]
            """
            )
            raise Exception("Bad argument")

    def _validate_boxplot(self, data):
        pass

    def runVis(self, name, javascriptFile):
        name = "roundtripTreeVis" + str(self.id_number)
        header = (
            """
                  <div id=\""""
            + name
            + """\"></div>
                  <script>
                  elementTop.appendChild(document.getElementById('"""
            + str(name)
            + """'));
                  element = document.getElementById('"""
            + str(name)
            + """');"""
        )
        footer = """</script>"""
        display(HTML(header + javascriptFile + footer))

    @line_magic
    def fetchData(self, dest):
        # added eval() to 'execute' the JS list-as-string as a Python list

        hook = (
            """
                var holder = jsNodeSelected;
                holder = '"' + holder + '"';
                IPython.notebook.kernel.execute('"""
            + str(dest)
            + """ = '+ eval(holder));
                //console.log('"""
            + str(dest)
            + """ = '+ holder);
               """
        )

        display(Javascript(hook))

        return display(Javascript(hook))


# Function to make module loading possible
def load_ipython_extension(ipython):
    ipython.register_magics(Roundtrip)
