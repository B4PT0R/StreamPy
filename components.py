import json
import os
import streamlit.components.v1 as components
_root_=os.path.dirname(os.path.abspath(__file__))
def root_join(*args):
    return os.path.join(_root_,*args)


#components.json allows for easier implementation of third party components in the streamlit_deferrer module

"""
Structure of components.json : 
{
    component_key : {"module":module_name,"component":component_name,"type":st_object_subtype},
    #add your components here
    ...
}
"""

#Loads the components dictionary from components.json
def load_components_dict():
    with open(root_join("components.json"),'r') as f:
        ComponentsDict=json.load(f)
    return ComponentsDict


#This function imports the components from their modules and return a COMPONENTS dictionary allowing to access the corresponding objects by their keys
def ImportComponents(ComponentsDict):
    COMPONENTS={}
    for key in ComponentsDict:
        module = __import__(ComponentsDict[key]["module"], globals(), locals(), [ComponentsDict[key]["component"]], 0)
        COMPONENTS[key] = getattr(module, ComponentsDict[key]["component"])
    return COMPONENTS

ComponentsDict=load_components_dict()
COMPONENTS=ImportComponents(ComponentsDict)

SPECIAL={
    "html":components.html,
    "iframe":components.iframe
}

COMPONENTS.update(SPECIAL)

#This dictionary maps the built-in streamlit attributes to the adequate st_object subtype used by the deferrer
ATTRIBUTES_MAPPING = {
    "add_rows": "st_callable",
    "altair_chart": "st_callable",  
    "area_chart": "st_callable",
    "audio": "st_callable",
    "balloons": "st_balloons", 
    "bar_chart": "st_callable",
    "bokeh_chart": "st_callable",
    "button": "st_callable",
    "cache_data": "st_callable",
    "cache_resources": "st_callable",
    "camera_input": "st_callable",  
    "caching_clear_cache": "st_callable",
    "checkbox": "st_callable",
    "chat_input": "st_callable",
    "chat_message": "st_callable",
    "code": "st_callable",
    "color_picker": "st_callable",
    "column_config":"st_direct_property",
    "columns": "st_unpackable_callable",
    "container": "st_callable",
    "cursor_hide_cursor": "st_callable",
    "cursor_show_cursor": "st_callable",
    "date_input": "st_callable",
    "dataframe": "st_callable",
    "data_editor":"st_callable",
    "deck_gl_chart": "st_callable",
    "deck_gl_json_chart": "st_callable",  
    "download_button": "st_callable",
    #"echo": This is handled in a special way
    "empty": "st_callable", 
    "error": "st_callable",
    "exception": "st_callable",
    "experimental_connection": "st_direct_callable",
    "experimental_get_query_params": "st_direct_callable",
    "experimental_rerun": "st_direct_callable",
    "experimental_set_query_params": "st_direct_callable",
    "experimental_singleton": "st_direct_callable",
    "expander": "st_callable",
    "file_uploader": "st_callable",
    "form": "st_callable",
    "form_submit_button":"st_callable",
    "generate_id": "st_callable",
    "get_option": "st_callable",
    "graphviz_chart": "st_callable",
    "header": "st_callable",
    "help": "st_callable",
    "html":"st_callable",
    "iframe":"st_callable",
    "image": "st_callable",
    "info": "st_callable",
    "json": "st_callable",
    "latex": "st_callable",
    "legacy_caching_clear_cache": "st_callable",
    "line_chart": "st_callable",
    "map": "st_callable",
    "markdown": "st_callable",
    "metric": "st_callable",
    "multiselect": "st_callable",
    "number_input": "st_callable",
    "plotly_chart": "st_callable",
    "plotly_streamlit": "st_callable",
    "progress": "st_direct_callable",
    "pydeck_chart": "st_callable",
    "pyplot": "st_callable",
    "radio": "st_callable",
    "report_thread_get_report_ctx": "st_direct_callable",
    "secrets": "st_direct_property",
    "select_slider": "st_callable",
    "selectbox": "st_callable", 
    "set_option": "st_direct_callable",
    "set_page_config": "st_direct_callable",
    "session_state": "st_direct_property",
    "sidebar":"st_property",
    "slider": "st_callable",
    "snow": "st_snow",
    "spinner": "st_direct_callable",
    "status": "st_callable",
    "stop": "st_direct_callable",
    "subheader": "st_callable",
    "success": "st_callable",
    "table": "st_callable",
    "tabs": "st_unpackable_callable",
    "text": "st_callable",
    "text_area": "st_callable",
    "text_input": "st_callable", 
    "time_input": "st_callable",
    "title": "st_callable",
    "toast":"st_callable",
    "util_autoreload": "st_direct_callable",
    "util_docstrings_with_args": "st_direct_callable",
    "vega_lite_chart": "st_callable",
    "video": "st_callable",
    "warning": "st_callable",
    "write": "st_callable"
}

COMPONENTS_MAPPING={key:ComponentsDict[key]["type"] for key in ComponentsDict}

ATTRIBUTES_MAPPING.update(COMPONENTS_MAPPING)





