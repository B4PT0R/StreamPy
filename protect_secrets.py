import streamlit
import sys
from input import firebase_check_app_initialized  

class streamlit_with_protected_secrets:

    def __getattribute__(self,attr):
        if attr=='secrets':
            if firebase_check_app_initialized():
                return None
            else:
                return streamlit.__getattribute__(attr)
        else:
            return streamlit.__getattribute__(attr)


def protect_secrets():
    sys.modules['streamlit']=streamlit_with_protected_secrets()