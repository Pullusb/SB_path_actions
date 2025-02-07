import bpy
import re
from pathlib import Path
from bpy.types import Operator
# from . import path_func

## Operations related to save history

### Open Last file
def open_last_recent_file():
    '''opent the last file (last)'''
    history = Path(bpy.utils.user_resource('CONFIG')) / 'recent-files.txt'
    if history.exists():
        try:
            # with open(history, 'r') as f:
            with history.open('r') as fd:
                last_file = fd.readline().strip() # read first line of history txt file
            if last_file:
                bpy.ops.wm.open_mainfile(filepath=last_file, load_ui=True, use_scripts=True)
            else:
                return (1, 'error with recent-file.txt, may be empty : ' + history)
        except:
            return (1, 'error accessing recent-file.txt : ' + history)

    else:
        return (1, 'error, "recent-file.txt" not found')
    return (0, '')

def fuzzy_match_ratio(s1, s2, case_sensitive=False):
    '''Tell how much two passed strings are similar 1.0 being exactly similar'''
    from difflib import SequenceMatcher
    if case_sensitive:
        similarity = SequenceMatcher(None, s1, s2)
    else:
        similarity = SequenceMatcher(None, s1.lower(), s2.lower())
    return similarity.ratio()

class PATH_OT_open_last_file(Operator):
    bl_idname = "path.open_last_file"
    bl_label = "Open Last File"
    bl_description = "Open the last blend file"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        error, mess = open_last_recent_file()
        if error:
            self.report({'ERROR'}, mess)
        else:
            if mess:
                self.report({'INFO'}, mess)
        return {"FINISHED"}

### Search in history (Search popup)

def get_history_list(self, context):
    '''return (identifier, name, description) of enum content'''
    # blends = []
    # with open(self.history, 'r') as fd:
    #     blends = [line.strip() for line in fd]
    # if not blends:
    #     return [("", "", "")]
    # return [(i, Path(i).name, "") for i in blends]
    try:
        with open(self.history, 'r') as fd:
            blends = [line.strip() for line in fd]
    except:
        return [("", "", "")]
    return [(i, Path(i).name, "") for i in blends]

class PATH_OT_search_open_history(Operator) :
    bl_idname = "path.open_from_history"
    bl_label = 'Open Blend From History'
    # important to have the updated enum here as bl_property
    bl_property = "blend_files_enum"
    
    # There is a known bug with using a callback,
    # Python must keep a reference to the strings returned by the callback
    # or Blender will misbehave or even crash.
    history : bpy.props.StringProperty(default='', options={'SKIP_SAVE'}) # need to have a variable to store (to get it in self)

    blend_files_enum : bpy.props.EnumProperty(
        name="Blends",
        description="Take the blend",
        items=get_history_list,
        options={'HIDDEN'},
        )

    def invoke(self, context, event):
        history = Path(bpy.utils.user_resource('CONFIG')) / 'recent-files.txt'
        if not history.exists():
            self.report({'WARNING'}, 'No history file found')
            return {'CANCELLED'}

        self.history = str(history)

        blends = []
        try:
            with history.open('r') as fd:
                blends = [fd.readline().strip() for line in fd]
        except:
            self.report({'ERROR'}, f'Error accessing recent-file.txt : {self.history}')
            return {'CANCELLED'}

        if not blends:
            self.report({'WARNING'}, f'Empty history !')
            return {'CANCELLED'}

        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}

    def execute(self, context):
        blend = self.blend_files_enum
        bpy.ops.wm.open_mainfile(filepath=blend)
        return {'FINISHED'}


## Operator to list file history in a popup
## Check history of other blend version
## Store list separately to be able to refresh popup content depending on context and sub_ops (attach propperty group to window manager)
## WIP 

def get_user_path_all_versions(self, context):
    '''Get enum of all user path of blender versions (current on top of the list)
    return list of tuple (path, folder_name, description)
    Note: Can directly be used to feed a dynamic enum property
    But continuously refreshed when mouse move hover enum property.
    '''
    # print('Triggered get_user_path_all_versions') # Dbg
    current_path = Path(bpy.utils.resource_path('USER'))
    
    ## List all except current
    # return [(str(p), p.name, '') for p in current_path.parent.iterdir() if p.name != current_path.name]

    ## List all, with custom name for current p
    # return [(str(p), p.name if p.name != current_path.name else f'{p.name} (current)' , '') for p in current_path.parent.iterdir()]

    ## Lust all, same as above but reverse sorterd and with current version moved on top
    paths = [(str(p), p.name, '') for p in current_path.parent.iterdir() if p.name != current_path.name]
    paths.reverse()
    paths.insert(0, (str(current_path), f'{current_path.name} (Current)', ''))
    return paths

