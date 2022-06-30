import bpy
from bpy.types import Operator
from os.path import dirname, basename, realpath, split, exists


from .path_func import openFolder

class PATH_OT_browser_to_blend_folder(Operator):
    """current blend path to the browser filepath"""
    bl_idname = "path.paste_path"
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
    """Open blend's directory in OS explorer\nCtrl: Copy full data path\nCtrl+Shift: Copy path to directory\nAlt: Copy file name\nShift: Open a side blend"""
    bl_idname = "path.open_blend"
    bl_label = "Open blend folder"
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
        folder = dirname(fileloc)

        if self.ctrl and self.shift:
            bpy.context.window_manager.clipboard = folder
            self.report({'INFO'}, f'Copied: {folder}')
            return {'FINISHED'}
        elif self.ctrl:
            bpy.context.window_manager.clipboard = fileloc
            self.report({'INFO'}, f'Copied: {fileloc}')
            return {'FINISHED'}
        elif self.shift:
            bpy.ops.wm.open_side_blend('INVOKE_DEFAULT')
            self.report({'INFO'}, f'Open side blend')
            return {'FINISHED'}
        elif self.alt:
            bpy.context.window_manager.clipboard = basename(fileloc)
            self.report({'INFO'}, f'Copied: {basename(fileloc)}')
            return {'FINISHED'}

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

