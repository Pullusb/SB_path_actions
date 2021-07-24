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
    "version": (1, 7, 0),
    "blender": (2, 80, 0),
    "location": "Window top right corner and browser footer",
    "description": "Open blend file folder in OS explorer",
    "warning": "",
    "wiki_url": "https://github.com/Pullusb/SB_path_actions",
    "tracker_url": "https://github.com/Pullusb/SB_path_actions/issues/new",
    "category": "System"}

from . import (
            operators,
            blend_open_ops,
            panels,
            keymap)

import bpy, os
import rna_keymap_ui
from pathlib import Path

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
    bl_idname = __name__.split('.')[0] # __name__
    bl_label = "Addon Preferences"

    def draw(self, context):
        layout = self.layout

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
        row.operator("wm.path_open", text='User Addons').filepath = bpy.utils.user_resource('SCRIPTS', "addons")
        # local default installed addons (release)
        row.operator("wm.path_open", text='Native Addons').filepath = str(Path(bpy.utils.resource_path('LOCAL')) / 'scripts' / 'addons')

        # external scripts (if specified)
        preferences = bpy.context.preferences
        external_scripts = preferences.filepaths.script_directory
        if external_scripts and len(external_scripts) > 2:
            row.operator("wm.path_open", text='External Addons').filepath = str(Path(external_scripts))

        ## Config folder
        box.separator()
        row = box.row()
        row.label(text='Application locations')
        row = box.row()
        row.label(text='Open: ', icon='FILE_FOLDER')
        row.operator("wm.path_open", text='Config Folder').filepath = bpy.utils.user_resource('CONFIG')
        row.operator("wm.path_open", text='Application Folder').filepath = str(Path(bpy.app.binary_path).parent)


def register():
    blend_open_ops.register()
    operators.register()
    panels.register()
    keymap.register()
    bpy.utils.register_class(PATH_addon_preferences)

def unregister():
    bpy.utils.unregister_class(PATH_addon_preferences)
    keymap.unregister()
    panels.unregister()
    operators.unregister()
    blend_open_ops.unregister()
    
if __name__ == "__main__":
    register()
