import bpy
import re   
from . import path_func
from pathlib import Path
from bpy.types import Operator


def get_addons_modules_infos(filter="ALL"):
    import addon_utils

    addon_list = []
    remodule = re.compile(r"<module '(.*?)' from '(.*?)'>")

    for i, m in enumerate(addon_utils.modules()):
        n = m.bl_info.get('name','')
        
        res = remodule.search(str(m))
        if not res:
            continue

        diskname, fp = res.group(1), Path(res.group(2))
        
        if filter != 'ALL':
            installed, current = addon_utils.check(diskname)
            if filter == 'ACTIVE' and not current: # (installed or current)
                continue
            elif filter == 'INACTIVE' and current: # (installed or current)
                continue
        
        if not diskname or not n or not fp:
            continue
        addon_list.append((str(fp), n, diskname))

    return addon_list


def get_addon_list(self, context):
    '''return (identifier, name, description) of enum content'''
    return get_addons_modules_infos() # self.all_addons_l
    # return [(i.path, basename(i.path), "") for i in self.blends]


class PATH_OT_search_open_addon_path(Operator) :
    bl_idname = "path.open_addon_directory"
    bl_label = 'Open addon directory'
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
        path_func.openFolder(chosen)

        return {'FINISHED'}

    def invoke(self, context, event):
        all_addons_l = get_addons_modules_infos()
        wm = context.window_manager
        wm.invoke_search_popup(self) # can't specify size... width=500, height=600
        return {'FINISHED'}

classes = (
PATH_OT_search_open_addon_path,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)