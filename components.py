#Allows for easier implementation of third party components in the streamlit_deferrer module

"""
Structure of ComponentsDict : 
    {
        component_key : {"module":module_name,"component":component_name,"type":st_object_subtype},
        ...
    }
"""

ComponentsDict={
    "ace":{"module":"streamlit_ace","component":"st_ace","type":"st_callable"}
    #add your components here
}

#This function will import the components from their modules and return a COMPONENTS dictionary allowing to access the corresponding objects from their keys
def ImportComponents():
    COMPONENTS={}
    for key in ComponentsDict:
        module = __import__(ComponentsDict[key]["module"], globals(), locals(), [ComponentsDict[key]["component"]], 0)
        COMPONENTS[key] = getattr(module, ComponentsDict[key]["component"])
    return COMPONENTS

COMPONENTS=ImportComponents()

#This dictionary maps the built-in streamlit attributes to the adequate st_object subtype used by the deferrer
ATTRIBUTES_MAPPING = {
    "add_rows": "st_callable",
    "altair_chart": "st_callable",  
    "area_chart": "st_callable",
    "audio": "st_callable",
    "balloons": "st_one_shot_callable", 
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
    "column_config":"st_direct_exec_property",
    "columns": "st_unpackable_callable",
    "container": "st_callable",
    "cursor_hide_cursor": "st_callable",
    "cursor_show_cursor": "st_callable",
    "date_input": "st_callable",
    "dataframe": "st_callable",
    "data_editor":"st_callable",
    "deck_gl_chart": "st_callable",
    "deck_gl_json_chart": "st_callable",  
    "download_button": "st_one_shot_callable",
    "echo": "st_one_shot_callable",
    "empty": "st_callable", 
    "error": "st_callable",
    "exception": "st_callable",
    "experimental_connection": "st_callable",
    "experimental_get_query_params": "st_callable",
    "experimental_rerun": "st_one_shot_callable",
    "experimental_set_query_params": "st_callable",
    "experimental_singleton": "st_callable",
    "expander": "st_callable",
    "file_uploader": "st_callable",
    "form": "st_callable",
    "generate_id": "st_callable",
    "get_option": "st_callable",
    "graphviz_chart": "st_callable",
    "header": "st_callable",
    "help": "st_callable", 
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
    "progress": "st_direct_exec_callable",
    "pydeck_chart": "st_callable",
    "pyplot": "st_callable",
    "radio": "st_callable",
    "report_thread_get_report_ctx": "st_callable",
    "secrets": "st_property",
    "select_slider": "st_callable",
    "selectbox": "st_callable", 
    "set_option": "st_callable",
    "set_page_config": "st_callable",
    "session_state": "st_property",
    "slider": "st_callable",
    "snow": "st_one_shot_callable",
    "spinner": "st_direct_exec_callable",
    "status": "st_callable",
    "stop": "st_one_shot_callable",
    "subheader": "st_callable",
    "success": "st_callable",
    "table": "st_callable",
    "tabs": "st_unpackable_callable",
    "text": "st_callable",
    "text_area": "st_callable",
    "text_input": "st_callable", 
    "time_input": "st_callable",
    "title": "st_callable",
    "util_autoreload": "st_callable",
    "util_docstrings_with_args": "st_callable",
    "vega_lite_chart": "st_callable",
    "video": "st_callable",
    "warning": "st_callable",
    "write": "st_callable"
}

COMPONENTS_MAPPING={key:ComponentsDict[key]["type"] for key in ComponentsDict}

ATTRIBUTES_MAPPING.update(COMPONENTS_MAPPING)





