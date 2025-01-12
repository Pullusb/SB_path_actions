import bpy
import os
import re
from os.path import basename, dirname, join, exists
from pathlib import Path
import subprocess
import time
from bpy.types import Operator
from . import path_func


class PATH_OT_open_in_new_instance(Operator) :
    bl_idname = "wm.open_in_new_instance"
    bl_label = 'Open Blend In New Instance'
    bl_description = "Open blend file in a new instance of blender"
    bl_options = {"REGISTER", "INTERNAL"}

    filepath : bpy.props.StringProperty(default='', options={'SKIP_SAVE'})

    def execute(self, context):
        path_func.open_blend_new_instance(self.filepath)
        return {'FINISHED'}

class PATH_OT_full_reopen(Operator) :
    bl_idname = "wm.full_reopen"
    bl_label = 'Full Reopen Blend'
    bl_description = "Close and re-open blender file\nCtrl: Force reopen even if file is not saved"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return True
        return bpy.data.is_saved #only if file is saved?

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
        path_func.open_blend_new_instance()
        # Delay to avoid quitting before subprocess is launched
        time.sleep(0.1) # lower value ?
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

        ## Best to list the file even if solo (that way can open another instance quickly)
        # if len(self.blend_list) < 2:
        #     self.report({"WARNING"}, 'No other blend file in current blend location !')
        #     return {'CANCELLED'}
        
        natural_sort = lambda x: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', x.name)]
        try:
            self.blend_list.sort(key=natural_sort)
        except Exception:
            self.blend_list.sort(key=lambda x: x.name)
        
        wm = context.window_manager
        ## using a 'props_popup' crashes blender (using dialog add an OK button...but works)
        # return wm.invoke_props_popup(self, event) # need "undo" in bl_options else get an error

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        for path in self.blend_list:
            
            mainrow=col.row()
            subrow = mainrow.row()
            subrow.alignment = 'LEFT'
            
            if path == Path(bpy.data.filepath):
                ## Current file, Displayed but disabled (non-clickable)
                subrow.enabled=False
                subrow.operator('wm.open_mainfile', text=path.name, emboss=False).filepath = str(path) # path.as_posix()
            
            else:
                # subrow.operator_context = "EXEC_AREA"# , (should be "INVOKE_AREA" if file was not saved) # no need in blender 4.2+
                op = subrow.operator('wm.open_mainfile', text=path.name, emboss=False)
                op.filepath = str(path)
                op.display_file_selector = False # adding this arg (True or False) display the warning correctly when file is not saved
                op.load_ui = context.preferences.filepaths.use_load_ui
            
            row = mainrow.row()
            row.alignment = 'RIGHT'
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