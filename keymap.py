import bpy

addon_keymaps = []
def register_keymaps(force=False):
    if bpy.app.background:
        return
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name = "Window", space_type = "EMPTY")

    ## Pop up search in history
    idn = 'path.open_from_history'
    kmi = km.keymap_items.get(idn)

    # refresh here
    # if kmi:
    #     km.keymap_items.remove(idn)
    # kmi = km.keymap_items.new(idn, 
    # type = "O", value = "PRESS", shift = True, ctrl = True, alt = True)
    # addon_keymaps.append((km, kmi))
    
    ## Menu open with search
    if not kmi or force:
        kmi = km.keymap_items.new(idn, 
        type = "O", value = "PRESS", shift = True, ctrl = True, alt = True)
        addon_keymaps.append((km, kmi))
    # else:
    #     print(f'Found kmi {idn}')
    
    ## Open last blend in one go
    # idn = 'path.open_last_file'
    # kmi = km.keymap_items.get(idn)
    # if not kmi or force:
    #     kmi = km.keymap_items.new(idn, 
    #     type = "P", value = "PRESS", shift = True, ctrl = True, alt = True)
    #     addon_keymaps.append((km, kmi))

def unregister_keymaps():
    if bpy.app.background:
        return
    for km, kmi in addon_keymaps:
        if km.keymap_items.get(kmi.idname):
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()

""" 
# /old
class PATH_OT_re_register_keymap(bpy.types.Operator):
    bl_idname = "path.re_register_keymaps"
    bl_label = "Register Addon Keymaps"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):        
        register_keymaps()
        return {'FINISHED'}
# old/

# unregistered not exposed anymore
class PATH_OT_re_register_keymap(bpy.types.Operator):
    bl_idname = "path.re_register_keymaps"
    bl_label = "Register Addon Keymaps"
    bl_options = {'REGISTER', 'INTERNAL'}

    idname: bpy.props.StringProperty()

    def execute(self, context):
        # Clean addon_keymap list 
        # wm = bpy.context.window_manager
        # kc = wm.keyconfigs.user

        # print('addon_keymaps: ', len(addon_keymaps))
        to_pop = []
        for i, kmp in enumerate(addon_keymaps):
            km, kmi = kmp
            idn = kmi.idname
            if self.idname == kmi.idname:
                print('idname found', self.idname)
                if km.keymap_items.get(kmi.idname):
                    ## try removing in user...
                    # kmu = kc.keymaps[km.name]
                    # kmui = kmu.keymap_items.get(idn)
                    # if kmui:
                    #     print('found kmui')
                    #     kmu.keymap_items.remove(kmui)

                    km.keymap_items.remove(kmi)
                    to_pop.append(i)
        
        print('to_pop: ', to_pop)

        for i in reversed(to_pop):
            del addon_keymaps[i]
            # addon_keymaps.pop(i)

        # register again
        register_keymaps() #  force=True 
        return {'FINISHED'}
"""

### ---

def register():
    register_keymaps()
    # bpy.utils.register_class(PATH_OT_re_register_keymap)

def unregister():
    # bpy.utils.unregister_class(PATH_OT_re_register_keymap)
    unregister_keymaps()