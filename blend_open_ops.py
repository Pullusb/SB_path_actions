import bpy
import os
import re
from os.path import basename, dirname, join, exists
from pathlib import Path
import subprocess
import time
from bpy.types import Operator
from . import path_func


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
    # return [(i, basename(i), "") for i in blends]
    try:
        with open(self.history, 'r') as fd:
            blends = [line.strip() for line in fd]
    except:
        return [("", "", "")]
    return [(i, basename(i), "") for i in blends]

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
            if path == Path(bpy.data.filepath):
                mainrow=col.row()
                subrow = mainrow.row()
                subrow.alignment = 'LEFT'
                subrow.enabled=False
                subrow.operator('wm.open_mainfile', text=path.name, emboss=False).filepath = str(path) # path.as_posix()
            else:
                mainrow=col.row()
                subrow = mainrow.row()
                subrow.alignment = 'LEFT'
                subrow.operator_context = "EXEC_AREA"# , (should be "INVOKE_AREA" if file was not saved)
                op = subrow.operator('wm.open_mainfile', text=path.name, emboss=False)
                op.load_ui = context.preferences.filepaths.use_load_ui
                op.filepath = str(path)
                # subrow.operator('wm.open_mainfile', text=path.name, emboss=False).filepath = str(path)
            
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

""" # unused yet - same as copy_blend_path from operator.py but for generic paths
# TODO: ensure idname is usnique (already used in other addons)
class PATH_OT_copy_chosen_path(bpy.types.Operator):
    bl_idname = "path.copy_chosen_path"
    bl_label = "Copy Chosen Path"
    bl_description = "Copy chosen path in a list of proposed alternative"
    bl_options = {"REGISTER", "INTERNAL"}
    
    path : bpy.props.StringProperty(options={'SKIP_SAVE'})

    quote_style : bpy.props.EnumProperty(
        name="Quote Style",
        description="Choose the quote style",
        items=(
            ('PLAIN', "Plain", "No quotes", 0),
            ('DOUBLE', "Double Quote", 'Wrap with "', 1),
            ('SINGLE', "Single Quote", "Wrap with '", 2),
            ('BACK', "Back Quote", "Wrap with `", 3)
        ),
        default='PLAIN',
        # options={'SKIP_SAVE'}
    )

    def invoke(self, context, event):
        if not self.path:
            return {"CANCELLED"}
        self.pathes = []

        try:
            path_obj = Path(self.path)
            absolute = Path(os.path.abspath(bpy.path.abspath(self.path)))
            resolved = Path(bpy.path.abspath(self.path)).resolve()
        except:
            # case of invalid / non-accessable path
            bpy.context.window_manager.clipboard = self.path
            self.report({'INFO'}, f'Copied: {self.path}')
            return self.execute(context)

        self.pathes.append(('Path', self.path))
        self.pathes.append(('Parent', dirname(self.path)))

        ## Show absolute path if different
        if absolute != path_obj:        
            self.pathes.append(('Absolute', str(absolute)))
            self.pathes.append(('Absolute Parent', str(absolute.parent)))

        ## Show resolved path if different
        if absolute != resolved:
            self.pathes.append(('Resolved', str(resolved)))
            self.pathes.append(('Absolute Parent', str(resolved.parent)))

        self.pathes.append(('File Name', path_obj.name))
        self.pathes.append(('File Stem', path_obj.stem))

        maxlen = max(len(l[1]) for l in self.pathes)
        popup_width = 800 
        if maxlen < 50:
            popup_width = 500
        elif maxlen > 100:
            popup_width = 1000
        return context.window_manager.invoke_props_dialog(self, width=popup_width)
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        # with align True, path are probably too close visually
        col = layout.column(align=False)
        row = col.row()
        # row.use_property_split = False # <- only on row
        row.prop(self, 'quote_style', text='Quote Style', expand=True)

        col.separator()

        for action_name, filepath in self.pathes:

            if self.quote_style == 'DOUBLE':
                filepath = f'"{filepath}"'
            elif self.quote_style == 'SINGLE':
                filepath = f"'{filepath}'"
            elif self.quote_style == 'BACK':
                filepath = f"`{filepath}`"

            split=col.split(factor=0.2, align=True)
            split.operator('pathaction.copy_text_to_clipboard', text=action_name, icon='COPYDOWN').text = filepath
            split.label(text=filepath)

    def execute(self, context):
        return {"FINISHED"}
"""

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