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
    "version": (1, 3, 2),
    "blender": (2, 79, 0),
    "location": "Properties > Render > Output and filebrowser",
    "description": "open output path or blend file location in OS explorer",
    "warning": "",
    "wiki_url": "https://github.com/Pullusb/SB_Path-Actions",
    "tracker_url": "https://github.com/Pullusb/SB_Path-Actions/issues/new",
    "category": "System"}

"""
Usage:

Add buttons in properties > render > Output pannel and filebrowser
quick-use: search "folder" in the spacebar menu
"""

import bpy
from sys import platform
from os import path, system

def openFolder(folderpath):
    """
    open the folder at the path given
    with cmd relative to user's OS
    """
    myOS = platform
    if myOS.startswith('linux') or myOS.startswith('freebsd'):
        # linux
        cmd = 'xdg-open '
        #print("operating system : Linux")
    elif myOS.startswith('win'):
        # Windows
        #cmd = 'start '
        cmd = 'explorer '
        #print("operating system : Windows")
        if not folderpath:
            return('/')
        
    else:#elif myOS == "darwin":
        # OS X
        #print("operating system : MACos")
        cmd = 'open '

    if not folderpath:
        return('//')

    #double quote the path to avoid problem with special character
    folderpath = '"' + folderpath + '"'
    fullcmd = cmd + folderpath

    #print & launch open command
    print(fullcmd)
    system(fullcmd)


class PATH_OT_BrowserToBlendFolder(bpy.types.Operator):
    """current blend path to the browser filepath"""
    bl_idname = "path.paste_path"
    bl_label = "Browser to blend folder"

    def execute(self, context):
        bpy.ops.file.select_bookmark(dir="//")
        return {"FINISHED"}

class PATH_OT_OpenFilepathFolder(bpy.types.Operator):
    """Open browser filepath directory in OS explorer"""
    bl_idname = "path.open_filepath"
    bl_label = "Open Current filepath"

    def execute(self, context):
        try: #handle error if context isn't filebrowser (if operator is launched from search)
            folder = context.space_data.params.directory #give the path, params.filename give the tail (file)
            openFolder(folder)
        except:
            self.report({'WARNING'}, "Only works in fileBrowser context")
        return {"FINISHED"}


class PATH_OT_OpenBlendFolder(bpy.types.Operator):
    """open blend's directory in OS explorer"""
    bl_idname = "path.open_blend"
    bl_label = "Open blend folder"
    bl_options = {'REGISTER'}

    def execute(self, context):
        fileloc = bpy.context.blend_data.filepath
        folder = path.dirname(fileloc)
        openFolder(folder)
         
        self.report({'INFO'}, "Blend's folder opened")
        return {'FINISHED'}
   

class PATH_OT_OpenOutputFolder(bpy.types.Operator):
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
            openFolder(folder)

        elif path.exists(fhead):
           self.report({'INFO'}, "Open " + fhead)
           openFolder(fhead)

        else:
            self.report({'INFO'}, "Can't open " + folder)

        return {'FINISHED'}

       
class PATH_OT_SwitchPathOperator(bpy.types.Operator):
    """toggle path absolute/relative"""
    bl_idname = "path.switch_operator"
    bl_label = "Switch output path mode"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        compare = openFolder(False) # return "//" for windows, "/" for other OS
        
        fpath = bpy.context.scene.render.filepath
        if fpath.startswith(compare):
            bpy.context.scene.render.filepath = path.realpath(bpy.path.abspath(fpath))
        else:
            bpy.context.scene.render.filepath = bpy.path.relpath(fpath)
        
        return {'FINISHED'}


################## Pannel Integration


def TopBarOpenButton(self, context):
    layout = self.layout
    if bpy.data.is_saved:
        layout.operator(PATH_OT_OpenBlendFolder.bl_idname, text = "", icon = 'FILE_FOLDER')#BLENDER

def PathActionsPanel(self, context):
    """Path operations"""
    layout = self.layout
    split = layout.split(percentage=.2, align=True)
    
    split.label("Open: ")
    split.operator(PATH_OT_OpenBlendFolder.bl_idname, text = "blender folder", icon = 'BLENDER')
    split.operator(PATH_OT_OpenOutputFolder.bl_idname, text = "output folder", icon = 'FILE_FOLDER')
    #layout.operator(PATH_OT_SwitchPathOperator.bl_idname, text = "Toggle path mode", icon = 'PARTICLE_PATH')


def BrowserPathActionsButtons(self, context):
    layout = self.layout
    #split = layout.split()
    row = layout.row(align=True)
    if bpy.data.filepath:
        #button to paste blend path in blender filebrowser's path (file must be saved for the button to appear)
        row.operator(
            PATH_OT_BrowserToBlendFolder.bl_idname,
            text="Blend location",
            icon="APPEND_BLEND")
    #button to open current filepath destination in OS browser
    row.operator(
        PATH_OT_OpenFilepathFolder.bl_idname,
        text="Open folder",
        icon="FILE_FOLDER")

################## Registration

def register():
    bpy.utils.register_class(PATH_OT_SwitchPathOperator)
    bpy.utils.register_class(PATH_OT_OpenOutputFolder)
    bpy.utils.register_class(PATH_OT_OpenBlendFolder)
    bpy.utils.register_class(PATH_OT_BrowserToBlendFolder)
    bpy.utils.register_class(PATH_OT_OpenFilepathFolder)
    bpy.types.FILEBROWSER_HT_header.append(BrowserPathActionsButtons)
    bpy.types.INFO_HT_header.append(TopBarOpenButton)
    bpy.types.RENDER_PT_output.append(PathActionsPanel)

def unregister():
    bpy.utils.unregister_class(PATH_OT_OpenOutputFolder)
    bpy.utils.unregister_class(PATH_OT_OpenBlendFolder)
    bpy.utils.unregister_class(PATH_OT_BrowserToBlendFolder)
    bpy.utils.unregister_class(PATH_OT_OpenFilepathFolder)
    bpy.utils.unregister_class(PATH_OT_SwitchPathOperator)
    bpy.types.RENDER_PT_output.remove(PathActionsPanel)
    bpy.types.INFO_HT_header.remove(TopBarOpenButton)
    bpy.types.FILEBROWSER_HT_header.remove(BrowserPathActionsButtons)
    
if __name__ == "__main__":
    register()