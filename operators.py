import bpy
from pathlib import Path
import os
from bpy.types import Operator
from os.path import dirname, basename, realpath, split, exists

from .path_func import openFolder

class PATH_OT_copy_string_to_clipboard(bpy.types.Operator):
    bl_idname = "gp.copy_string_to_clipboard"
    bl_label = "Copy String"
    bl_description = "Copy passed string to clipboard"
    bl_options = {"REGISTER", "INTERNAL"}
    
    string : bpy.props.StringProperty(options={'SKIP_SAVE'})
    
    def execute(self, context):
        if not self.string:
            return {"CANCELLED"}
        bpy.context.window_manager.clipboard = self.string
        self.report({'INFO'}, f'Copied: {self.string}')
        return {"FINISHED"}

class PATH_OT_copy_blend_path(bpy.types.Operator):
    bl_idname = "path.copy_blend_path"
    bl_label = "Copy Blend Path"
    bl_description = "Copy path to blend from a list of proposed alternative"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return bpy.data.is_saved

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
        self.path = bpy.data.filepath
        if not self.path:
            return {"CANCELLED"}
        self.pathes = []

        path_obj = Path(self.path)
        absolute = Path(os.path.abspath(bpy.path.abspath(self.path)))
        resolved = Path(bpy.path.abspath(self.path)).resolve()

        self.pathes.append(('Blend', self.path))
        self.pathes.append(('Folder', dirname(self.path)))

        ## Show absolute path if different
        if absolute != path_obj:        
            self.pathes.append(('Absolute', str(absolute)))
            self.pathes.append(('Absolute Parent', str(absolute.parent)))

        ## Show resolved path if different
        if absolute != resolved:
            self.pathes.append(('Resolved', str(resolved)))
            self.pathes.append(('Resolved Parent', str(resolved.parent)))

        self.pathes.append(('Name', path_obj.name))
        self.pathes.append(('Stem', path_obj.stem))

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
            split.operator('gp.copy_string_to_clipboard', text=action_name, icon='COPYDOWN').string = filepath
            split.label(text=filepath)

    def execute(self, context):
        return {"FINISHED"}

class PATH_OT_browser_to_blend_folder(Operator):
    """current blend path to the browser filepath"""
    bl_idname = "path.browser_to_blend_folder"
    bl_label = "Browser to blend folder"

    def execute(self, context):
        bpy.ops.file.select_bookmark(dir="//")
        return {"FINISHED"}

class PATH_OT_open_filepath_folder(Operator):
    """Open browser filepath directory in OS explorer"""
    bl_idname = "path.open_filepath"
    bl_label = "Open Current filepath"

    def execute(self, context):
        try: #handle error if context isn't filebrowser (if operator is launched from search)
            folder = context.space_data.params.directory #give the path, params.filename give the tail (file)
            openFolder(folder.decode())
        except:
            self.report({'WARNING'}, "Only works in fileBrowser context")
        return {"FINISHED"}

class PATH_OT_open_blend_folder(Operator):
    bl_idname = "wm.open_blend_folder"
    bl_label = "Open blend folder"
    bl_description = "Open blend's directory in OS explorer\
        \nCtrl: Pop-up 'copy path to blend' panel with choices\
        \nShift: Open a side blend"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return bpy.data.is_saved

    def invoke(self, context, event):
        self.ctrl = event.ctrl
        self.alt = event.alt
        self.shift = event.shift
        return self.execute(context)

    def execute(self, context):
        fileloc = bpy.data.filepath # bpy.context.blend_data.filepath
        # folder = dirname(fileloc)

        # if self.ctrl and self.shift:
        #     bpy.context.window_manager.clipboard = fileloc
        #     self.report({'INFO'}, f'Copied: {fileloc}')
        #     return {'FINISHED'}
        if self.ctrl:
            bpy.ops.path.copy_blend_path('INVOKE_DEFAULT')
            # bpy.context.window_manager.clipboard = fileloc
            # self.report({'INFO'}, f'Copied: {fileloc}')
            return {'FINISHED'}
        elif self.shift:
            bpy.ops.wm.open_side_blend('INVOKE_DEFAULT')
            self.report({'INFO'}, f'Open side blend')
            return {'FINISHED'}
        # elif self.alt:
        #     bpy.context.window_manager.clipboard = basename(fileloc)
        #     self.report({'INFO'}, f'Copied: {basename(fileloc)}')
        #     return {'FINISHED'}

        openFolder(fileloc)
         
        self.report({'INFO'}, "Blend's folder opened")
        return {'FINISHED'}


## Only accessible trough search
class PATH_OT_open_output_folder(Operator):
    """open output directory in OS explorer"""
    bl_idname = "path.open_output"
    bl_label = "Open output folder"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        outfileloc = bpy.context.scene.render.filepath # get filepath from blender
        folder = dirname(outfileloc) # get last dir

        if folder.startswith("/"): #Convert root/relative path to absolute
            folder = realpath(bpy.path.abspath(folder))

        fhead, _ftail = split(folder)
 
        
        if exists(folder):
            self.report({'INFO'}, "Open " + folder)
            openFolder(folder)

        elif exists(fhead):
           self.report({'INFO'}, "Open " + fhead)
           openFolder(fhead)

        else:
            self.report({'INFO'}, "Can't open " + folder)

        return {'FINISHED'}

       
## Only accessible trough search
class PATH_OT_switch_path_operator(Operator):
    """toggle path absolute/relative"""
    bl_idname = "path.switch_output_path_mode"
    bl_label = "Switch output path mode"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        compare = openFolder(False) # return "//" for windows, "/" for other OS
        
        fpath = bpy.context.scene.render.filepath
        if fpath.startswith(compare):
            bpy.context.scene.render.filepath = realpath(bpy.path.abspath(fpath))
        else:
            bpy.context.scene.render.filepath = bpy.path.relpath(fpath)
        
        return {'FINISHED'}


classes = (
    PATH_OT_copy_string_to_clipboard,
    PATH_OT_copy_blend_path,
    PATH_OT_switch_path_operator,
    PATH_OT_open_output_folder,
    PATH_OT_open_blend_folder,
    PATH_OT_browser_to_blend_folder,
    PATH_OT_open_filepath_folder,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

