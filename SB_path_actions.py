# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Path Actions",
    "author": "Samuel Bernou",
    "version": (1, 0),
    "blender": (2, 73, 0),
    "location": "Properties > Render > Output ",
    "description": "open output path or blend file location in OS explorer",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "System"}

import bpy
from os import startfile, path

class OpenBlendFolder(bpy.types.Operator):
    """open blend's directory in OS explorer"""
    bl_idname = "path.open_blend"
    bl_label = "Open blend folder"
    bl_options = {'REGISTER'}

    def execute(self, context):
        fileloc = bpy.context.blend_data.filepath
        folder = path.dirname(fileloc)
        startfile(folder)
         
        self.report({'INFO'}, "Blend's folder opened")
        return {'FINISHED'}
   
   

class OpenOutputFolder(bpy.types.Operator):
    """open output directory in OS explorer"""
    bl_idname = "path.open_output"
    bl_label = "Open output folder"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        outfileloc = bpy.context.scene.render.filepath # get filepath from blender
        folder = path.dirname(outfileloc) # get last dir

        if folder.startswith("/"): #Convert root/relative path to absolute
            folder = path.realpath(bpy.path.abspath(folder))

        fhead, ftail = path.split(folder)
 
        
        if path.exists(folder):
            self.report({'INFO'}, "Open " + folder)
            startfile(folder)

        elif path.exists(fhead):
           self.report({'INFO'}, "Open " + fhead)
           startfile(fhead)

        else:
            self.report({'INFO'}, "Can't open " + folder)

        return {'FINISHED'}

       
class SwitchPathOperator(bpy.types.Operator):
    """toggle path absolute/relative"""
    bl_idname = "path.switch_operator"
    bl_label = "Switch output path mode"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        
        fpath = bpy.context.scene.render.filepath
        if fpath.startswith("/"):
            bpy.context.scene.render.filepath = path.realpath(bpy.path.abspath(fpath))
        else:
            bpy.context.scene.render.filepath = bpy.path.relpath(fpath)
        
        return {'FINISHED'}
    

################## Pannel Integration

def PathActionsPanel(self, context):
    """Path operations"""
    layout = self.layout
    split = layout.split(percentage=.2, align=True)
    
    split.label("Open: ")
    split.operator(OpenBlendFolder.bl_idname, text = "blender folder", icon = 'BLENDER')
    split.operator(OpenOutputFolder.bl_idname, text = "output folder", icon = 'FILE_FOLDER')
    layout.operator(SwitchPathOperator.bl_idname, text = "Toggle path mode", icon = 'PARTICLE_PATH')


################## Registration

def register():
    bpy.utils.register_class(SwitchPathOperator)
    bpy.utils.register_class(OpenOutputFolder)
    bpy.utils.register_class(OpenBlendFolder)
    bpy.types.RENDER_PT_output.append(PathActionsPanel)

def unregister():
    bpy.utils.unregister_class(SwitchPathOperator)
    bpy.utils.unregister_class(OpenOutputFolder)
    bpy.utils.unregister_class(OpenBlendFolder)
    bpy.types.RENDER_PT_output.remove(PathActionsPanel)
    
if __name__ == "__main__":
    register()