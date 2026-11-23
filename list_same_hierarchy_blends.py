## Same depth blends
## List blends located at the same hierarchy depth as current blend
## (in sibling folders, up to N parent levels), with live filters

import bpy
import os
import re
import time
from fnmatch import fnmatch
from pathlib import Path
from bpy.types import Operator
from . import blend_nav_list

## Max number of rows drawn in popup (copy to clipboard always use the full filtered list)
MAX_DISPLAY = 61
## Safety: stop going deeper when a level contains too many folders
MAX_FOLDERS_PER_LEVEL = 10000


class BlendItem:
    __slots__ = ('path', 'rel', 'rel_dirs', 'mtime', 'sort_key')

    def __init__(self, path, base, mtime):
        self.path = path
        rel = path.relative_to(base)
        self.rel = rel.as_posix()
        self.rel_dirs = rel.parts[:-1] # folders between base and blend
        self.mtime = mtime
        self.sort_key = [natural_key(p) for p in self.rel_dirs] + [natural_key(path.stem)]


## Scan result is stored at module level (not on operator instance)
## so property update callbacks and draw can access it
_cache = {
    'blend': None, # blend filepath used for scan
    'base': None, # folder from which blends are listed
    'levels': 0, # effective parent levels (can be lower than requested if reaching root)
    'requested_levels': 0,
    'items': [],
    'folder_count': 0,
    'folder_names': [], # unique folder names found (for parent filter suggestions)
    'errors': 0,
    'truncated': False,
    'scan_time': 0.0,
    'filtered': [], # last filtered list displayed in popup (used by copy operator)
}


def natural_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]


def scan_same_depth(blend_path, levels):
    '''List blends at same depth as blend_path, going up "levels" parent folders.
    Fill module cache and return it'''
    start = time.perf_counter()
    current = Path(blend_path)
    base = current.parent
    effective = 0
    for _ in range(levels):
        if base.parent == base: # reached root
            break
        base = base.parent
        effective += 1

    ## Do not skip hidden folders that are part of current blend path
    current_parts = set(current.parts)
    errors = 0
    truncated = False
    folder_names = set()

    ## Walk down level by level (no recursion past target depth)
    folders = [base]
    for _ in range(effective):
        sub_folders = []
        for folder in folders:
            try:
                with os.scandir(folder) as it:
                    for entry in it:
                        if entry.name.startswith('.') and entry.name not in current_parts:
                            continue
                        try:
                            if entry.is_dir():
                                sub_folders.append(Path(entry.path))
                                folder_names.add(entry.name)
                        except OSError:
                            errors += 1
            except OSError:
                errors += 1
            if len(sub_folders) > MAX_FOLDERS_PER_LEVEL:
                truncated = True
                break
        folders = sub_folders
        if truncated:
            break

    items = []
    if not truncated:
        for folder in folders:
            try:
                with os.scandir(folder) as it:
                    for entry in it:
                        if not entry.name.endswith('.blend'):
                            continue
                        try:
                            if entry.is_file():
                                items.append(BlendItem(Path(entry.path), base, entry.stat().st_mtime))
                        except OSError:
                            errors += 1
            except OSError:
                errors += 1

    items.sort(key=lambda x: x.sort_key)

    _cache.update(
        blend=blend_path,
        base=base,
        levels=effective,
        requested_levels=levels,
        items=items,
        folder_count=len(folders),
        folder_names=sorted(folder_names, key=natural_key),
        errors=errors,
        truncated=truncated,
        scan_time=time.perf_counter() - start,
        filtered=[],
    )
    return _cache


def filter_items(items, search='', parent_filter='', latest_only=False):
    '''Return filtered list of BlendItem (order is kept)'''
    parent_filter = parent_filter.strip().lower()
    if parent_filter:
        ## Exact folder name (case insensitive), wildcards allowed (ex: "anim*")
        ## TODO: could be used at scan time to skip non-matching folders (faster on big trees)
        items = [i for i in items if any(fnmatch(d.lower(), parent_filter) for d in i.rel_dirs)]

    terms = search.lower().split()
    if terms:
        ## All space-separated terms must be found in relative path
        items = [i for i in items if all(t in i.rel.lower() for t in terms)]

    if latest_only:
        ## Keep only last blend (natural sort on stem) of each folder
        latest = {}
        for i in items:
            key = i.path.parent
            if key not in latest or natural_key(i.path.stem) > natural_key(latest[key].path.stem):
                latest[key] = i
        keep = set(id(i) for i in latest.values())
        items = [i for i in items if id(i) in keep]

    return items


## --- Property callbacks (module level: callback "self" only has operator properties)

def update_levels(self, context):
    if bpy.data.filepath:
        scan_same_depth(bpy.data.filepath, self.parent_levels)


def search_folder_names(self, context, edit_text):
    edit_text = edit_text.lower()
    return [n for n in _cache['folder_names'] if edit_text in n.lower()]


