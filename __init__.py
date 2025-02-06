# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Path Actions",
    "author": "Samuel Bernou",
    "version": (2, 3, 3),
    "blender": (4, 2, 0),
    "location": "Window top right corner, browser up-left corner, addon prefs",
    "description": "Open blend folder in OS explorer",
    "warning": "",
    "doc_url": "https://github.com/Pullusb/SB_path_actions",
    "tracker_url": "https://github.com/Pullusb/SB_path_actions/issues/new",
    "category": "System"}

from . import (
            operators,
            history,
            blend_open_ops,
            extend_history,
            open_addons_path,
            panels,
            keymap,
            prefs)

mods = (
    operators,
    blend_open_ops,
    history,
    extend_history,
    open_addons_path,
    panels,
    keymap,
    prefs,
)

def register():
    for mod in mods:
        mod.register()

def unregister():
    for mod in reversed(mods):
        mod.unregister()
    
if __name__ == "__main__":
    register()