class PATHACTION_PG_path_list(bpy.types.PropertyGroup):
    path : bpy.props.StringProperty()
    # name : bpy.props.StringProperty() # tail
    is_checked : bpy.props.BoolProperty(default=False) # Define if path validity has been checked
    is_valid : bpy.props.BoolProperty(default=False)
    is_error_message: bpy.props.BoolProperty(
        default=False,
        description='When path is an error message instead of a path')

    valid_parent_path : bpy.props.StringProperty() # valid parent path if any
    is_relative : bpy.props.BoolProperty(default=False)


def fetch_history(self, context):
    '''Fetch history from the selected blender version and fill path_list collection property'''

    ## Only triggered when enum is set
    wm = context.window_manager

    ## Clear list and fill with selected version history
    wm.pa_path_list.clear()

    if not self.blender_versions or not Path(self.blender_versions).exists():
        print('!! No blender version listed by operator')
        item = wm.pa_path_list.add()
        item.path = 'Error: No valid blender version paths'
        item.is_error_message = True
        return

    ## get history from the selected blender version
    blender_version = Path(self.blender_versions)
    history = blender_version / 'config' / 'recent-files.txt'
    if not history.exists():
        item = wm.pa_path_list.add()
        item.path = 'No history file found.'
        item.is_error_message = True
        item = wm.pa_path_list.add()
        item.path = f'Checked at: {history}'
        item.is_error_message = True
        return
    
    ## Build path list collection from history
    with open(history, 'r') as fd:
        blends = [line.strip() for line in fd if line.strip()]

    if not blends:
        item = wm.pa_path_list.add()
        item.path = 'Empty history file.'
        item.is_error_message = True
        return

    for blend_path in blends:
        if not blend_path:
            continue
        item = wm.pa_path_list.add()
        item.path = blend_path

        blend = Path(blend_path)

        item.is_valid = blend.exists()
        item.is_checked = True

        if not item.is_valid:
            ## if Blend path is invalid
            ## go up parents in path until a folder is valid
            for i in range(len(blend.parts) - 2): # minus 2 otherwhise can go out of range
                parent = blend.parents[i]
                if parent.exists():
                    item.valid_parent_path = str(parent)
                    break

    # wm.pa_path_list.clear()
    # for path in Path(self.blender_versions).iterdir():
    #     item = wm.pa_path_list.add()
    #     item.path = str(path)
    #     item.is_valid = True

    return

