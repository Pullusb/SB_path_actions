import bpy
import rna_keymap_ui
from pathlib import Path
from . import open_addons_path
# import addon_utils

# def get_hotkey_entry_item(km, kmi_name):
def get_hotkey_entry_item(km, kmi_name, kmi_value, properties):
    for i, km_item in enumerate(km.keymap_items):
        if km.keymap_items.keys()[i] == kmi_name:
            return km_item
        # elif properties == 'none':
        #     return km_item
    return None

def blender_locations(layout):
    ### Addons
    # col.use_property_split = True
    col = layout.column(align=False)

    ## Config folder
    col.label(text='Application:')
    row = layout.row()

    config_folder = bpy.utils.user_resource('CONFIG')
    row = col.row(align=True)
    row.operator("wm.path_open", text='Config Folder', icon='FILE_FOLDER').filepath = config_folder
    row.operator("pathaction.copy_string_to_clipboard", text="", icon='COPYDOWN').string = config_folder

    bin_path = Path(bpy.app.binary_path)
    app_folder = str(bin_path.parent)
    row = col.row(align=True)
    row.operator("wm.path_open", text='Application Folder', icon='FILE_FOLDER').filepath = app_folder
    row.operator("pathaction.copy_string_to_clipboard", text="", icon='COPYDOWN').string = app_folder

    row = col.row(align=True)
    row.operator("pathaction.copy_string_to_clipboard", text="Copy Blender Exec Path", icon='COPYDOWN').string = str(bin_path)

    col.separator()

    col.label(text='Scripts / Addons:')
    # Extensions
    if bpy.app.version >= (4, 2, 0):
        extension_dir = str(Path(bpy.utils.user_resource('EXTENSIONS')))
        row = col.row(align=True)
        row.operator("wm.path_open", text='Extensions', icon='FILE_FOLDER').filepath = extension_dir
        row.operator("pathaction.copy_string_to_clipboard", text="", icon='COPYDOWN').string = extension_dir


    user_scripts = str(Path(bpy.utils.user_resource('SCRIPTS')))
    row = col.row(align=True)
    # Local user addon source (usually appdata/.config folders). Where it goes when 'install from file'
    row.operator("wm.path_open", text='User Scripts', icon='FILE_FOLDER').filepath = user_scripts
    row.operator("pathaction.copy_string_to_clipboard", text="", icon='COPYDOWN').string = user_scripts
    
    # local default installed addons (release)

    native_scripts = str(Path(bpy.utils.resource_path('LOCAL')) / 'scripts')
    row = col.row(align=True)
    row.operator("wm.path_open", text='Native Scripts', icon='FILE_FOLDER').filepath = native_scripts
    row.operator("pathaction.copy_string_to_clipboard", text="", icon='COPYDOWN').string = native_scripts

    # external scripts (if specified)
    preferences = bpy.context.preferences
    if bpy.app.version < (3, 6, 0):
        external_scripts = preferences.filepaths.script_directory
        if external_scripts and len(external_scripts) > 2:
            extern_script = str(Path(external_scripts))
            row = col.row(align=True)
            row.operator("wm.path_open", text='External Addons').filepath = extern_script
            row.operator("pathaction.copy_string_to_clipboard", text="", icon='COPYDOWN').string = extern_script
    else:
        if len(preferences.filepaths.script_directories):
            col.label(text='Other Script Directories:')
            for s in preferences.filepaths.script_directories:
                if s.directory:
                    row = col.row(align=True)
                    row.operator("wm.path_open", text=s.name, icon='FILE_FOLDER').filepath = str(Path(s.directory))
                    row.operator("pathaction.copy_string_to_clipboard", text="", icon='COPYDOWN').string = str(Path(s.directory))


""" # old multi row UI (might be better for preferences)
def blender_locations(layout):
    row = layout.row()
    
    ### Addons
    row.label(text='Addons:')
    row = layout.row()
    row.label(text='Open: ', icon='FILE_FOLDER')
    # Local user addon source (usually appdata/.config folders). Where it goes when 'install from file'
    row.operator("wm.path_open", text='User Addons').filepath = str(Path(bpy.utils.user_resource('SCRIPTS')) / 'addons')
    # local default installed addons (release)
    row.operator("wm.path_open", text='Native Addons').filepath = str(Path(bpy.utils.resource_path('LOCAL')) / 'scripts' / 'addons')

    # external scripts (if specified)
    preferences = bpy.context.preferences
    if bpy.app.version < (3, 6, 0):
        external_scripts = preferences.filepaths.script_directory
        if external_scripts and len(external_scripts) > 2:
            row.operator("wm.path_open", text='External Addons').filepath = str(Path(external_scripts))
    else:
        if len(preferences.filepaths.script_directories):
            row = layout.row()
            row.label(text='Script directories:', icon='FILE_FOLDER')
            for s in preferences.filepaths.script_directories:
                if s.directory:
                    row.operator("wm.path_open", text=s.name).filepath = str(Path(s.directory))

    ## Config folder
    layout.separator()
    row = layout.row()
    row.label(text='Application:')
    row = layout.row()
    row.label(text='Open: ', icon='FILE_FOLDER')
    row.operator("wm.path_open", text='Config Folder').filepath = bpy.utils.user_resource('CONFIG')
    row.operator("wm.path_open", text='Application Folder').filepath = str(Path(bpy.app.binary_path).parent)
"""

