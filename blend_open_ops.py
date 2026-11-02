import bpy
import os
import re
import sys
from os.path import basename, dirname, join, exists
from pathlib import Path
import subprocess
import time
from bpy.types import Operator
from . import path_func


class PATH_OT_open_in_new_instance(Operator) :
    bl_idname = "wm.open_in_new_instance"
    bl_label = 'Open Blend In New Instance'
    bl_description = "Open blend file in a new instance of blender\
        \nAlt + Click : Strip extra arguments from initial command, opening with command [blender filepath]"
    bl_options = {"REGISTER", "INTERNAL"}

    filepath : bpy.props.StringProperty(default='', options={'SKIP_SAVE'})
    strip_args : bpy.props.BoolProperty(default=False, options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties):
        desc = "Open blend file in a new instance of blender"
        if sys.argv and len(sys.argv) > 2:
            str_cmd = ' '.join(sys.argv[2:])
            desc += "\nAlt + Click : Strip extra arguments from initial command, opening with a simple [blender filepath]"
            desc += "\n"
            desc += f'\nExtra args: "{str_cmd}"'
        return desc

    def invoke(self, context, event):
        self.strip_args = event.alt
        return self.execute(context)

    def execute(self, context):
        path_func.open_blend_new_instance(self.filepath, strip_extra_args=self.strip_args)
        return {'FINISHED'}


def load_workspaces(src):
    '''Load all workspace from a file and return list'''
    with bpy.data.libraries.load(str(src), link=False) as (data_from, data_to):
        setattr(data_to, 'workspaces', [item for item in getattr(data_from, 'workspaces')])
    return data_to.workspaces

def replace_workspaces(source_blend):
    ### replace
    ## rename wk to temp
    
    active_workspace_name = bpy.context.workspace.name
    tmp = 'tmpold_'
    
    current_wks = [w for w in bpy.data.workspaces]
    for wk in current_wks:
        wk.name = f'{tmp}_{wk.name}'

    new_wks = load_workspaces(source_blend)

    ## import user workspaces
    if not len(new_wks):
        print('could not load new workspaces, Abort')
        ## remove tmp prefix from name and abort
        for wk in reversed(current_wks):
            if wk.name.startswith(tmp):
                wk.name = wk.name[len(tmp):]
        return

    ## Remove old temp workspaces by name
    for wk in reversed(current_wks):
        if wk.name.startswith(tmp):
            with bpy.context.temp_override(workspace=wk):
                bpy.ops.workspace.delete()
    
    same_wk = next((w for w in new_wks if w.name == active_workspace_name), None)
    
    if same_wk:
        # print('Restore new workspace tab with same previous name')
        bpy.context.window.workspace = same_wk
    # else:
    #     bpy.context.window.workspace = new_wks[0] # <- not the first in tab list

def load_startup_workspace():
    ## find startup source
    user_startup = Path(bpy.utils.resource_path('USER'), 'config', 'startup.blend')

    if user_startup.exists():
        # user startup
        source_blend = str(user_startup)
        print('using startup:', source_blend)
        replace_workspaces(source_blend)
        return source_blend

    print('!! No custom user startup!!')        

class PATH_OT_full_reopen(Operator) :
    bl_idname = "wm.full_reopen"
    bl_label = 'Full Reopen Blend'
    bl_description = "Close and re-open blender file\
        \nCtrl: Force reopen even if file is not saved"
    bl_options = {"REGISTER", "INTERNAL"}

    def invoke(self, context, event):
        ## Alt action : Replace workspaces by appending startup and removing current
        ## TODO: Can crash, need testing before implementation.
        # if event.alt:
        #     ret = load_startup_workspace()
        #     if not ret:
        #         self.report({'ERROR'}, 'Need to save a startup file first (File > Defaults > Save Startup File)')
        #         return {'CANCELLED'}
        #     self.report({'INFO'}, f'Loaded startup file workspaces from: {ret}')
        #     return {'FINISHED'}

        ## "full reopen" action (skip prompt with ctrl)
        if bpy.data.is_dirty and not event.ctrl:
            wm = context.window_manager
            return wm.invoke_props_dialog(self)
        return self.execute(context)
    
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text='File is not saved! Reopen anyway ?')
        col.label(text='(use Ctrl to bypass this prompt even if not saved)')
        
    def execute(self, context):
        path_func.open_blend_new_instance()
        # Delay to avoid quitting before subprocess is launched
        time.sleep(0.1) # lower value ?
        bpy.ops.wm.quit_blender()
        return {'FINISHED'}

