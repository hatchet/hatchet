from __future__ import print_function
from IPython.core.magic import (Magics, magics_class, line_magic,
                                cell_magic, line_cell_magic)
from IPython.display import (HTML, Javascript, Markdown, display, clear_output)

'''
   File: Interface.py
   Purpose: Test interface between 
'''
@magics_class
class Interface(Magics):

    # Note to self: Custom magic classes MUST call parent's constructor
    def __init__(self, shell):
        requireInfo = open("require.config").read()
        display(Javascript("require.config({ \
                                            baseUrl: './', \
                                            paths: { "+requireInfo+"} });"))
        super(Interface, self).__init__(shell)
        # Clean up namespace function
        display(HTML("<script>function cleanUp() { argList =[]; element = null; cell_idx = -1}</script>"))
        display(HTML("<style>.container { width:100% !important; }</style>"))
                
    inputType = {"js": "text/javascript",
                 "csv": "text/csv",
                 "html": "text/html",
                 "json": "text/json",
                 "css": "text/css"}
    codeMap = {}
    
    @line_magic
    def loadVisualization(self, line):
        # Get command line args for loading the vis
        args = line.split(" ")
        name = args[0]
        javascriptFile = open(args[1]).read()
        #self.codeMap[name] = javascriptFile
        # Source input files
        # Set up the object to map inout files to what javascript expects
        argList = '<script> var argList = []; var elementTop = null; var cell_idx = -1</script>'
        displayObj = display(HTML(argList), display_id=True)
        for i in range(2, len(args), 1):
            if("%" in args[i]):
                #print(self.shell.user_ns[args[i][1:]])
                args[i] = self.shell.user_ns[args[i][1:]]
            if(isinstance(args[i], str) and "." in args[i]):
                if("." in args[i] and args[i].split(".")[1] in self.inputType.keys()):
                    displayObj.update(HTML("<script src=" + args[i] + " type=" + self.inputType[args[i].split(".")[1]] +"></script>"))
                if(args[i].split(".")[1] == "html" or args[i].split(".")[1] == "css"):
                    fileVal = open(args[i]).read()
                    display(HTML(fileVal))
            if(isinstance(args[i], str) and "\"" in args[i]):
                args[i] = args[i].replace("\"", "\\\"")
            if(isinstance(args[i], str) and "\n" in args[i]):
                args[i] = args[i].replace("\n", "\\n")
            displayObj.update(Javascript('argList.push("' + str(args[i]) + '")')) 
        # Get curent cell id
        self.codeMap[name] = javascriptFile
        preRun = """
        // Grab current context
        elementTop = element.get(0);"""
        displayObj.update(Javascript(preRun))
        self.runViz(name, javascriptFile)
   
    def runViz(self, name, javascriptFile):
        header = """
                  <div id=\""""+name+"""\"></div>
                  <script>
                  elementTop.appendChild(document.getElementById('"""+str(name)+"""'));
                  element = document.getElementById('"""+str(name)+"""');"""
        footer = """</script>"""
        display(HTML(header + javascriptFile + footer))
    
    @line_magic
    def fetchData(self, line):
        args = line[1:-1].split()
        location = args[0][:-1]
        dest = args[1][:-1]
        source = args[2] #in JS: jsNodeSelected
        
        #display(Javascript('console.log("WE HAVE NEWLINES", '+source+')'))

        hook = """
                var holder = """+str(source)+""";
                holder = '"' + holder + '"';
                
                //console.log('holder:', holder);
                IPython.notebook.kernel.execute('"""+str(dest)+""" = '+ holder);
                //console.log('"""+str(dest)+""" = '+ holder);
               """
        display(Javascript(hook))
        
            
# Function to make module loading possible
def load_ipython_extension(ipython):
    ipython.register_magics(Interface)
