import importlib

def protect_secrets(name, globals=None, locals=None, fromlist=(), level=0):

    if name == 'streamlit':
        module=importlib.__import__(name, globals, locals, fromlist, level)
        module.secrets=None
        return module
    else:
       return importlib.__import__(name, globals, locals, fromlist, level)

__builtins__['__import__'] = protect_secrets