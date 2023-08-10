import traceback
import importlib
import sys

#Module used to restrict access to a given module's subset of attributes for code run by the user in the interactive console

#Determine if the current code being executed is run by the user from the interactive interpreter by examining the traceback stack
def is_run_by_user():
    return "user" in [frame.filename for frame in traceback.extract_stack()]

#Function that restricts whole or part of a module's attributes
def restrict_module(module_name,restricted_attributes='all',allowed_attributes=[]):
    module=importlib.import_module(module_name)
    if restricted_attributes=='all':
        def is_restricted(attr):
            return not attr in allowed_attributes
    else:
        def is_restricted(attr):
            return attr in restricted_attributes and not attr in allowed_attributes

    class restricted_module:
        def __getattribute__(self,attr):
            if is_restricted(attr):
                if is_run_by_user():
                    raise AttributeError(f"Access to this attribute is restricted: {attr}")
                else:
                    return module.__getattribute__(attr)
            else:
                return module.__getattribute__(attr)
            
    sys.modules[module_name]=restricted_module()    


