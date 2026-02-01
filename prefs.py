import bpy
import rna_keymap_ui
from pathlib import Path
import tempfile
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
    layout.label(text='Browse Blender Folders', icon='FILE_FOLDER')
    col = layout.column(align=False)

    ## Config folder
    col.label(text='Application:')
    row = layout.row()

    config_folder = bpy.utils.user_resource('CONFIG')
    row = col.row(align=True)
    row.operator("wm.path_open", text='Config').filepath = config_folder
    row.operator("pathaction.copy_path", text="", icon='COPYDOWN').path = config_folder

    bin_path = Path(bpy.app.binary_path)
    app_folder = str(bin_path.parent)
    row = col.row(align=True)
    row.operator("wm.path_open", text='Blender App Folder').filepath = app_folder
    row.operator("pathaction.copy_path", text="", icon='COPYDOWN').path = app_folder

    row = col.row(align=True)
    row.operator("pathaction.copy_path", text="Copy Blender Executable Path", icon='COPYDOWN').path = str(bin_path)

    col.separator()

    col.label(text='Scripts / Addons:')
    # Extensions
    if bpy.app.version >= (4, 2, 0):
        extension_dir = str(Path(bpy.utils.user_resource('EXTENSIONS')))
        row = col.row(align=True)
        row.operator("wm.path_open", text='Extensions').filepath = extension_dir
        row.operator("pathaction.copy_path", text="", icon='COPYDOWN').path = extension_dir


    user_scripts = str(Path(bpy.utils.user_resource('SCRIPTS')))
    row = col.row(align=True)
    # Local user addon source (usually appdata/.config folders). Where it goes when 'install from file'
    row.operator("wm.path_open", text='User Scripts').filepath = user_scripts
    row.operator("pathaction.copy_path", text="", icon='COPYDOWN').path = user_scripts
    
    # local default installed addons (release)

    native_scripts = str(Path(bpy.utils.resource_path('LOCAL')) / 'scripts')
    row = col.row(align=True)
    row.operator("wm.path_open", text='Native Scripts').filepath = native_scripts
    row.operator("pathaction.copy_path", text="", icon='COPYDOWN').path = native_scripts

    # external scripts (if specified)
    preferences = bpy.context.preferences
    if bpy.app.version < (3, 6, 0):
        external_scripts = preferences.filepaths.script_directory
        if external_scripts and len(external_scripts) > 2:
            extern_script = str(Path(external_scripts))
            row = col.row(align=True)
            row.operator("wm.path_open", text='External Addons').filepath = extern_script
            row.operator("pathaction.copy_path", text="", icon='COPYDOWN').path = extern_script
    else:
        if len(preferences.filepaths.script_directories):
            col.label(text='Other Script Directories:')
            for s in preferences.filepaths.script_directories:
                if s.directory:
                    row = col.row(align=True)
                    row.operator("wm.path_open", text=s.name).filepath = str(Path(s.directory))
                    row.operator("pathaction.copy_path", text="", icon='COPYDOWN').path = str(Path(s.directory))

    if not bpy.context.preferences.addons[__package__].preferences.dev_mode:
        return

    col.separator()
    col.label(text='Dev Extras:')
    temp_dir = tempfile.gettempdir()
    row = col.row(align=True)
    row.operator("wm.path_open", text='Temp Directory').filepath = temp_dir
    row.operator("pathaction.copy_path", text="", icon='COPYDOWN').path = temp_dir

    col.operator("pathaction.links_checker", text="Check File Links", icon='LINKED') # Check Links 
    
    ## Temp directory of current session (not really useful)
    # session_temp_dir = bpy.app.tempdir
    # row = col.row(align=True)
    # row.operator("wm.path_open", text='Session Temp Directory').filepath = session_temp_dir
    # row.operator("pathaction.copy_path", text="", icon='COPYDOWN').path = session_temp_dir


class PATH_addon_preferences(bpy.types.AddonPreferences):
    """ Preference Settings Addon Panel"""
    bl_idname = __package__
    bl_label = "Addon Preferences"

    dev_mode : bpy.props.BoolProperty(name='Developer mode',
        description='Add a button on upper-right corner to fully reopen blender with current file (not just revert)\
            \nAdd features for developpers, TDs or advanced users (temp folder shortcut, link checker,...)',
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