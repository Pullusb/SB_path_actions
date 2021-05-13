import bpy
import os
from os.path import basename, dirname, join, exists
from bpy.types import Operator


### Open Last file

def open_last_recent_file():
    '''opent the last file (last)'''

    history = join(bpy.utils.user_resource('CONFIG'), 'recent-files.txt')
    if exists(history):
        try:
            with open(history, 'r') as f:
                last_file = f.readline().strip()#read first line of history txt file
            if last_file:
                #print ('last_file:', last_file)#D
                bpy.ops.wm.open_mainfile(filepath=last_file, load_ui=True, use_scripts=True)
            else:
                return (1, 'error with recent-file.txt, may be empty : ' + history)
        except:
            return (1, 'error accessing recent-file.txt : ' + history)

    else:
        return (1, 'error, "recent-file.txt" not found')
    return (0, '')#os.path.basename(last_file) + ' opened'


class PATH_OT_open_last_file(Operator):
    bl_idname = "path.open_last_file"
    bl_label = "Open Last File"
    bl_description = "Open the last blend file"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        ## Verification step (may integrate later)
        #if bpy.data.is_saved:#if file has been saved
        #    if not bpy.data.is_dirty:#if file as not unsaved modification
        #        error, mess = open_last_recent_file()
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
    try:
        with open(self.history, 'r') as fd:
            blends = [line.strip() for line in fd]
    except:
        return [("", "", "")]
    return [(i, basename(i), "") for i in blends]
    # return [(i.path, basename(i.path), "") for i in self.blends]


class PATH_OT_search_open_history(Operator) :
    bl_idname = "path.open_from_history"
    bl_label = 'Open Blend From History'
    # important to have the updated enum here as bl_property
    bl_property = "blend_files_enum"


    blend_files_enum : bpy.props.EnumProperty(
        name="Blends",
        description="Take the blend",
        items=get_history_list
        )
    
    # There is a known bug with using a callback,
    # Python must keep a reference to the strings returned by the callback
    # or Blender will misbehave or even crash.

    history : bpy.props.StringProperty(default='', options={'SKIP_SAVE'}) # need to have a variable to store (to get it in self)

    def execute(self, context):
        blend = self.blend_files_enum
        bpy.ops.wm.open_mainfile(filepath=blend) # load_ui=True, use_scripts=True
        return {'FINISHED'}

    def invoke(self, context, event):
        self.history = join(bpy.utils.user_resource('CONFIG'), 'recent-files.txt')
        if not exists(self.history):
            self.report({'WARNING'}, 'No history file found')
            return {'CANCELLED'}

        blends = []
        try:
            with open(self.history, 'r') as fd:
                blends = [fd.readline().strip() for line in fd]
        except:
            self.report({'ERROR'}, f'error accessing recent-file.txt : {self.history}')
            return {'CANCELLED'}

        if not blends:
            self.report({'WARNING'}, f'Empty history !')
            return {'CANCELLED'}

        wm = context.window_manager
        wm.invoke_search_popup(self) # can't specify size... width=500, height=600
        return {'FINISHED'}

classes = (
PATH_OT_open_last_file,
PATH_OT_search_open_history
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)