class PATHACTION_OT_blend_history(Operator):
    bl_idname = "pathaction.blend_history"
    bl_label = "Blend History"
    bl_description = "Show the history of opened blend files with mutliple actions"
    bl_options = {"REGISTER"}
    ## bl_prop works to go right into search-field editing, but that prevent hovering to display blend infos
    # bl_property = "search_field" 

    blender_versions : bpy.props.EnumProperty(
        name="Blender Version",
        description="Blender version to get history from (default to current version)",
        items=get_user_path_all_versions,
        update=fetch_history,
        options={'HIDDEN'},
        )

    search_field : bpy.props.StringProperty(
        name='Search Filter', default='',
        description='Filter by name, case insensitive',
        options={'TEXTEDIT_UPDATE'}
        )

    ## Not exposed, window cannot resize dynamically so full paths is always will always be shown truncated
    show_full_path : bpy.props.BoolProperty(name='Show Full Path', default=False)

    def invoke(self, context, event):
        ## Triggering the enum update to load current history
        self.blender_versions = self.blender_versions
        return context.window_manager.invoke_props_dialog(self, width=480)

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        list_collection = wm.pa_path_list # list to create a copy

        layout.use_property_decorate = False
        layout.use_property_split = True

        # layout.prop(self, 'show_full_path')
        layout.prop(self, 'blender_versions')
        layout.prop(self, 'search_field', text="", icon='VIEWZOOM')

        if not len(list_collection):
            layout.label(text='Error, Nothing found', icon='ERROR')
            return

        search_terms = self.search_field
        if search_terms:
            result = [item for item in list_collection if search_terms.lower() in Path(item.path).name.lower()]

            ## // Additional (and supernaive) fuzzy search to find "close" names
            detail = ''
            if not result:
                ## Try to fuzzy match against names in list
                result = [item for item in list_collection if fuzzy_match_ratio(search_terms, Path(item.path).name) > 0.6]
                detail = 'No exact matchs, showing close names'
            
            if not result:
                ## Try fuzzy match againts splitted parts of the names
                result = [item for item in list_collection
                          if any(
                              [fuzzy_match_ratio(search_terms, x) > 0.7 for x in re.split(r'-|_|\s', Path(item.path).name)]
                              )
                         ]
                detail = 'No exact matchs, showing elements containing close parts'

            if not result:
                layout.label(text='Nothing found', icon='ERROR')
                return
            
            if detail:
                layout.label(text=detail, icon='INFO')
            ## End of additional fuzzy search //
    
            list_collection = result

        main_row = layout.row(align=True)
        blend_col = main_row.column(align=True)
        blend_col.alignment = 'LEFT'

        # main_row.separator_spacer()
        # main_row.separator()
        action_col = main_row.column(align=True)
        action_col.alignment = 'RIGHT'

        col = layout.column(align=True)
        for item in list_collection:
            blend_row = blend_col.row(align=True)
            action_row = action_col.row(align=True)
            action_row.alignment = 'RIGHT'

            if item.is_error_message:
                blend_row.label(text=item.path, icon='ERROR')
                action_row.label(text='', icon='BLANK1')
                continue

            blend = Path(item.path)

            open_path = item.path
            if not item.is_valid:
                open_path = item.valid_parent_path

            valid_icon = 'FILE_BLEND' if item.is_valid else 'LIBRARY_DATA_BROKEN' # FILE_HIDDEN
            
            # icon_row = row.row(align=True)
            # icon_row.label(text='', icon=valid_icon)
            # icon_row.alignment = 'LEFT'

            ## Label
            blend_row.alignment = 'LEFT'
            # blend_row.label(text='', icon=valid_icon)
            blend_row.enabled = item.is_valid
            # blend_row.ui_units_x = 25.0

            display_text = item.path if self.show_full_path else blend.name            
            op = blend_row.operator('wm.open_mainfile', text=display_text, emboss=False, icon=valid_icon)
            op.filepath = str(item.path)
            op.display_file_selector = False
            op.load_ui = context.preferences.filepaths.use_load_ui

            ## Action buttons
            action_row.operator('path.open_browser', text='', icon='FILE_FOLDER').filepath = open_path
            action_row.operator('pathaction.copy_path', text='', icon='COPYDOWN').path = item.path

            sub_action_row = action_row.row(align=False)
            sub_action_row.operator('wm.open_in_new_instance', text='', icon='FILE_BACKUP').filepath = item.path
            sub_action_row.enabled = item.is_valid

    def execute(self, context):
        return {'FINISHED'}

## Not possible to add on topbar menu
# def extend_recent_file_menu(self, context):
#     '''Extend the recent file menu with the operators'''
#     layout = self.layout
#     layout.separator()
#     # layout.operator(PATH_OT_open_last_file.bl_idname, text='Open Last File', icon='FILE_BLEND')
#     # layout.operator("path.open_from_history", text='Search in history', icon='FILE_BLEND')
#     layout.operator("pathaction.blend_history", text='Advanced History', icon='FILE_BLEND')

classes = (
PATHACTION_PG_path_list,
PATHACTION_OT_blend_history,
PATH_OT_open_last_file,
PATH_OT_search_open_history,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.pa_path_list = bpy.props.CollectionProperty(type=PATHACTION_PG_path_list)

    ## Add to open recent "File > Open Recent" menu
    # bpy.types.TOPBAR_MT_file_open_recent.append(extend_recent_file_menu) # not found
    # bpy.types.TOPBAR_MT_file.append(extend_recent_file_menu) # Add to File menu ?

def unregister():
    # bpy.types.TOPBAR_MT_file.remove(extend_recent_file_menu)
    # bpy.types.TOPBAR_MT_file_open_recent.remove(extend_recent_file_menu)

    del bpy.types.WindowManager.pa_path_list

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
