import bpy
import os

### Topbar
# add a button on top bar : TOPBAR_HT_upper_bar (there is a def draw_left and a def draw_right )
#else add in the top lower bar : TOPBAR_HT_lower_bar

def get_addon_prefs():
    addon_name = os.path.splitext(__name__)[0]
    preferences = bpy.context.preferences
    addon_prefs = preferences.addons[addon_name].preferences
    return addon_prefs

def TopBarOpenButton(self, context):
    layout = self.layout
    region = context.region
    if region.alignment == 'RIGHT':
        if get_addon_prefs().dev_mode:
            layout.operator("wm.full_reopen", text = "", icon = 'FILE_REFRESH')
        layout.operator("path.open_blend", text = "", icon = 'FILE_FOLDER')

### File browser

def BrowserPathActionsButtons(self, context):
    layout = self.layout
    #split = layout.split()
    row = layout.row(align=True)
    if bpy.data.filepath:
        #button to paste blend path in blender filebrowser's path (file must be saved for the button to appear)
        row.operator(
            "path.paste_path",
            text="Blend Location",
            icon="FILE_BACKUP")#BLENDER#APPEND_BLEND (paperclip in 2.8)
    #button to open current filepath destination in OS browser
    row.operator(
        "path.open_filepath",
        text="Open Folder",
        icon="FILE_FOLDER")


## From space_filebrowser.py
# def panel_poll_is_upper_region(region):
#     # The upper region is left-aligned, the lower is split into it then.
#     # Note that after "Flip Regions" it's right-aligned.
#     return region.alignment in {'LEFT', 'RIGHT'}

## Panel taken from Amaranth
class PATH_PT_top_filebrowser_ui(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOLS'
    bl_category = "Bookmarks"
    bl_label = "Filebrowser"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return context.region.alignment in {'LEFT', 'RIGHT'}

    def draw(self, context):
        layout = self.layout
        layout.scale_x = 1.3
        layout.scale_y = 1.3

        row = layout.row(align=True)
        if bpy.data.filepath:
            row.operator(
                'path.paste_path', text='Blend Location',
                icon="FILE_BACKUP") # DESKTOP
        
        row.operator(
            "path.open_filepath", text="Open Folder",
            icon="FILE_FOLDER")
        
        ''' #using grid
        row = layout.row()
        flow = row.grid_flow(row_major=False, columns=0, even_columns=False, even_rows=False, align=True)
        subrow = flow.row()
        subsubrow = subrow.row(align=True)
        if bpy.data.filepath:
            subsubrow.operator(
                'path.paste_path', text='Blend Location',
                icon="FILE_BACKUP") # DESKTOP
        
        subsubrow.operator(
        "path.open_filepath",
        text="Open Folder",
        icon="FILE_FOLDER")
        '''


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
    # bpy.types.FILEBROWSER_HT_header.append(BrowserPathActionsButtons)
    bpy.types.TOPBAR_HT_upper_bar.append(TopBarOpenButton)
    bpy.utils.register_class(PATH_PT_top_filebrowser_ui)
    
    # bpy.types.RENDER_PT_output.append(PathActionsPanel)

def unregister():
    bpy.utils.unregister_class(PATH_PT_top_filebrowser_ui)
    # bpy.types.FILEBROWSER_HT_header.remove(BrowserPathActionsButtons)
    bpy.types.TOPBAR_HT_upper_bar.remove(TopBarOpenButton)
    
    # bpy.types.RENDER_PT_output.remove(PathActionsPanel)