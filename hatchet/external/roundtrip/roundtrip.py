from __future__ import print_function
from IPython.core.magic import Magics, magics_class, line_magic
from IPython.display import HTML, Javascript, display

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

        fileAndPath = ""
        if path[-1] == "/":
            fileAndPath = path + "roundtripTree.js"
        else:
            fileAndPath = path + "/roundtripTree.js"

        javascriptFile = open(fileAndPath).read()

        # Source input files
        # Set up the object to map input files to what javascript expects
        argList = "<script> var argList = []; var elementTop = null; var cell_idx = -1;</script>"

        displayObj = display(HTML(argList), display_id=True)

        args[1] = self.shell.user_ns[args[1]]
        displayObj.update(Javascript('argList.push("' + str(args[1]) + '")'))

        # Get curent cell id
        self.codeMap[name] = javascriptFile

        preRun = """
        // Grab current context
        elementTop = element.get(0);"""
        displayObj.update(Javascript(preRun))

        self.runVis(name, javascriptFile)
        self.id_number += 1

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