class PATH_OT_open_side_blend(Operator) :
    bl_idname = "wm.open_side_blend"
    bl_label = 'Open Side Blend'
    bl_description = "Open blend in same folder as current"
    bl_options = {"REGISTER"}

    sort_by : bpy.props.EnumProperty(
        name="Sort By",
        items=(
            ('NAME', "Name", "Sort by name", 'SORTALPHA', 0),
            ('DATE', "Date", "Sort by modification date, last saved on top", 'SORTTIME', 1),
        ),
        default='NAME',
    )

    @classmethod
    def poll(cls, context):
        return bpy.data.is_saved

    def invoke(self, context, event):
        ## list surrounding blends with their modification time
        try:
            self.mtimes = {Path(i.path): i.stat().st_mtime for i in os.scandir(Path(bpy.data.filepath).parent) if i.is_file() and i.name.endswith('.blend')}
            self.blend_list = list(self.mtimes)
        except OSError as e:
            self.report({'ERROR'}, f'Cannot access blend folder: {e}')
            return {'CANCELLED'}

        ## Best to list the file even if solo (that way can open another instance quickly)
        # if not self.blend_list:
        #     self.report({'WARNING'}, 'No blend file found in current blend location !')
        #     return {'CANCELLED'}

        natural_sort = lambda x: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', x.name)]
        try:
            self.blend_list.sort(key=natural_sort)
        except Exception:
            self.blend_list.sort(key=lambda x: x.name)
        
        ## Adapt panel size to longest name... (Not predictable, font is not monospace)
        self.longest_path = max([len(i.name) for i in self.blend_list])
        estimated = int(self.longest_path * 8.8) + 70 # + date column
        popup_width = max(370, estimated) # low clamp
        popup_width = min(popup_width, 600) # high clamp

        # print('longest_path:', self.longest_path)# Dbg
        # print('estimated width: ', estimated)# Dbg

        ## using a 'props_popup' crashes blender (using dialog add an OK button...but works)
        # return wm.invoke_props_popup(self, event) # need "undo" in bl_options else get an error
        wm = context.window_manager
        return context.window_manager.invoke_props_dialog(self, width=popup_width)

    def draw(self, context):
        layout = self.layout
        layout.row().prop(self, 'sort_by', expand=True)

        main_row = layout.row(align=True)
        blend_col = main_row.column(align=True)
        blend_col.alignment = 'LEFT'

        date_col = main_row.column(align=True)
        date_col.alignment = 'RIGHT'

        # main_row.separator_spacer()
        # main_row.separator()
        option_col = main_row.column(align=True)
        option_col.alignment = 'RIGHT'
        # option_col.ui_units_x = 2.2

        blend_list = self.blend_list
        if self.sort_by == 'DATE':
            blend_list = sorted(blend_list, key=lambda x: self.mtimes[x], reverse=True)

        for path in blend_list:
            blend_row = blend_col.row()
            blend_row.alignment = 'LEFT'
            
            if path == Path(bpy.data.filepath):
                ## Current file, Displayed but disabled (non-clickable)
                blend_row.enabled=False
                blend_row.operator('wm.open_mainfile', text=path.name, emboss=False).filepath = str(path) # path.as_posix()
            
            else:
                # blend_row.operator_context = "EXEC_AREA"# , (should be "INVOKE_AREA" if file was not saved) # no need in blender 4.2+
                op = blend_row.operator('wm.open_mainfile', text=path.name, emboss=False)
                op.filepath = str(path)
                op.display_file_selector = False # adding this arg (True or False) display the warning correctly when file is not saved
                op.load_ui = context.preferences.filepaths.use_load_ui

            date_row = date_col.row()
            date_row.alignment = 'RIGHT'
            date_row.active = False # greyed, secondary info
            date_row.label(text=time.strftime('%Y-%m-%d %H:%M', time.localtime(self.mtimes[path])))

            # option_row = option_col.box()
            option_row = option_col.row(align=True)
            option_row.alignment = 'RIGHT'
            option_row.operator('wm.open_in_new_instance', text='', icon='FILE_BACKUP').filepath = str(path)
            option_row.operator('pathaction.copy_path', text='', icon='COPYDOWN').path = str(path)

    def execute(self, context):
        return {'FINISHED'}

