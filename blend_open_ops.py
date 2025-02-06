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


def load_workspaces(src):
    '''Load all workspace from a file and return list'''
    with bpy.data.libraries.load(str(src), link=False) as (data_from, data_to):
        setattr(data_to, 'workspaces', [item for item in getattr(data_from, 'workspaces')])
    return data_to.workspaces

def replace_workspaces(source_blend):
    ### replace
    ## rename wk to temp
    
    active_workspace_name = bpy.context.workspace.name
    tmp = 'tmpold_'
    
    current_wks = [w for w in bpy.data.workspaces]
    for wk in current_wks:
        print(wk.name)
        wk.name = f'{tmp}_{wk.name}'

    new_wks = load_workspaces(source_blend)

    ## import user workspaces
    if not len(new_wks):
        print('could not load new workspaces, Abort')
        ## remove tmp prefix from name and abort
        for wk in reversed(current_wks):
            if wk.name.startswith(tmp):
                wk.name = wk.name[len(tmp):]
        return

    ## Remove old temp workspaces by name
    for wk in reversed(current_wks):
        if wk.name.startswith(tmp):
            with bpy.context.temp_override(workspace=wk):
                bpy.ops.workspace.delete()
    
    same_wk = next((w for w in new_wks if w.name == active_workspace_name), None)
    
    if same_wk:
        # print('Restore new workspace tab with same previous name')
        bpy.context.window.workspace = same_wk
    # else:
    #     bpy.context.window.workspace = new_wks[0] # <- not the first in tab list

def load_startup_workspace():
    ## find startup source
    user_startup = Path(bpy.utils.resource_path('USER'), 'config', 'startup.blend')

    if user_startup.exists():
        # user startup
        source_blend = str(user_startup)
        print('using startup:', source_blend)
        replace_workspaces(source_blend)
        return source_blend

    print('!! No custom user startup!!')        

class PATH_OT_full_reopen(Operator) :
    bl_idname = "wm.full_reopen"
    bl_label = 'Full Reopen Blend'
    bl_description = "Close and re-open blender file\
        \nCtrl: Force reopen even if file is not saved"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return True
        return bpy.data.is_saved #only if file is saved?

    def invoke(self, context, event):
        ## Alt action : Replace workspaces by appending startup and removing current
        ## TODO: Can crash, need testing before implementation.
        # if event.alt:
        #     ret = load_startup_workspace()
        #     if not ret:
        #         self.report({'ERROR'}, 'Need to save a startup file first (File > Defaults > Save Startup File)')
        #         return {'CANCELLED'}
        #     self.report({'INFO'}, f'Loaded startup file workspaces from: {ret}')
        #     return {'FINISHED'}

        ## "full reopen" action (skip prompt with ctrl)
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
        
        ## Adapt panel size to longest name... (Not predictable, font is not monospace)
        self.longest_path = max([len(i.name) for i in self.blend_list])
        estimated = int(self.longest_path * 8.8)
        popup_width = max(250, estimated) # low clamp
        popup_width = min(popup_width, 520) # high clamp

        # print('longest_path:', self.longest_path)# Dbg
        # print('estimated width: ', estimated)# Dbg

        ## using a 'props_popup' crashes blender (using dialog add an OK button...but works)
        # return wm.invoke_props_popup(self, event) # need "undo" in bl_options else get an error
        wm = context.window_manager
        return context.window_manager.invoke_props_dialog(self, width=popup_width)

    def draw(self, context):
        layout = self.layout
        main_row = layout.row(align=True)
        blend_col = main_row.column(align=True)
        blend_col.alignment = 'LEFT'

        # main_row.separator_spacer()
        # main_row.separator()
        option_col = main_row.column(align=True)
        option_col.alignment = 'RIGHT'
        # option_col.ui_units_x = 2.2

        for path in self.blend_list:
            blend_row = blend_col.row()
            blend_row.alignment = 'LEFT'
            
            if path == Path(bpy.data.filepath):
                ## Current file, Displayed but disabled (non-clickable)
                blend_row.enabled=False
                blend_row.operator('wm.open_mainfile', text=path.name, emboss=False).filepath = str(path) # path.as_posix()
            
            else:
                # blend_row.operator_context = "EXEC_AREA"# , (should be "INVOKE_AREA" if file was not saved) # no need in blender 4.2+
                op = blend_row.operator('wm.open_mainfile', text=path.name, emboss=False)
                op.filepath = str(path)
                op.display_file_selector = False # adding this arg (True or False) display the warning correctly when file is not saved
                op.load_ui = context.preferences.filepaths.use_load_ui
            
            # option_row = option_col.box()
            option_row = option_col.row(align=True)
            option_row.alignment = 'RIGHT'
            option_row.operator('wm.open_in_new_instance', text='', icon='FILE_BACKUP').filepath = str(path)
            option_row.operator('pathaction.copy_path', text='', icon='COPYDOWN').path = str(path)

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