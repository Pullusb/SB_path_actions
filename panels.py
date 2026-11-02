import bpy

### Topbar
# add a button on top bar : TOPBAR_HT_upper_bar (there is a def draw_left and a def draw_right )
#else add in the top lower bar : TOPBAR_HT_lower_bar

def get_addon_prefs():
    return bpy.context.preferences.addons[__package__].preferences

def TopBarOpenButton(self, context):
    layout = self.layout
    region = context.region
    if region.alignment == 'RIGHT':
        if get_addon_prefs().dev_mode:
            layout.operator("wm.full_reopen", text = "", icon = 'FILE_REFRESH')
        layout.operator("wm.open_blend_folder", text = "", icon = 'FILE_FOLDER')

### File browser

def BrowserPathActionsButtons(self, context):
    layout = self.layout
    row = layout.row(align=True)
    # button to open current filepath destination in OS browser
    row.operator(
        "path.open_filepath",
        text="Open Folder",
        icon="FILE_FOLDER")

    if bpy.data.filepath:
        # button to paste blend path in blender filebrowser's path (file must be saved for the button to appear)
        row.operator(
            "path.browser_to_blend_folder",
            text="Blend Location",
            icon="FILE_BACKUP")

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
        from bpy_extras.asset_utils import SpaceAssetInfo
        if SpaceAssetInfo.is_asset_browser_poll(context):
            return
        return context.region.alignment in {'LEFT', 'RIGHT'}

    def draw(self, context):
        # if context.area.regions[2].type != 'UI':
        #     return
        layout = self.layout
        layout.scale_x = 1.3
        layout.scale_y = 1.3

        row = layout.row(align=True)
        if bpy.data.filepath:
            row.operator(
                'path.browser_to_blend_folder', text='Blend Location',
                icon="FILE_BACKUP") # DESKTOP
        
        row.operator(
            "path.open_filepath", text="Open Folder",
            icon="FILE_FOLDER")


def register():
    # bpy.types.FILEBROWSER_HT_header.append(BrowserPathActionsButtons)
    bpy.types.TOPBAR_HT_upper_bar.append(TopBarOpenButton)
    bpy.utils.register_class(PATH_PT_top_filebrowser_ui)

def unregister():
    bpy.utils.unregister_class(PATH_PT_top_filebrowser_ui)
    # bpy.types.FILEBROWSER_HT_header.remove(BrowserPathActionsButtons)
    bpy.types.TOPBAR_HT_upper_bar.remove(TopBarOpenButton)
