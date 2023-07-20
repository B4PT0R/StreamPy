#Allows for easier implementation of third party components in the streamlit_deferrer module

"""Structure of ImportDict : 
    {
        component_key : {"module":module_name,"component":component_name},
        ...
    }
"""

ImportDict={
    "ace":{"module":"streamlit_ace","component":"st_ace"}
    #add your components here
}

#This function will import the components from their modules and return a COMPONENTS dictionary to access the corresponding objects
def ImportComponents():
    COMPONENTS={}
    for key in ImportDict:
        module = __import__(ImportDict[key]["module"], globals(), locals(), [ImportDict[key]["component"]], 0)
        COMPONENTS[key] = getattr(module, ImportDict[key]["component"])
    return COMPONENTS

