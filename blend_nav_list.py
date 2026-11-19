## Blend navigation list
## A plain text file (one blend path per line) in user config folder
## Exposes previous / next / list buttons in topbar to step through listed blends
## The file can be written from the "Same Depth Blend" popup or by any external tool

import bpy
import os
import time
from pathlib import Path
from bpy.app.handlers import persistent
from bpy.types import Operator

LIST_FILENAME = 'path_actions_nav_list.txt'
## Max number of rows drawn in list popup (window centered on current blend)
MAX_DISPLAY = 100

## Navigation list cache, frozen at each refresh (file load, set, clear, list popup)
## Draw and step only read it: no path comparison, no disk access
## (a "save as" afterwards keeps previous targets until next refresh)
_nav = {
    'files': [], # path strings as written in file
    'display': [], # path relative to common base (popup display)
    'base': '', # common parent folder of listed blends
    'current': -1, # row of current blend at refresh time (popup display only)
    'prev_targets': [], # blends before current, nearest first
    'next_targets': [], # blends after current, nearest first
    'prev_name': '', # stem of nearest previous (topbar label)
    'next_name': '', # stem of nearest next (topbar label)
}


def get_list_path():
    return Path(bpy.utils.user_resource('CONFIG')) / LIST_FILENAME


def path_key(path):
    return os.path.normcase(os.path.normpath(path))


def read_nav_list():
    '''Return list of path strings from navigation list file (empty list if no file)
    Blank lines and lines starting with "#" are ignored, surrounding quotes are stripped'''
    try:
        ## utf-8-sig: strip BOM written by some Windows editors
        with get_list_path().open('r', encoding='utf-8-sig') as fd:
            lines = fd.read().splitlines()
    except (OSError, UnicodeDecodeError):
        return []

    files = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        line = line.strip('"\'').strip()
        if line:
            files.append(line)
    return files


def write_nav_list(paths):
    list_path = get_list_path()
    list_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = list_path.with_name(list_path.name + '.tmp')
    with tmp.open('w', encoding='utf-8') as fd:
        fd.write('\n'.join(str(p) for p in paths) + '\n')
    os.replace(tmp, list_path)


def clear_nav_list():
    try:
        get_list_path().unlink(missing_ok=True)
    except OSError as e:
        print(f'Path Actions: could not delete navigation list: {e}')
        return False
    return True


def refresh_nav():
    '''Read list file and freeze cache (position of current blend and its prev / next targets)'''
    files = read_nav_list()
    base = ''
    if files:
        try:
            base = os.path.commonpath([os.path.dirname(os.path.normpath(f)) for f in files])
        except ValueError: # mixed drives or relative/absolute
            base = ''

    display = []
    for f in files:
        rel = f
        if base:
            try:
                rel = os.path.relpath(os.path.normpath(f), base)
            except ValueError:
                pass
        display.append(Path(rel).as_posix())

    ## Locate current blend once (bpy.data is restricted during addon registration)
    current = -1
    filepath = getattr(bpy.data, 'filepath', '')
    if filepath:
        key = path_key(filepath)
        current = next((i for i, f in enumerate(files) if path_key(f) == key), -1)

    prev_targets = files[:current][::-1] if current >= 0 else []
    next_targets = files[current + 1:] if current >= 0 else []

    _nav.update(
        files=files,
        display=display,
        base=base,
        current=current,
        prev_targets=prev_targets,
        next_targets=next_targets,
        prev_name=Path(prev_targets[0]).stem if prev_targets else '',
        next_name=Path(next_targets[0]).stem if next_targets else '',
    )


def tag_topbar_redraw():
    wm = bpy.context.window_manager
    if not wm:
        return
    for win in wm.windows:
        ## Topbar is a global area (not in screen.areas). "global_areas" may not exist in older versions
        for area in getattr(win, 'global_areas', ()):
            if area.type == 'TOPBAR':
                area.tag_redraw()


def open_blend(context, filepath):
    '''Open blend, showing the "unsaved changes" warning when needed'''
    bpy.ops.wm.open_mainfile('INVOKE_DEFAULT',
                             filepath=filepath,
                             display_file_selector=False,
                             load_ui=context.preferences.filepaths.use_load_ui)


## --- Topbar

