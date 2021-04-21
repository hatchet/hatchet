import inspect
import os
import json
from datetime import datetime
import hatchet

class Log(object):    
    def __init__(self, filename="hatchet_log.json", active=True):
        self._log_file = filename
        self._active = active

    def set_output_file(self, filename=""):
        self._log_file = filename

    def set_active(self):
        self._active = True
    
    def set_inactive(self):
        self._active = False

    def append_to_file(self, log):
        logs = []
        if os.path.exists(self._log_file):
            with open(self._log_file, 'r') as f:
                logs = json.loads(f.read())
        
        logs.append(log)
        with open(self._log_file, 'w+') as f:
                f.write(json.dumps(logs))    

    def loggable(self, function):
        '''A decrator which logs calls to hatchet functions'''
        def inner(*args, **kwargs):
            if self._active:
                
                log_dict = {}    
                arg_list = []
                graphframe_metadata = {}

                for i, arg in enumerate(args):
                    if(inspect.isfunction(arg)):
                        arg_source = inspect.getsource(arg)
                        arg_list.append(arg_source)
                    elif isinstance(arg, hatchet.GraphFrame):
                        graphframe_metadata['rows'] = arg.dataframe.shape[0]
                        graphframe_metadata['nodes'] = len(arg.graph)
                        # arg_list.append(arg)
                    else:
                        arg_list.append(arg)
                
                log_dict['graphframe_metadata'] = graphframe_metadata
                log_dict['args'] = tuple(arg_list)
                log_dict['start'] = datetime.now().isoformat()
                
                holder =  function(*args, **kwargs)

                log_dict['end'] = datetime.now().isoformat()
                log_dict['function'] = function.__name__
                log_dict['kwargs'] = kwargs

                self.append_to_file(log_dict)

                return holder
            else:
                return function(*args, **kwargs)

        return inner

Logger = Log()