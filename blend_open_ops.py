from ast import operator
import bpy
import os
from os.path import basename, dirname, join, exists
from pathlib import Path
import sys
import subprocess
from bpy.types import Operator
from . import path_func


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

def open_blend_new_instance(filepath=None):
    filepath = filepath or bpy.data.filepath
    cmd = sys.argv
    if len(cmd) > 1 and cmd[1].endswith('.blend'):
        cmd[1] = str(filepath)
    else:
        cmd.insert(1, str(filepath))
    print('cmd: ', cmd)
    if sys.platform.lower().startswith('linux'):
        subprocess.Popen(['gnome-terminal', '--'] + cmd) # check if env is passed
    else:
        subprocess.Popen(cmd) #, shell=True
    ## potential flag for windows, need testing
    # subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)


class PATH_OT_open_in_new_instance(Operator) :
    bl_idname = "wm.open_in_new_instance"
    bl_label = 'Open Blend In New Instance'
    bl_description = "Open blend file in a new instance of blender"
    bl_options = {"REGISTER", "INTERNAL"}

    filepath : bpy.props.StringProperty(default='', options={'SKIP_SAVE'})

    def execute(self, context):
        open_blend_new_instance(self.filepath)
        return {'FINISHED'}

class PATH_OT_full_reopen(Operator) :
    bl_idname = "wm.full_reopen"
    bl_label = 'Full Reopen Blend'
    bl_description = "Close and re-open blender file\nCtrl: Force reopen even if file is not saved"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return bpy.data.is_saved

    def invoke(self, context, event):
        if bpy.data.is_dirty and not event.ctrl:
            wm = context.window_manager
            return wm.invoke_props_dialog(self)
        return self.execute(context)
    
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text='File is not saved! Reopen anyway ?')
        col.label(text='(use Ctrl to bypass this prompt even if not saved)')
        
    def execute(self, context):
        open_blend_new_instance()
        bpy.ops.wm.quit_blender()
        return {'FINISHED'}

class PATH_OT_open_side_blend(Operator) :
    bl_idname = "wm.open_side_blend"
    bl_label = 'Open Side Blend'
    bl_description = "Open blend in same folder as current"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bpy.data.is_saved

    def invoke(self, context, event):
        ## list surrounding blends
        self.blend_list = [Path(i.path) for i in os.scandir(Path(bpy.data.filepath).parent) if i.is_file() and i.name.endswith('.blend')]
        if len(self.blend_list) < 2:
            self.report({"WARNING"}, 'No other blend file in current blend location !')
            return {'CANCELLED'}

        self.blend_list.sort(key=lambda x: x.name) # needed ?
        
        wm = context.window_manager
        ## using a 'props_popup' crashes blender (using dialog add an OK button...but works)
        # return wm.invoke_props_popup(self, event) # need "undo" in bl_options else get an error

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        for path in self.blend_list:
            if path == Path(bpy.data.filepath):
                mainrow=col.row()
                subrow = mainrow.row()
                subrow.enabled=False
                subrow.operator('wm.open_mainfile', text=path.name, emboss=False).filepath = str(path) # path.as_posix()
                row = mainrow.row()
            else:
                row=col.row()
                row.operator_context = "EXEC_AREA"# , (should be "INVOKE_AREA" if file was not saved)
                op = row.operator('wm.open_mainfile', text=path.name, emboss=False)
                op.load_ui = context.preferences.filepaths.use_load_ui
                op.filepath = str(path)
                # row.operator('wm.open_mainfile', text=path.name, emboss=False).filepath = str(path)
            
            row.operator('wm.open_in_new_instance', text='', icon='FILE_BACKUP').filepath = str(path)

    def execute(self, context):
        return {'FINISHED'}

class PATH_OT_open_browser(Operator):
    bl_idname = "path.open_browser"
    bl_label = "Open Path In Browser"
    bl_description = "Open passed file/folder in OS browser. If a file, the file will be selected"
    bl_options = {"REGISTER", "INTERNAL"}

    filepath : bpy.props.StringProperty(options={'SKIP_SAVE'})

    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, 'No filepath')
            return {"CANCELLED"}
        if not exists(self.filepath):
            self.report({'ERROR'}, f'Not found : {self.filepath}')
            return {"CANCELLED"}

        path_func.openFolder(self.filepath)

        self.report({'INFO'}, f'Open: {self.filepath}')
        return {"FINISHED"}


classes = (
PATH_OT_open_last_file,
PATH_OT_search_open_history,
PATH_OT_open_in_new_instance,
PATH_OT_full_reopen,
PATH_OT_open_side_blend,
PATH_OT_open_browser,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)