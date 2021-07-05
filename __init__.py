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
    "version": (1, 6, 0),
    "blender": (2, 80, 0),
    "location": "Window top right corner and browser footer",
    "description": "Open output path or blend file location in OS explorer",
    "warning": "",
    "wiki_url": "https://github.com/Pullusb/SB_path_actions",
    "tracker_url": "https://github.com/Pullusb/SB_path_actions/issues/new",
    "category": "System"}

"""
Usage:
Add buttons in properties > render > Output pannel and filebrowser
quick-use: search "folder" in the spacebar menu
"""

from . import (
            operators,
            blend_open_ops,
            panels,
            keymap)

import bpy
import rna_keymap_ui

# def get_hotkey_entry_item(km, kmi_name):
def get_hotkey_entry_item(km, kmi_name, kmi_value, properties):
    for i, km_item in enumerate(km.keymap_items):
        if km.keymap_items.keys()[i] == kmi_name:
            return km_item
        # elif properties == 'none':
        #     return km_item
    return None


class PATH_AddonPreferences(bpy.types.AddonPreferences):
    """ Preference Settings Addon Panel"""
    bl_idname = __name__.split('.')[0] # __name__
    bl_label = "Addon Preferences"

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        col.label(text = "Hotkeys:")
        col.label(text = "Do NOT remove hotkeys, disable them instead.", icon='INFO')

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

        col.separator()

        col.label(text = "Open last blend (without warning)")
        kmi = get_hotkey_entry_item(km, "path.open_last_file","EXECUTE","tab")
        if kmi:
            col.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        else:
            col.label(text = "Keymap was deleted, restart blender (if you have saved prefs, disable > re-enable addon to reset)")
            # col.operator("path.re_register_keymaps", text = "Restore Keymap").idname = 'path.open_from_history'



def register():
    blend_open_ops.register()
    operators.register()
    panels.register()
    keymap.register()
    bpy.utils.register_class(PATH_AddonPreferences)

def unregister():
    bpy.utils.unregister_class(PATH_AddonPreferences)
    keymap.unregister()
    panels.unregister()
    operators.unregister()
    blend_open_ops.unregister()
    
if __name__ == "__main__":
    register()