class PATH_OT_open_same_depth_blend(Operator):
    bl_idname = "wm.open_same_depth_blend"
    bl_label = 'Open Same Depth Blend'
    bl_description = "List blends at the same depth as current blend in surrounding folders\
        \n(siblings folders, up to chosen number of parent levels)"
    bl_options = {"REGISTER"}

    parent_levels : bpy.props.IntProperty(
        name='Parent Levels',
        description='Number of parent folders to go up from current blend folder\
            \nBlends are then listed at the same depth as current blend (triggers a rescan)\
            \n0 = Only current folder',
        default=1, min=0, soft_max=4, max=10,
        update=update_levels,
    )

    sort_by : bpy.props.EnumProperty(
        name="Sort By",
        items=(
            ('NAME', "Name", "Sort by path (natural sort)", 'SORTALPHA', 0),
            ('DATE', "Date", "Sort by modification date, last saved on top", 'SORTTIME', 1),
        ),
        default='NAME',
    )

    latest_only : bpy.props.BoolProperty(
        name='Latest Only',
        description='Show only the last blend of each folder (natural sort on name)',
        default=False,
    )

    parent_filter : bpy.props.StringProperty(
        name='Parent Folder',
        description='Show only blends having a parent folder with this name (below scanned base folder)\
            \nCase insensitive, wildcards allowed (ex: "anim*")',
        default='',
        search=search_folder_names,
        search_options={'SUGGESTION', 'SORT'},
    )

    search : bpy.props.StringProperty(
        name='Search',
        description='Filter by relative path, case insensitive\
            \nSpace-separated words must all be found',
        default='',
        options={'TEXTEDIT_UPDATE', 'SKIP_SAVE'},
    )

    show_all : bpy.props.BoolProperty(
        name='Show All',
        description=f'Display all listed blends (list is cropped at {MAX_DISPLAY} by default)',
        default=False,
        options={'SKIP_SAVE'},
    )

    @classmethod
    def poll(cls, context):
        return bpy.data.is_saved

    def invoke(self, context, event):
        cache = scan_same_depth(bpy.data.filepath, self.parent_levels)

        ## Adapt popup size to longest relative path (not exact, font is not monospace)
        longest = max((len(i.rel) for i in cache['items']), default=20)
        popup_width = int(longest * 8.0) + 140 # + date and buttons columns
        popup_width = min(max(450, popup_width), 900)
        return context.window_manager.invoke_props_dialog(self, width=popup_width)

    def draw(self, context):
        layout = self.layout
        cache = _cache
        current = Path(bpy.data.filepath)

        ## Rescan if current blend changed (ex: popup re-opened from redo after loading another file)
        if cache['blend'] != bpy.data.filepath:
            scan_same_depth(bpy.data.filepath, self.parent_levels)

        ## -- Settings
        row = layout.row(align=True)
        row.prop(self, 'parent_levels')
        row.operator('wm.same_depth_blend_rescan', text='', icon='FILE_REFRESH').parent_levels = self.parent_levels

        row = layout.row()
        row.prop(self, 'sort_by', expand=True)
        row.prop(self, 'latest_only')

        row = layout.row()
        row.enabled = cache['levels'] > 0 # no sub-folders to filter on current folder only
        row.prop(self, 'parent_filter', text='', icon='FILE_FOLDER', placeholder='Parent Folder Name')

        layout.prop(self, 'search', text='', icon='VIEWZOOM', placeholder='Search')

        ## -- Scan infos
        base = cache['base']
        items = cache['items']
        filtered = filter_items(items, self.search, self.parent_filter, self.latest_only)
        if self.sort_by == 'DATE':
            filtered = sorted(filtered, key=lambda x: x.mtime, reverse=True)
        cache['filtered'] = filtered

        box = layout.box()
        col = box.column(align=True)
        pattern = Path(base, *(['*'] * cache['levels'])).as_posix() + '/'
        info_row = col.row()
        info_row.label(text=pattern, icon='FILE_FOLDER')
        info_row.operator('path.open_browser', text='', icon='FILE_PARENT', emboss=False).filepath = str(base)

        row = col.row()
        sub = row.row()
        sub.active = False
        sub.label(text=f"{len(filtered)} / {len(items)} blends in {cache['folder_count']} folders ({cache['scan_time']:.2f}s)")
        copy_row = row.row()
        copy_row.alignment = 'RIGHT'
        copy_row.enabled = bool(filtered)
        copy_row.operator('wm.same_depth_blend_copy_list', text='Copy List', icon='COPYDOWN')
        copy_row.operator('wm.same_depth_blend_to_nav_list', text='To Navigation List', icon='LONGDISPLAY')

        if cache['levels'] < cache['requested_levels']:
            col.label(text=f"Reached root: only {cache['levels']} parent level(s)", icon='INFO')
        if cache['truncated']:
            col.label(text=f'Too many folders (>{MAX_FOLDERS_PER_LEVEL}), scan stopped. Lower parent levels', icon='ERROR')
        if cache['errors']:
            col.label(text=f"{cache['errors']} access error(s) during scan", icon='ERROR')

        if not filtered:
            layout.label(text='No blend found' if not items else 'No blend matching filters', icon='INFO')
            return

        ## -- Show all / less toggle, above list (popup opens scrolled to top)
        if len(filtered) > MAX_DISPLAY:
            row = layout.row()
            sub = row.row()
            sub.active = False
            if self.show_all:
                sub.label(text=f'Showing all {len(filtered)}')
                row.prop(self, 'show_all', text=f'Show Less ({MAX_DISPLAY})', icon='TRIA_UP', toggle=True)
            else:
                sub.label(text=f'Showing {MAX_DISPLAY} of {len(filtered)}')
                row.prop(self, 'show_all', text=f'Show All ({len(filtered)})', icon='TRIA_DOWN', toggle=True)

        ## -- Blend list (same layout as open side blend)
        main_row = layout.row(align=True)
        blend_col = main_row.column(align=True)
        blend_col.alignment = 'LEFT'

        date_col = main_row.column(align=True)
        date_col.alignment = 'RIGHT'

        option_col = main_row.column(align=True)
        option_col.alignment = 'RIGHT'

        displayed = filtered if self.show_all else filtered[:MAX_DISPLAY]
        for item in displayed:
            path = item.path
            blend_row = blend_col.row()
            blend_row.alignment = 'LEFT'

            if path == current:
                ## Current file, Displayed but disabled (non-clickable)
                blend_row.enabled = False
                blend_row.operator('wm.open_mainfile', text=item.rel, emboss=False).filepath = str(path)
            else:
                op = blend_row.operator('wm.open_mainfile', text=item.rel, emboss=False)
                op.filepath = str(path)
                op.display_file_selector = False # display the warning correctly when file is not saved
                op.load_ui = context.preferences.filepaths.use_load_ui

            date_row = date_col.row()
            date_row.alignment = 'RIGHT'
            date_row.active = False # greyed, secondary info
            date_row.label(text=time.strftime('%Y-%m-%d %H:%M', time.localtime(item.mtime)))

            option_row = option_col.row(align=True)
            option_row.alignment = 'RIGHT'
            option_row.operator('path.open_browser', text='', icon='FILE_FOLDER').filepath = str(path)
            option_row.operator('wm.open_in_new_instance', text='', icon='FILE_BACKUP').filepath = str(path)
            option_row.operator('pathaction.copy_path', text='', icon='COPYDOWN').path = str(path)

        if len(filtered) > MAX_DISPLAY and not self.show_all:
            row = layout.row()
            row.active = False
            row.label(text=f'... {len(filtered) - MAX_DISPLAY} more not displayed', icon='INFO')

    def execute(self, context):
        return {'FINISHED'}


