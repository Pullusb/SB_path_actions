import bpy

addon_keymaps = []
def register_keymaps(force=False):
    if bpy.app.background:
        return
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name = "Window", space_type = "EMPTY")

    ## Pop up history
    # idn = 'path.open_from_history' # pure-search popup
    idn = 'pathaction.blend_history' # custom history popup
    kmi = km.keymap_items.get(idn)

    ## Menu open with search
    if not kmi or force:
        kmi = km.keymap_items.new(idn,
        type = "O", value = "PRESS", shift = True, ctrl = True, alt = True)
        addon_keymaps.append((km, kmi))

def unregister_keymaps():
    if bpy.app.background:
        return
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

### ---

def register():
    register_keymaps()

def unregister():
    unregister_keymaps()