class PATH_OT_open_browser(Operator):
    bl_idname = "path.open_browser"
    bl_label = "Open Path In Browser"
    bl_description = "Open passed file/folder in OS browser. If a file, the file will be selected"
    bl_options = {"REGISTER", "INTERNAL"}

    filepath : bpy.props.StringProperty(options={'SKIP_SAVE'})

    def execute(self, context):
        if not self.filepath:
            self.report({'ERROR'}, 'No filepath')
            return {"CANCELLED"}
        if not exists(self.filepath):
            self.report({'ERROR'}, f'Not found : {self.filepath}')
            return {"CANCELLED"}

        path_func.open_folder(self.filepath)

        self.report({'INFO'}, f'Open: {self.filepath}')
        return {"FINISHED"}

def get_exportable_ids(context):
    '''Return local datablocks selected in outliner (fallback on hovered id)'''
    ids = list(getattr(context, 'selected_ids', None) or [])
    hovered = getattr(context, 'id', None)
    if hovered is not None and hovered not in ids:
        ids.append(hovered)
    return [i for i in ids
            if i.library is None
            and not isinstance(i, (bpy.types.WindowManager, bpy.types.Screen, bpy.types.Library))]

class PATH_OT_export_datablocks_to_blend(Operator):
    bl_idname = "path.export_datablocks_to_blend"
    bl_label = "Export To Blend"
    bl_description = "Write selected local datablocks (and their dependencies) to an external blend file"
    bl_options = {"REGISTER", "INTERNAL"}

    filepath : bpy.props.StringProperty(subtype='FILE_PATH', options={'SKIP_SAVE'})
    filter_glob : bpy.props.StringProperty(default='*.blend', options={'HIDDEN'})
    ## Highlight filename in red in file browser when it already exists
    check_existing : bpy.props.BoolProperty(default=True, options={'HIDDEN'})

    compress : bpy.props.BoolProperty(name='Compress', default=True,
        description='Write compressed blend file')

    fake_user : bpy.props.BoolProperty(name='Fake User', default=False,
        description='Set fake user on written datablocks')

    mark_asset : bpy.props.BoolProperty(name='Mark As Asset', default=False,
        description='Mark exported datablocks as assets in the written file\
            \nOnly supported types (object, collection, material, node group, world, action, brush)\
            \nPreview thumbnail is not generated (existing previews are kept)\
            \nCurrent file is left unchanged')

    path_remap : bpy.props.EnumProperty(name='Path Remap', default='RELATIVE',
        description='How to handle external file paths',
        items=(
            ('NONE', 'None', 'No path manipulation'),
            ('RELATIVE', 'Relative', 'Remap paths that are already relative to the new location'),
            ('RELATIVE_ALL', 'Relative All', 'Remap all paths to be relative to the new location'),
            ('ABSOLUTE', 'Absolute', 'Make all paths absolute on writing'),
        ))

    def invoke(self, context, event):
        self.datablocks = get_exportable_ids(context)
        if not self.datablocks:
            self.report({'ERROR'}, 'No local datablock selected')
            return {'CANCELLED'}

        if not self.filepath:
            name = self.datablocks[0].name if len(self.datablocks) == 1 else 'datablocks'
            folder = dirname(bpy.data.filepath) if bpy.data.filepath else str(Path.home())
            self.filepath = join(folder, bpy.path.clean_name(name) + '.blend')

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        datablocks = getattr(self, 'datablocks', None) or get_exportable_ids(context)
        if not datablocks:
            self.report({'ERROR'}, 'No local datablock to export')
            return {'CANCELLED'}

        if not self.filepath:
            self.report({'ERROR'}, 'No filepath given')
            return {'CANCELLED'}

        filepath = bpy.path.ensure_ext(bpy.path.abspath(self.filepath), '.blend')
        if bpy.data.filepath and Path(filepath) == Path(bpy.data.filepath):
            self.report({'ERROR'}, 'Cannot overwrite current blend file')
            return {'CANCELLED'}

        ## Temporarily mark as asset, restored after write
        ## (asset_mark/asset_clear also toggle fake user, so store its state)
        restore = []
        asset_count = 0
        if self.mark_asset:
            for id in datablocks:
                if id.asset_data is not None:
                    asset_count += 1
                    continue
                use_fake_user = id.use_fake_user
                id.asset_mark()
                if id.asset_data is not None: # unsupported types are not marked
                    restore.append((id, use_fake_user))
                    asset_count += 1

        try:
            bpy.data.libraries.write(filepath, set(datablocks),
                                     path_remap=self.path_remap,
                                     fake_user=self.fake_user,
                                     compress=self.compress)
        except Exception as e:
            self.report({'ERROR'}, f'Export failed: {e}')
            return {'CANCELLED'}
        finally:
            for id, use_fake_user in restore:
                id.asset_clear()
                id.use_fake_user = use_fake_user

        msg = f'Exported {len(datablocks)} datablock(s)'
        if self.mark_asset:
            msg += f' ({asset_count} as asset)'
        level = 'WARNING' if self.mark_asset and asset_count < len(datablocks) else 'INFO'
        self.report({level}, f'{msg} to: {filepath}')
        return {'FINISHED'}