class PATH_OT_same_depth_blend_rescan(Operator):
    bl_idname = "wm.same_depth_blend_rescan"
    bl_label = 'Rescan Same Depth Blends'
    bl_description = "Rescan folders to refresh listed blends"
    bl_options = {"REGISTER", "INTERNAL"}

    parent_levels : bpy.props.IntProperty(default=1, min=0, options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return bpy.data.is_saved

    def execute(self, context):
        cache = scan_same_depth(bpy.data.filepath, self.parent_levels)
        self.report({'INFO'}, f"Found {len(cache['items'])} blends ({cache['scan_time']:.2f}s)")
        return {'FINISHED'}


class PATH_OT_same_depth_blend_copy_list(Operator):
    bl_idname = "wm.same_depth_blend_copy_list"
    bl_label = 'Copy Blend List'
    bl_description = "Copy full paths of filtered blends to clipboard (one per line)"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        filtered = _cache['filtered']
        if not filtered:
            self.report({'WARNING'}, 'No blend to copy')
            return {'CANCELLED'}
        context.window_manager.clipboard = '\n'.join(str(i.path) for i in filtered)
        self.report({'INFO'}, f'Copied {len(filtered)} blend paths')
        return {'FINISHED'}


class PATH_OT_same_depth_blend_to_nav_list(Operator):
    bl_idname = "wm.same_depth_blend_to_nav_list"
    bl_label = 'To Navigation List'
    bl_description = "Set filtered blends (in displayed order) as navigation list\
        \nShow previous / next buttons in topbar to step through those blends\
        \nReplace existing navigation list"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        filtered = _cache['filtered']
        if not filtered:
            self.report({'WARNING'}, 'No blend to set as navigation list')
            return {'CANCELLED'}
        try:
            blend_nav_list.write_nav_list([i.path for i in filtered])
        except OSError as e:
            self.report({'ERROR'}, f'Could not write navigation list: {e}')
            return {'CANCELLED'}
        blend_nav_list.refresh_nav()
        blend_nav_list.tag_topbar_redraw()
        self.report({'INFO'}, f'{len(filtered)} blends set as navigation list')
        return {'FINISHED'}


classes = (
    PATH_OT_open_same_depth_blend,
    PATH_OT_same_depth_blend_rescan,
    PATH_OT_same_depth_blend_copy_list,
    PATH_OT_same_depth_blend_to_nav_list,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    ## Release scan data
    _cache['items'] = []
    _cache['filtered'] = []
