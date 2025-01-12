import bpy
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

### Search in open history

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

## Load once on WM, then refresh enum from the property group
class PATHACTION_PG_blender_versions(bpy.types.PropertyGroup):
    path : bpy.props.StringProperty()
    version_name : bpy.props.StringProperty()
    # add config path here ?

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

    blender_versions : bpy.props.EnumProperty(
        name="Blender Version",
        description="Blender version to get history from (default to current version)",
        items=get_user_path_all_versions,
        update=fetch_history,
        options={'HIDDEN'},
        )

    show_full_path : bpy.props.BoolProperty(name='Show Full Path', default=False)

    def invoke(self, context, event):
        ## Triggering the enum update
        self.blender_versions = self.blender_versions

        ## TODO: Test if possible to refresh enum from a collection property set in invoke
        # wm = context.window_manager
        # wm.pa_blender_versions.clear()
        # for version in get_user_path_all_versions(None, context):
        #     item = wm.pa_blender_versions.add()
        #     item.path = version[0]
        #     item.version_name = version[1]

        ## Need Trigger prop for update ?
        # return context.window_manager.invoke_props_dialog(self, width=600) # large width for full path display
        return context.window_manager.invoke_props_dialog(self, width=450)
        # return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout

        wm = context.window_manager
        list_collection = wm.pa_path_list

        layout.use_property_decorate = False
        layout.use_property_split = True
        # layout.prop(self, 'show_full_path')
        layout.prop(self, 'blender_versions')

        col = layout.column(align=True)
        if not len(list_collection):
            layout.label(text='Error, Nothing found', icon='ERROR')
            return
        
        for item in list_collection:
            if item.is_error_message:
                layout.label(text=item.path, icon='ERROR')
                continue
            
            blend = Path(item.path)

            open_path = item.path
            if not item.is_valid:
                open_path = item.valid_parent_path

            row = col.row(align=True)


            ## FIXME: avoid breaking alignment with long paths
            valid_icon = 'FILE_BLEND' if item.is_valid else 'LIBRARY_DATA_BROKEN' # FILE_HIDDEN
            
            # icon_row = row.row(align=True)
            # icon_row.label(text='', icon=valid_icon)
            # icon_row.alignment = 'LEFT'

            ## Label
            left_row = row.row(align=True)
            left_row.alignment = 'LEFT'
            # left_row.label(text='', icon=valid_icon)
            left_row.enabled = item.is_valid
            # left_row.ui_units_x = 25.0

            display_text = item.path if self.show_full_path else blend.name            
            op = left_row.operator('wm.open_mainfile', text=display_text, emboss=False, icon=valid_icon)
            op.filepath = str(item.path)
            op.display_file_selector = False
            op.load_ui = context.preferences.filepaths.use_load_ui

            ## Action buttons
            action_row = row.row(align=True)
            action_row.alignment = 'RIGHT'

            action_row.operator('path.open_browser', text='', icon='FILE_FOLDER').filepath = open_path
            action_row.operator('pathaction.copy_path', text='', icon='COPYDOWN').path = item.path

            sub_action_row = action_row.row(align=False)
            sub_action_row.operator('wm.open_in_new_instance', text='', icon='FILE_BACKUP').filepath = item.path
            sub_action_row.enabled = item.is_valid

    def execute(self, context):
        return {'FINISHED'}

classes = (
PATHACTION_PG_blender_versions,
PATHACTION_PG_path_list,
PATHACTION_OT_blend_history,
PATH_OT_open_last_file,
PATH_OT_search_open_history,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.pa_blender_versions = bpy.props.CollectionProperty(type=PATHACTION_PG_blender_versions)
    bpy.types.WindowManager.pa_path_list = bpy.props.CollectionProperty(type=PATHACTION_PG_path_list)

def unregister():
    del bpy.types.WindowManager.pa_blender_versions
    del bpy.types.WindowManager.pa_path_list

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
