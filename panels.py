import bpy

### Topbar
# add a button on top bar : TOPBAR_HT_upper_bar (there is a def draw_left and a def draw_right )
#else add in the top lower bar : TOPBAR_HT_lower_bar

def TopBarOpenButton(self, context):
    layout = self.layout
    region = context.region
    if region.alignment == 'RIGHT':
        layout.operator("path.open_blend", text = "", icon = 'FILE_FOLDER')#BLENDER

### File browser

def BrowserPathActionsButtons(self, context):
    layout = self.layout
    #split = layout.split()
    row = layout.row(align=True)
    if bpy.data.filepath:
        #button to paste blend path in blender filebrowser's path (file must be saved for the button to appear)
        row.operator(
            "path.paste_path",
            text="Blend location",
            icon="FILE_BACKUP")#BLENDER#APPEND_BLEND (paperclip in 2.8)
    #button to open current filepath destination in OS browser
    row.operator(
        "path.open_filepath",
        text="Open folder",
        icon="FILE_FOLDER")


### Output panel (DISABLED)
""" 
def PathActionsPanel(self, context):
    layout = self.layout
    layout.use_property_split = True 

    '''##Button aligned to right (as large as containing text)
    row = layout.row(align=False)
    row.alignment = 'RIGHT'
    row.operator("path.open_output", text = "Open Output folder", icon = 'FILE_FOLDER')
    row.operator("path.switch_output_path_mode", text = "Toggle path mode", icon = 'PARTICLE_PATH')
    '''

    ### Button aligned with properties
    col = layout.split()
    #Disable col.label to get a full large button
    col.label(text="Open")#Labeled like a propertie
    #col.label(text="")#Hack to align with properties 
    col.operator("path.open_output", text = "Output folder", icon = 'FILE_FOLDER')
    
    ###button for toggle path mode (a bit useless, access via search bar is better)
    # col = layout.split()
    # col.label(text="")
    # col.operator("path.switch_output_path_mode", text = "Toggle path mode", icon = 'PARTICLE_PATH')
 """

def register():
    bpy.types.FILEBROWSER_HT_header.append(BrowserPathActionsButtons) # FILEBROWSER_PT_directory_path 
    bpy.types.TOPBAR_HT_upper_bar.append(TopBarOpenButton)
    # bpy.types.RENDER_PT_output.append(PathActionsPanel)

def unregister():
    bpy.types.FILEBROWSER_HT_header.remove(BrowserPathActionsButtons) # FILEBROWSER_PT_directory_path
    bpy.types.TOPBAR_HT_upper_bar.remove(TopBarOpenButton)
    # bpy.types.RENDER_PT_output.remove(PathActionsPanel)