def show_export_on_outliner_entry(self, context):
    if not context.preferences.addons[__package__].preferences.dev_mode:
        return
    if not get_exportable_ids(context):
        return
    layout = self.layout
    layout.separator()
    col = layout.column()
    ## OUTLINER_MT_object is called with EXEC context, force invoke to get the file browser
    col.operator_context = 'INVOKE_REGION_WIN'
    col.operator('path.export_datablocks_to_blend', icon='EXPORT')


def show_open_ops_on_outliner_entry(self, context):
    if not getattr(context, 'id'):
        return
    id = context.id

    ## Possible filter by type
    # id_type = id.bl_rna.name # type(id).__name__ 
    # if id_type.lower() not in ('library',):
    #     return

    ## Only for items with a filepath (non-empty)
    if not getattr(id, 'filepath', None):
        return

    layout = self.layout
    layout.separator()
    col = layout.column()

    path = id.filepath
    abs_path = os.path.abspath(bpy.path.abspath(str(path)))

    col.operator('path.open_browser', text='Open Containing Folder', icon='FILE_FOLDER').filepath = abs_path
    col.operator('pathaction.copy_path', icon='COPYDOWN').path = str(path)
    if path.endswith('.blend'):
        col.operator('wm.open_in_new_instance', icon='FILE_BACKUP').filepath = str(path)

    self.layout.separator()

classes = (
PATH_OT_open_in_new_instance,
PATH_OT_full_reopen,
PATH_OT_open_side_blend,
PATH_OT_open_browser,
PATH_OT_export_datablocks_to_blend,
)

outliner_menus = ('OUTLINER_MT_context_menu', 'OUTLINER_MT_object', 'OUTLINER_MT_collection')

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.OUTLINER_MT_context_menu.append(show_open_ops_on_outliner_entry)
    for menu in outliner_menus:
        getattr(bpy.types, menu).append(show_export_on_outliner_entry)

def unregister():
    for menu in outliner_menus:
        getattr(bpy.types, menu).remove(show_export_on_outliner_entry)
    bpy.types.OUTLINER_MT_context_menu.remove(show_open_ops_on_outliner_entry)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
