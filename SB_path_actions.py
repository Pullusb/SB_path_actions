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
    "version": (1, 3, 3),
    "blender": (2, 80, 0),
    "location": "Properties > Render > Output and filebrowser",
    "description": "Open output path or blend file location in OS explorer",
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
import subprocess
from os import path, system

def openFolder(folderpath):
    """
    open the folder at the path given
    with cmd relative to user's OS
    """
    myOS = platform
    if myOS.startswith('linux') or myOS.startswith('freebsd'):
        # linux
        cmd = 'xdg-open'
        #print("operating system : Linux")
    elif myOS.startswith('win'):
        # Windows
        #cmd = 'start '
        cmd = 'explorer'
        #print("operating system : Windows")
        if not folderpath:
            return('/')
        
    else:#elif myOS == "darwin":
        # OS X
        #print("operating system : MACos")
        cmd = 'open'

    if not folderpath:
        return('//')

    """#old system method
    #double quote the path to avoid problem with special character
    folderpath = '"' + folderpath + '"'
    fullcmd = cmd + folderpath

    #print & launch open command
    print(fullcmd)
    system(fullcmd)
    """
    #if bad opening use : folderpath = os.path.normpath(folderpath)
    fullcmd = [cmd, folderpath]
    print(fullcmd)
    subprocess.Popen(fullcmd)
    return ' '.join(fullcmd)#back to string to print


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


### Topbar
# add a button on top bar : TOPBAR_HT_upper_bar (there is a def draw_left and a def draw_right )
#else add in the top lower bar : TOPBAR_HT_lower_bar

def TopBarOpenButton(self, context):
    layout = self.layout
    layout.operator(PATH_OT_OpenBlendFolder.bl_idname, text = "", icon = 'FILE_FOLDER')#BLENDER


### Output panel

def PathActionsPanel(self, context):
    layout = self.layout
    layout.use_property_split = True 

    '''##Button aligned to right (as large as containing text)
    row = layout.row(align=False)
    row.alignment = 'RIGHT'
    row.operator(PATH_OT_OpenOutputFolder.bl_idname, text = "Open Output folder", icon = 'FILE_FOLDER')
    row.operator(PATH_OT_SwitchPathOperator.bl_idname, text = "Toggle path mode", icon = 'PARTICLE_PATH')
    '''

    ### Button aligned with properties
    col = layout.split()
    #Disable col.label to get a full large button
    col.label(text="Open")#Labeled like a propertie
    #col.label(text="")#Hack to align with properties 
    col.operator(PATH_OT_OpenOutputFolder.bl_idname, text = "Output folder", icon = 'FILE_FOLDER')
    
    ###button for toggle path mode (a bit useless, access via search bar is better)
    # col = layout.split()
    # col.label(text="")
    # col.operator(PATH_OT_SwitchPathOperator.bl_idname, text = "Toggle path mode", icon = 'PARTICLE_PATH')

### File browser

def BrowserPathActionsButtons(self, context):
    layout = self.layout
    #split = layout.split()
    row = layout.row(align=True)
    if bpy.data.filepath:
        #button to paste blend path in blender filebrowser's path (file must be saved for the button to appear)
        row.operator(
            PATH_OT_BrowserToBlendFolder.bl_idname,
            text="Blend location",
            icon="FILE_BACKUP")#BLENDER#APPEND_BLEND (paperclip in 2.8)
    #button to open current filepath destination in OS browser
    row.operator(
        PATH_OT_OpenFilepathFolder.bl_idname,
        text="Open folder",
        icon="FILE_FOLDER")

################## Registration


classes = (
    PATH_OT_SwitchPathOperator,
    PATH_OT_OpenOutputFolder,
    PATH_OT_OpenBlendFolder,
    PATH_OT_BrowserToBlendFolder,
    PATH_OT_OpenFilepathFolder,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.FILEBROWSER_HT_header.append(BrowserPathActionsButtons)
    bpy.types.TOPBAR_HT_upper_bar.append(TopBarOpenButton)
    # bpy.types.RENDER_PT_output.append(PathActionsPanel)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    bpy.types.FILEBROWSER_HT_header.remove(BrowserPathActionsButtons)
    bpy.types.TOPBAR_HT_upper_bar.remove(TopBarOpenButton)
    # bpy.types.RENDER_PT_output.remove(PathActionsPanel)

    
if __name__ == "__main__":
    register()