def draw_nav_buttons(layout, context):
    if not _nav['files']:
        return
    listed = _nav['current'] >= 0

    row = layout.row(align=True)
    if listed:
        ## Previous: [<][name]
        prev_row = row.row(align=True)
        prev_row.enabled = bool(_nav['prev_name'])
        prev_row.operator('pathaction.nav_step', text='', icon='TRIA_LEFT').direction = -1
        if _nav['prev_name']:
            name_row = prev_row.row(align=True)
            name_row.ui_units_x = 6
            name_row.operator('pathaction.nav_step', text=_nav['prev_name']).direction = -1

    row.operator('pathaction.nav_list_popup', text='', icon='LONGDISPLAY')

    if listed:
        ## Next: [name][>]
        next_row = row.row(align=True)
        next_row.enabled = bool(_nav['next_name'])
        if _nav['next_name']:
            name_row = next_row.row(align=True)
            name_row.ui_units_x = 6
            name_row.operator('pathaction.nav_step', text=_nav['next_name']).direction = 1
        next_row.operator('pathaction.nav_step', text='', icon='TRIA_RIGHT').direction = 1


## --- Operators

class PATHACTION_OT_nav_step(Operator):
    bl_idname = "pathaction.nav_step"
    bl_label = 'Navigation List Step'
    bl_description = "Open previous / next blend of navigation list"
    bl_options = {'INTERNAL'} # no undo push: a file is loaded

    direction : bpy.props.IntProperty(default=1, options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties):
        side = 'previous' if properties.direction < 0 else 'next'
        desc = f'Open {side} blend of navigation list'
        targets = _nav['prev_targets'] if properties.direction < 0 else _nav['next_targets']
        if targets:
            desc += f"\n{targets[0]}"
        desc += '\n(Missing files are skipped)'
        return desc

    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        if _nav['current'] < 0:
            self.report({'ERROR'}, 'Current blend is not in navigation list')
            return {'CANCELLED'}

        targets = _nav['prev_targets'] if self.direction < 0 else _nav['next_targets']
        skipped = []
        target = None
        for path in targets:
            ## Only place where listed paths are checked on disk
            if os.path.isfile(path):
                target = path
                break
            skipped.append(path)

        side = 'before' if self.direction < 0 else 'after'
        if skipped:
            print('Path Actions - navigation list, skipped missing files:\n' + '\n'.join(skipped))
        if target is None:
            msg = f'No existing blend {side} current in navigation list'
            if skipped:
                msg += f' ({len(skipped)} missing)'
            self.report({'WARNING'}, msg)
            return {'CANCELLED'}

        if skipped:
            ## Report before opening (operator data can be freed once file is loaded)
            self.report({'WARNING'}, f'Skipped {len(skipped)} missing file(s), see console')

        open_blend(context, target)
        return {'FINISHED'}