class PATH_addon_preferences(bpy.types.AddonPreferences):
    """ Preference Settings Addon Panel"""
    bl_idname = __package__
    bl_label = "Addon Preferences"

    dev_mode : bpy.props.BoolProperty(name='Developer mode',
        description='Add a button on upper-right corner to fully reopen blender with current file (not just revert)',
        default=False)

    show_addon_open_buttons : bpy.props.BoolProperty(name='Addons Directory Shortcuts', default=False)

    filter : bpy.props.EnumProperty(
        name="Filter", description="Filter addon list to open their directory",
        default='ALL', options={'HIDDEN'},
        items=(
            ('ALL', 'All', 'List all addons', 0),
            ('ACTIVE', 'Enabled', 'List only enabled addons', 1),   
            ('INACTIVE', 'Disabled', 'List only Disabled addons', 2),   
            ))

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'dev_mode')

        box = layout.box()
        col = box.column()

        col.label(text = "Hotkeys:")
        col.label(text = "Don't remove the hotkeys, use disable checkbox", icon='INFO')

        col.separator()

        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user
        km = kc.keymaps["Window"]

        col.label(text = "Pop up search/open blend history")
        kmi = get_hotkey_entry_item(km, "path.open_from_history", "EXECUTE", "tab")
        if kmi:
            col.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        else:
            col.label(text = "Keymap was deleted, restart blender (if you have saved prefs, disable > re-enable addon to reset)")
            # col.operator("path.re_register_keymaps", text = "Restore Keymap").idname = 'path.open_from_history'

        # col.separator()
        # col.label(text = "Open last blend (without warning)")
        # kmi = get_hotkey_entry_item(km, "path.open_last_file","EXECUTE","tab")
        # if kmi:
        #     col.context_pointer_set("keymap", km)
        #     rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        # else:
        #     col.label(text = "Keymap was deleted, restart blender (if you have saved prefs, disable > re-enable addon to reset)")
            # col.operator("path.re_register_keymaps", text = "Restore Keymap").idname = 'path.open_from_history'

        # box = layout.box()
        # blender_locations(box)
        blender_locations(layout)
        
        ## addon folder list
        # layout.operator("path.open_addon_directory", text='Search And Open Addon Folder', icon='FILE_FOLDER')

        box = layout.box()
        expand_icon = 'TRIA_DOWN' if self.show_addon_open_buttons else 'TRIA_RIGHT'
        row = box.row()
        row.prop(self, 'show_addon_open_buttons', icon=expand_icon, emboss=False,) # text='Open Individual Addon Directory'
        row.operator("path.open_addon_directory", text='Search', icon='VIEWZOOM')
        ui_scale = context.preferences.view.ui_scale
        if self.show_addon_open_buttons:
            box.prop(self, 'filter')
            ## responsive column list
            if context.area.width > 2050 * ui_scale:
                colnum = 7
            elif context.area.width > 1750 * ui_scale:
                colnum = 6
            elif context.area.width > 1450 * ui_scale:
                colnum = 5
            elif context.area.width > 1150 * ui_scale:
                colnum = 4
            elif context.area.width > 850 * ui_scale:
                colnum = 3
            elif context.area.width > 550 * ui_scale:
                colnum = 2
            else:
                colnum = 1

            cf = box.column_flow(columns=colnum, align=True)
            for ad in open_addons_path.get_addons_modules_infos(self.filter):
                # path, name, diskname
                # col.operator("path.open_browser", text=ad[1]).filepath = ad[0]
                cf.operator("path.open_browser", text=ad[1]).filepath = ad[0]


def register():
    bpy.utils.register_class(PATH_addon_preferences)

def unregister():
    bpy.utils.unregister_class(PATH_addon_preferences)