# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Path Actions",
    "author": "Samuel Bernou",
    "version": (2, 0, 11),
    "blender": (4, 2, 0),
    "location": "Window top right corner, browser up-left corner, addon prefs",
    "description": "Open blend folder in OS explorer",
    "warning": "",
    "doc_url": "https://github.com/Pullusb/SB_path_actions",
    "tracker_url": "https://github.com/Pullusb/SB_path_actions/issues/new",
    "category": "System"}

from . import (
            operators,
            blend_open_ops,
            extend_history,
            open_addons_path,
            panels,
            keymap)

import bpy, os
import rna_keymap_ui
from pathlib import Path
# import addon_utils

# def get_hotkey_entry_item(km, kmi_name):
def get_hotkey_entry_item(km, kmi_name, kmi_value, properties):
    for i, km_item in enumerate(km.keymap_items):
        if km.keymap_items.keys()[i] == kmi_name:
            return km_item
        # elif properties == 'none':
        #     return km_item
    return None


class PATH_addon_preferences(bpy.types.AddonPreferences):
    """ Preference Settings Addon Panel"""
    bl_idname = __package__
    bl_label = "Addon Preferences"

    # show_addon_loc_details : bpy.props.BoolProperty(name='All Addons load folders', default=False)

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
        kmi = get_hotkey_entry_item(km, "path.open_from_history","EXECUTE","tab")
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

        box = layout.box()
        row = box.row()
        row.label(text='Addons locations ')
        row = box.row()
        
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
                row = box.row()
                row.label(text='Script directories:', icon='FILE_FOLDER')
                for s in preferences.filepaths.script_directories:
                    if s.directory:
                        row.operator("wm.path_open", text=s.name).filepath = str(Path(s.directory))

        ## Config folder
        box.separator()
        row = box.row()
        row.label(text='Application locations')
        row = box.row()
        row.label(text='Open: ', icon='FILE_FOLDER')
        row.operator("wm.path_open", text='Config Folder').filepath = bpy.utils.user_resource('CONFIG')
        row.operator("wm.path_open", text='Application Folder').filepath = str(Path(bpy.app.binary_path).parent)

        ## Addons external pathes
        
        # box = layout.box()
        # box.prop(self, 'show_addon_loc_details')
        # if self.show_addon_loc_details:
        #     for fp in addon_utils.paths():
        #         row = box.row()
        #         # row.operator("wm.path_open", text=fp).filepath = fp
        #         row.operator("path.open_browser", text=fp).filepath = fp
        
        
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
    extend_history.register()
    blend_open_ops.register()
    operators.register()
    open_addons_path.register()
    panels.register()
    keymap.register()
    bpy.utils.register_class(PATH_addon_preferences)

def unregister():
    bpy.utils.unregister_class(PATH_addon_preferences)
    keymap.unregister()
    panels.unregister()
    open_addons_path.unregister()
    operators.unregister()
    blend_open_ops.unregister()
    extend_history.unregister()
    
if __name__ == "__main__":
    register()