class PATHACTION_OT_nav_list_popup(Operator):
    bl_idname = "pathaction.nav_list_popup"
    bl_label = 'Navigation List'
    bl_description = "Show blends of navigation list\
        \nList file can be generated from 'Same Depth Blend' popup or edited manually (one path per line)"
    bl_options = {'REGISTER'}

    def invoke(self, context, event):
        ## Re-read: list file may have been edited externally
        refresh_nav()
        tag_topbar_redraw()

        ## Dates (single stat per file, only when popup opens)
        self.mtimes = {}
        for f in _nav['files']:
            try:
                self.mtimes[f] = os.stat(f).st_mtime
            except OSError:
                pass

        longest = max((len(d) for d in _nav['display']), default=30)
        popup_width = int(longest * 8.0) + 140
        popup_width = min(max(450, popup_width), 900)
        return context.window_manager.invoke_props_dialog(self, width=popup_width)

    def draw(self, context):
        layout = self.layout
        files = _nav['files']
        idx = _nav['current']

        box = layout.box()
        col = box.column(align=True)
        row = col.row()
        row.label(text=_nav['base'] + '/' if _nav['base'] else 'Navigation list', icon='FILE_FOLDER')
        row.operator('path.open_browser', text='', icon='TEXT', emboss=False).filepath = str(get_list_path())

        row = col.row()
        sub = row.row()
        sub.active = False
        position = f' (current: {idx + 1})' if idx >= 0 else ' (current blend not listed)'
        sub.label(text=f'{len(files)} blends{position}' if files else 'Empty list')
        btn_row = row.row(align=True)
        btn_row.alignment = 'RIGHT'
        btn_row.enabled = bool(files)
        btn_row.operator('pathaction.nav_list_copy', text='Copy List', icon='COPYDOWN')
        btn_row.operator('pathaction.nav_list_clear', text='Clear List', icon='TRASH')

        if not files:
            layout.label(text='No navigation list (cleared or empty)', icon='INFO')
            return

        ## Display a window around current blend when list is long
        start = 0
        if len(files) > MAX_DISPLAY and idx >= 0:
            start = min(max(0, idx - MAX_DISPLAY // 2), len(files) - MAX_DISPLAY)
        end = min(len(files), start + MAX_DISPLAY)

        if start:
            row = layout.row()
            row.active = False
            row.label(text=f'... {start} more above', icon='INFO')

        main_row = layout.row(align=True)
        blend_col = main_row.column(align=True)
        blend_col.alignment = 'LEFT'

        date_col = main_row.column(align=True)
        date_col.alignment = 'RIGHT'

        option_col = main_row.column(align=True)
        option_col.alignment = 'RIGHT'

        mtimes = getattr(self, 'mtimes', {})
        for i in range(start, end):
            path = files[i]
            blend_row = blend_col.row()
            blend_row.alignment = 'LEFT'
            if i == idx:
                ## Current file, Displayed but disabled (non-clickable)
                blend_row.enabled = False
                blend_row.operator('wm.open_mainfile', text=_nav['display'][i], emboss=False).filepath = path
            else:
                op = blend_row.operator('wm.open_mainfile', text=_nav['display'][i], emboss=False)
                op.filepath = path
                op.display_file_selector = False
                op.load_ui = context.preferences.filepaths.use_load_ui

            date_row = date_col.row()
            date_row.alignment = 'RIGHT'
            date_row.active = False
            mtime = mtimes.get(path)
            date_row.label(text=time.strftime('%Y-%m-%d %H:%M', time.localtime(mtime)) if mtime is not None else '')

            option_row = option_col.row(align=True)
            option_row.alignment = 'RIGHT'
            option_row.operator('path.open_browser', text='', icon='FILE_FOLDER').filepath = path
            option_row.operator('wm.open_in_new_instance', text='', icon='FILE_BACKUP').filepath = path
            option_row.operator('pathaction.copy_path', text='', icon='COPYDOWN').path = path

        if end < len(files):
            row = layout.row()
            row.active = False
            row.label(text=f'... {len(files) - end} more below', icon='INFO')

    def execute(self, context):
        return {'FINISHED'}


class PATHACTION_OT_nav_list_copy(Operator):
    bl_idname = "pathaction.nav_list_copy"
    bl_label = 'Copy Navigation List'
    bl_description = "Copy paths of navigation list to clipboard (one per line)"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        if not _nav['files']:
            self.report({'WARNING'}, 'Navigation list is empty')
            return {'CANCELLED'}
        context.window_manager.clipboard = '\n'.join(_nav['files'])
        self.report({'INFO'}, f"Copied {len(_nav['files'])} blend paths")
        return {'FINISHED'}


class PATHACTION_OT_nav_list_clear(Operator):
    bl_idname = "pathaction.nav_list_clear"
    bl_label = 'Clear Navigation List'
    bl_description = "Delete navigation list (hide navigation buttons in topbar)"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        if not clear_nav_list():
            self.report({'ERROR'}, f'Could not delete: {get_list_path()}')
            return {'CANCELLED'}
        refresh_nav()
        tag_topbar_redraw()
        self.report({'INFO'}, 'Navigation list cleared')
        return {'FINISHED'}


## --- Handlers

@persistent
def nav_load_post(*args):
    ## Re-read file: may have been changed externally or by another instance
    refresh_nav()

## Deferred first refresh (disabled): bpy.data is restricted during registration so current blend is unknown,
## when addon is enabled with a file already open, prev/next appear only after next file load
# def initial_refresh():
#     refresh_nav()
#     tag_topbar_redraw()
#     return None


classes = (
    PATHACTION_OT_nav_step,
    PATHACTION_OT_nav_list_popup,
    PATHACTION_OT_nav_list_copy,
    PATHACTION_OT_nav_list_clear,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.app.handlers.load_post.append(nav_load_post)
    ## Read list now (current blend is unknown here: only list button shows until next file load)
    refresh_nav()
    # bpy.app.timers.register(initial_refresh, first_interval=0.1)

def unregister():
    # if bpy.app.timers.is_registered(initial_refresh):
    #     bpy.app.timers.unregister(initial_refresh)
    if nav_load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(nav_load_post)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
