import bpy
import re   
from . import path_func
from pathlib import Path
from bpy.types import Operator


def get_addon_location(fp) -> str:
    '''get addon filepath and return a name of the addon location'''
    # fp = str(Path(fp))
    if fp.startswith( str(Path(bpy.utils.user_resource('SCRIPTS')) / 'addons') ):
        return 'user'

    if fp.startswith( str(Path(bpy.utils.resource_path('LOCAL')) / 'scripts' / 'addons') ):
        return 'native'

    if bpy.app.version < (3, 6, 0):
        external_scripts = bpy.context.preferences.filepaths.script_directory
        if external_scripts:
            if fp.startswith( str(Path(external_scripts)) ):
                return 'external'
    else:
        external_scripts = bpy.context.preferences.filepaths.script_directories
        for s in external_scripts:
            if s.directory and fp.startswith( str(Path(s.directory)) ):
                return 'external'

    return 'other'

def get_addons_modules_infos(filter="ALL", module_name_first=False):
    import addon_utils

    addon_list = []
    module_list = []
    remodule = re.compile(r"<module '(.*?)' from '(.*?)'>")
    
    for i, m in enumerate(addon_utils.modules()):
        n = m.bl_info.get('name','')
        
        res = remodule.search(str(m))
        if not res:
            continue

        diskname, fp = res.group(1), Path(res.group(2))
        
        installed, current = addon_utils.check(diskname)
        if filter != 'ALL':
            if filter == 'ACTIVE' and not current: # (installed or current)
                continue
            elif filter == 'INACTIVE' and current: # (installed or current)
                continue
        
        if not diskname or not n or not fp:
            continue
        
        if module_name_first:
            ## To return module name in enum choice (open preferences)
            # [0] Diskname(modulename), [1] bl_info name, [2] diskpath
            display_name = n
            if filter == 'ALL':
                if current:
                    ## show a number for status prefix
                    ## a bit ugly, but can be used as ultra fast filter when typing
                    display_name = '1 ' + display_name
                    # display_name += ' (on)'
                else:
                    display_name = '0 ' + display_name
                    # display_name += ' (off)'

            addon_list.append((diskname, display_name, str(fp)))
        else:
            ## To return path in enum choice (open path)
            ## [0] diskpath, [1] bl_info name, [2] Diskname(modulename)
            addon_list.append((str(fp), n, diskname))
        # module (can access m.bl_info['version']...etc)
        module_list.append(m)

    ## / treat duplicate name (check for infos on conflict)
    # find duplicate indices
    namelist = [x[1] for x in addon_list]
    dup_index = list(set(i for i, x in enumerate(namelist) if namelist.count(x) > 1))

    # add version and location name
    for idx in dup_index:
        disk_path = addon_list[idx][2] if module_name_first else addon_list[idx][0] 
        loc = get_addon_location(disk_path)
        version = str(module_list[idx].bl_info.get('version', '')).replace(" ", "").strip('()')
        # replace with new tuple
        addon_list[idx] = (addon_list[idx][0], f'{addon_list[idx][1]} ({loc} {version})', addon_list[idx][2])    

    return addon_list

def get_addon_list(self, context):
    '''return (identifier, name, description) of enum content
    Get all addon found as ([0] diskpath, [1] bl_info name, [2] Diskname (modulename))
    In enum prop item, return folderpath of the addon'''
    return get_addons_modules_infos()

class PATH_OT_search_open_addon_path(Operator) :
    bl_idname = "path.open_addon_directory"
    bl_label = "Open Addon Directory"
    bl_description = "Open chosen addon directory"
    bl_options = {'REGISTER'}
    # important to have the updated enum here as bl_property
    bl_property = "addons_enum"

    addons_enum : bpy.props.EnumProperty(
        name="Addons",
        description="Choose addon in list",
        items=get_addon_list
        )
    
    # There is a known bug with using a callback,
    # Python must keep a reference to the strings returned by the callback
    # or Blender will misbehave or even crash.

    addons : bpy.props.StringProperty(default='', options={'SKIP_SAVE'}) # need to have a variable to store (to get it in self)

    def execute(self, context):
        chosen = self.addons_enum
        self.report({'INFO'}, f'Open: {chosen}')
        path_func.open_folder(chosen)
        return {'FINISHED'}

    def invoke(self, context, event):
        # all_addons_l = get_addons_modules_infos()
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}


def get_addon_enabled_module_name_list(self, context):
    '''return (identifier, name, description) of enum content
    Get all addon found as ([0] Diskname (modulename), [1] bl_info name, [2] diskpath)
    In enum prop item, return module name of the addon, to open preferences'''
    return get_addons_modules_infos(module_name_first=True) # filter='ACTIVE' #  show only enabled ?

# Duplicate of above but to open preferences.
class PATH_OT_search_open_addon_preferences(Operator) :
    bl_idname = "path.search_open_addon_preferences"
    bl_label = "Search And Open Addon Preferences"
    bl_description = "Open chosen addon preferences (only enabled addons are listed)"
    bl_options = {'REGISTER'}
    # important to have the updated enum here as bl_property
    bl_property = "addons_enum"

    addons_enum : bpy.props.EnumProperty(
        name="Addons",
        description="Choose addon in list to open preferences",
        items=get_addon_enabled_module_name_list
        )

    addons : bpy.props.StringProperty(default='', options={'SKIP_SAVE'}) # need to have a variable to store (to get it in self)

    def execute(self, context):
        chosen = self.addons_enum # chosen addon module name
        self.report({'INFO'}, f'Open module preferences: {chosen}')
        bpy.ops.preferences.addon_show(module=chosen)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}

classes = (
PATH_OT_search_open_addon_path,
PATH_OT_search_open_addon_preferences,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)