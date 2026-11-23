import bpy
import os
import re
from pathlib import Path
from bpy.types import Operator, Panel, PropertyGroup

## Optional todo: Add a label displaying the number of users of a link (with an added shield icon if there is a fake user)

def get_file_icon(filepath):
    """Return an appropriate icon based on file extension"""
    if not filepath:
        return 'LIBRARY_DATA_BROKEN'
    
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.blend':
        return 'FILE_BLEND'
    elif ext in bpy.path.extensions_image:
        return 'FILE_IMAGE'
    elif ext in bpy.path.extensions_movie:
        return 'FILE_MOVIE'
    elif ext in bpy.path.extensions_audio:
        return 'FILE_SOUND'
    elif ext == '.py':
        return 'FILE_SCRIPT'
    elif ext == '.txt':
        return 'FILE_TEXT'
    elif os.path.isdir(bpy.path.abspath(filepath)):
        return 'FILE_FOLDER'
        
    # Default icon for linked data
    return 'LIBRARY_DATA_DIRECT'

def get_latest_version(filepath):
    """Find the latest version of a file in the same directory based on naming pattern"""
    try:
        # Get file info
        path_obj = Path(bpy.path.abspath(filepath))
        if not path_obj.exists():
            return None
        
        # TODO: make version check a customizable pattern ?
        
        # Find base name pattern (remove version numbers)
        stem = path_obj.stem
        # Match patterns like name_v001, name.001, name-001, etc.
        base_pattern = re.sub(r'[_.-]v?\d+$', '', stem)
        
        # If no version pattern found, return None
        if base_pattern == stem:
            return None
            
        # Look for other files with same base pattern
        versions = []
        # old direct filter: for file in path_obj.parent.glob(f"{base_pattern}*{path_obj.suffix}")
        for file in path_obj.parent.iterdir():
            # Iterate rather than using glob (pattern may contain glob special characters)
            if not file.is_file() or file.suffix != path_obj.suffix or not file.stem.startswith(base_pattern):
                continue
            # Match version number at the end of the filename
            match = re.search(r'[_.-]v?(\d+)$', file.stem)
            if match:
                versions.append((int(match.group(1)), file))
                
        if not versions:
            return None
            
        # Sort by version number and get the highest
        versions.sort(key=lambda x: x[0], reverse=True)
        if versions[0][1] != path_obj:
            # return str(versions[0][1]) # file has been converted to abspath, here we want to keep current formatting
            ## Return dir path with updated file name
            return ''.join(re.split(r'([\\/])', filepath)[:-1]) + versions[0][1].name
    except Exception:
        pass
    
    return None

def get_packed_filepaths():
    """Return the set of filepaths whose data is packed into the blend"""
    packed = set()
    # Check in various data collections
    for datablock_type in ['images', 'sounds', 'movieclips', 'fonts', 'texts']:
        collection = getattr(bpy.data, datablock_type, None)
        if collection is None:
            continue
        for item in collection:
            if getattr(item, 'packed_file', None) and getattr(item, 'filepath', None):
                packed.add(item.filepath)
    return packed

## Tile tokens used by tiled images, mapped to the regex of what they stand for
TILE_TOKENS = {
    '<UDIM>': r'\d{4}',
    '<UVTILE>': r'u\d+_v\d+',
}

def tiled_path_exists(filepath):
    """For a path containing a tile token (ex: 'tex.<UDIM>.png'), return True if at least one tile exists"""
    path_obj = Path(filepath)
    pattern = re.escape(path_obj.name)
    for token, token_pattern in TILE_TOKENS.items():
        pattern = pattern.replace(re.escape(token), token_pattern)
    try:
        return any(re.fullmatch(pattern, f.name) for f in path_obj.parent.iterdir() if f.is_file())
    except OSError:
        return False

def link_exists(filepath):
    """Check if a resolved absolute path exists, handling tiled images tokens"""
    if any(token in filepath for token in TILE_TOKENS):
        return tiled_path_exists(filepath)
    return Path(filepath).exists()

def is_bundled_path(filepath):
    """Return True if the resolved absolute path is inside Blender's install (ex: bundled essentials assets)"""
    local_root = os.path.normcase(os.path.abspath(bpy.utils.resource_path('LOCAL')))
    return os.path.normcase(os.path.abspath(filepath)).startswith(local_root + os.sep)

def check_links(context):
    """Check external file links and populate the path_list collection"""
    wm = context.window_manager

    wm.pa_path_list_extended.clear()
    
    # Get all paths
    viewed = set()
    packed_filepaths = get_packed_filepaths()
    wm.pa_links_stats.broken_count = 0
    wm.pa_links_stats.absolute_count = 0
    wm.pa_links_stats.relative_count = 0
    wm.pa_links_stats.bundled_count = 0

    for current, lib in zip(bpy.utils.blend_paths(local=True), bpy.utils.blend_paths(absolute=True, local=True)):
        # Avoid relisting same path multiple times
        if current in viewed:
            continue
        viewed.add(current)

        try:
            lfp = Path(lib)  # absolute path

            item = wm.pa_path_list_extended.add()
            item.path = current
            item.is_checked = True

            # Check if it's a blend file
            item.is_blend = current.lower().endswith('.blend')

            # Check if data is packed
            item.is_packed = current in packed_filepaths
            
            # Check if path exists (skip if packed)
            if item.is_packed:
                item.is_valid = True
                if current.startswith('//'):
                    wm.pa_links_stats.relative_count += 1
                    item.is_relative = True
                else:
                    wm.pa_links_stats.absolute_count += 1
                    item.is_relative = False
            elif not link_exists(lib):
                item.is_valid = False
                wm.pa_links_stats.broken_count += 1
                
                # Try to find a valid parent path
                for i in range(len(lfp.parts) - 2):
                    parent = lfp.parents[i]
                    if parent.exists():
                        item.valid_parent_path = str(parent)
                        break
            else:
                item.is_valid = True
                if is_bundled_path(lib):
                    ## Shipped with Blender (ex: essentials brushes), not a user link
                    ## Checked first: Blender may store it relative to the blend (//../../app/datafiles/...)
                    wm.pa_links_stats.bundled_count += 1
                    item.is_bundled = True
                elif current.startswith('//'):
                    wm.pa_links_stats.relative_count += 1
                    item.is_relative = True
                else:
                    wm.pa_links_stats.absolute_count += 1
                    item.is_relative = False

        except Exception as e:
            print(f'Links checker, error checking "{current}": {e}')
            item = wm.pa_path_list_extended.add()
            item.path = f'Error checking: {current}'
            item.is_checked = True
            item.is_valid = False
            item.is_error_message = True
            wm.pa_links_stats.broken_count += 1
    
    # Return the statistics for convenience
    return {
        'broken_count': wm.pa_links_stats.broken_count, 
        'absolute_count': wm.pa_links_stats.absolute_count, 
        'relative_count': wm.pa_links_stats.relative_count,
        'bundled_count': wm.pa_links_stats.bundled_count,
    }

# User count functionality removed as requested

class PATHACTION_OT_update_file_path(Operator):
    bl_idname = "pathaction.update_file_path"
    bl_label = "Update File Path"
    bl_description = "Update this file path to the specified target path"
    bl_options = {"REGISTER", "INTERNAL", "UNDO"}
    
    source_path: bpy.props.StringProperty(options={'SKIP_SAVE'})
    target_path: bpy.props.StringProperty(options={'SKIP_SAVE'})

    error : bpy.props.BoolProperty(name="Error", default=False, options={'SKIP_SAVE'})
    refresh : bpy.props.BoolProperty(name="Refresh", default=True, options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties):
        return f"source: {properties.source_path}\
            \ntarget: {properties.target_path}"

    def invoke(self, context, event):
        target_file = Path(bpy.path.abspath(self.target_path))
        if target_file.exists():
            return self.execute(context)
        
        self.error = True
        self.parent_dir = ''

        if target_file.parent.exists():
            self.parent_dir = str(target_file.parent)
        return context.window_manager.invoke_props_dialog(self, width=600)

    def draw(self, context):
        layout = self.layout
        layout.label(text=f"Not found: {self.target_path}")
        layout.label(text="Library was not replaced")
        layout.separator()

        layout.label(text="You may want to open folder to inspect", icon='INFO')
        layout.operator("path.open_browser", text=f"Open Folder", icon='FILE_FOLDER').filepath = self.parent_dir

    def execute(self, context):
        if self.error:
            return {'CANCELLED'}

        if not self.source_path or not self.target_path:
            self.report({'ERROR'}, "Source or target path is missing")
            return {'CANCELLED'}
            
        # Update path in appropriate datablocks
        updated = 0
        ## For any datablock type
        # for datablock_type in ['images', 'sounds', 'movies', 'fonts', 'texts', 'libraries']:
        #     if hasattr(bpy.data, datablock_type):
        #         collection = getattr(bpy.data, datablock_type)
        #         for item in collection:
        #             if hasattr(item, 'filepath') and item.filepath == self.source_path:
        #                 item.filepath = self.target_path
        #                 updated += 1

        ## Only for blend libraries
        for item in bpy.data.libraries:
            if hasattr(item, 'filepath') and item.filepath == self.source_path:
                item.filepath = self.target_path
                ## update name if it corresponds to the source path basname
                if re.split(r'([\\/])', self.source_path)[-1] == item.name:
                    new_lib_name = re.split(r'([\\/])', self.target_path)[-1]
                    print('Update library name:', item.name, '->', new_lib_name)
                    item.name = new_lib_name
                updated += 1
        
        if updated and self.refresh:
            self.report({'INFO'}, f"Updated {updated} references")
            # Refresh links checker data
            check_links(context)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No references found to update")
            return {'CANCELLED'}

class PATHACTION_OT_edit_file_path(Operator):
    bl_idname = "pathaction.edit_file_path"
    bl_label = "Edit File Path"
    bl_description = "Edit the file path directly"
    bl_options = {"REGISTER", "INTERNAL", "UNDO"}
    
    source_path: bpy.props.StringProperty(options={'SKIP_SAVE'})
    new_path: bpy.props.StringProperty(name="New Path", description="Enter the new file path")
    
    def invoke(self, context, event):
        self.new_path = self.source_path
        # Approximate width based on characters (this is a rough estimate)
        char_width = 7  # pixels per character
        popup_width = min(max(450, int(len(self.source_path) * char_width + 40)), 1200)
        return context.window_manager.invoke_props_dialog(self, width=popup_width)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "new_path", text="")
        layout.label(text="Note: Save and reopen blend file after applying changes", icon='INFO')
        layout.label(text="It is recommended to increment or backup file before editing library path", icon='INFO')
    
    def execute(self, context):
        if not self.source_path:
            self.report({'ERROR'}, "Source path is missing")
            return {'CANCELLED'}
            
        if self.source_path == self.new_path:
            self.report({'INFO'}, "Path unchanged")
            return {'CANCELLED'}
            
        return bpy.ops.pathaction.update_file_path('INVOKE_DEFAULT', source_path=self.source_path, target_path=self.new_path)

class PATHACTION_OT_replace_file_library(Operator):
    bl_idname = "pathaction.replace_file_library"
    bl_label = "Replace File Library"
    bl_description = "Browse for a file to replace current library path"
    bl_options = {"REGISTER", "INTERNAL", "UNDO"}
    
    options = {'SKIP_SAVE', 'PATH_SUPPORTS_BLEND_RELATIVE'} if bpy.app.version >= (4, 5, 0) else {'SKIP_SAVE'}
    source_path: bpy.props.StringProperty(options=options)
    filepath: bpy.props.StringProperty(subtype='FILE_PATH', options=options)
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text="Select a file to replace current:")
        col.label(text=self.source_path)
        layout.separator()
 
        col = layout.column()
        col.label(text="Important infos:", icon='INFO')
        col.label(text='This is NOT equivalent to "Relocate"')
        col.label(text='(Relocate apply changes immediately)')
        col.label(text="To apply changes: Save and Reopen")
        col.separator()
        col.label(text="Use at your own risk", icon='INFO')
        col.label(text="Recommended to Backup/increment first")

    def execute(self, context):
        if not self.source_path or not self.filepath:
            self.report({'ERROR'}, "Source or target path is missing")
            return {'CANCELLED'}
            
        # Make path relative if appropriate
        if self.source_path.startswith('//') and bpy.data.is_saved:
            try:
                self.filepath = bpy.path.relpath(self.filepath)
            except ValueError:
                # Cannot be made relative (ex: different drive), keep absolute
                pass
                
        return bpy.ops.pathaction.update_file_path(source_path=self.source_path, target_path=self.filepath)

def get_library_ids(library_path, id_type='', id_name=''):
    """Return datablocks linked from the library, optionally filtered by type name (ex: 'Mesh') and datablock name"""
    return [i for lib in bpy.data.libraries if lib.filepath == library_path for i in lib.users_id
            if (not id_type or type(i).__name__ == id_type) and (not id_name or i.name == id_name)]

def get_related_objects(ids, user_map=None):
    """Return objects related to passed datablocks
    (themselves if objects, overrides and local objects using them, ex: linked material > local mesh > object)"""
    objects = {i for i in ids if isinstance(i, bpy.types.Object)}
    if user_map is None:
        user_map = bpy.data.user_map()

    ## Go up the users chain, stop at objects (containers like collections and scenes are skipped)
    viewed = set(ids)
    to_check = list(ids)
    while to_check:
        for user in user_map.get(to_check.pop(), ()):
            if user in viewed:
                continue
            viewed.add(user)
            if isinstance(user, bpy.types.Object):
                objects.add(user)
            elif not isinstance(user, (bpy.types.Collection, bpy.types.Scene)):
                to_check.append(user)
    return objects

def get_library_users(library_path, id_type='', id_name=''):
    """Return datablocks linked from the library and the objects related to them"""
    linked_ids = get_library_ids(library_path, id_type, id_name)
    return linked_ids, get_related_objects(linked_ids)

def get_id_icon(id):
    """Return the icon of the datablock type (ex: 'MESH_DATA' for a mesh)"""
    try:
        return bpy.types.ID.bl_rna.properties['id_type'].enum_items[id.id_type].icon
    except (KeyError, AttributeError):
        return 'BLANK1'

class PATHACTION_OT_select_library_users(Operator):
    bl_idname = "pathaction.select_library_users"
    bl_label = "Select Library Users"
    bl_description = "List datablocks linked from this library\
        \nand select related objects in viewport (linked, overrides or using linked data)\
        \n\
        \nShift: Extend selection (keep previous selection)\
        \nCtrl: Do not show the infos popup"
    bl_options = {"REGISTER", "INTERNAL", "UNDO"}

    library_path: bpy.props.StringProperty(options={'SKIP_SAVE'})
    ## Optional filters (used from details popups). When filtered, only a report is done (no infos popup)
    id_type: bpy.props.StringProperty(options={'SKIP_SAVE'})
    id_name: bpy.props.StringProperty(options={'SKIP_SAVE'})
    extend: bpy.props.BoolProperty(name="Extend", default=False, options={'SKIP_SAVE'})
    show_popup: bpy.props.BoolProperty(name="Show Popup", default=True, options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties):
        if properties.id_name:
            return f"Select objects related to {properties.id_type} '{properties.id_name}'\
                \nShift: Extend selection (keep previous selection)"
        if properties.id_type:
            return f"Select objects related to all {properties.id_type} datablocks linked from this library\
                \nShift: Extend selection (keep previous selection)"
        return cls.bl_description

    def invoke(self, context, event):
        self.extend = event.shift
        self.show_popup = not event.ctrl
        return self.execute(context)

    def execute(self, context):
        linked_ids, objects = get_library_users(self.library_path, self.id_type, self.id_name)
        if not linked_ids:
            self.report({'WARNING'}, f"No datablock linked from: {self.library_path}")
            return {'CANCELLED'}

        ## Select related objects (only possible if in current view layer and selectable)
        view_layer_objects = set(context.view_layer.objects)
        if not self.extend:
            for ob in context.view_layer.objects:
                ob.select_set(False)
        for ob in objects:
            if ob in view_layer_objects:
                ob.select_set(True)
        selected = [ob for ob in objects if ob in view_layer_objects and ob.select_get()]
        active = context.view_layer.objects.active
        ## In extend mode, keep active if it is part of the previous selection
        keep_active = active in selected or (self.extend and active and active.select_get())
        if selected and not keep_active:
            context.view_layer.objects.active = selected[0]

        select_line = f"{len(selected)} related objects selected"
        if len(selected) < len(objects):
            select_line += f" ({len(objects) - len(selected)} hidden or not in view layer)"

        ## Filtered call (from details popup): only report
        if self.id_type or self.id_name:
            target = f"{self.id_type} '{self.id_name}'" if self.id_name else f"{len(linked_ids)} {self.id_type}"
            self.report({'INFO'}, f"{target}: {select_line}")
            return {'FINISHED'}

        print(f"\nLibrary: {self.library_path}")
        for type_name, header, names in get_type_summary(linked_ids):
            print(f"{header}: {', '.join(names)}")
        print(select_line)

        ## Popup crashes blender without a window (background mode)
        if self.show_popup and not bpy.app.background and context.window:
            bpy.ops.pathaction.library_infos('INVOKE_DEFAULT', library_path=self.library_path, select_line=select_line)
        self.report({'INFO'}, f"{len(linked_ids)} linked datablocks, {select_line}")
        return {'FINISHED'}

def get_type_summary(linked_ids):
    """Return a list of (type_name, header, sorted_names) for linked datablocks, sorted by type
    header contains count of datablocks, unused and kept only by fake user (ex: 'Mesh (3, 1 unused)')"""
    by_type = {}
    for i in linked_ids:
        by_type.setdefault(type(i).__name__, []).append(i)
    summary = []
    for type_name, ids in sorted(by_type.items()):
        count = f"{len(ids)}"
        if unused := sum(1 for i in ids if i.users == 0):
            count += f", {unused} unused"
        if fake_only := sum(1 for i in ids if i.users == 1 and i.use_fake_user):
            count += f", {fake_only} fake user only"
        summary.append((type_name, f"{type_name} ({count})", sorted(i.name for i in ids)))
    return summary

def text_width(text):
    """Approximate width of a UI label text at UI scale 1 (popup widths are scaled by Blender)"""
    import blf
    blf.size(0, 11)
    return blf.dimensions(0, text)[0]

## Popups use invoke_popup (regular layout): popup_menu uses a menu layout
## where icon buttons and multiple columns overlap.

class PATHACTION_OT_library_infos(Operator):
    bl_idname = "pathaction.library_infos"
    bl_label = "Linked Library Infos"
    bl_description = "Show datablocks linked from this library, by type"
    bl_options = {"INTERNAL"}

    library_path: bpy.props.StringProperty(options={'SKIP_SAVE'})
    select_line: bpy.props.StringProperty(options={'SKIP_SAVE'})

    max_names = 8

    def invoke(self, context, event):
        linked_ids = get_library_ids(self.library_path)
        if not linked_ids:
            self.report({'WARNING'}, f"No datablock linked from: {self.library_path}")
            return {'CANCELLED'}

        ## Store plain data only (no ID references kept while popup is open)
        self.rows = []
        for type_name, header, names in get_type_summary(linked_ids):
            ## Limit displayed names (full list is printed in console and in details popup)
            text = ', '.join(names[:self.max_names])
            if len(names) > self.max_names:
                text += ', ...'
            self.rows.append((type_name, f"{header}: {text}"))

        self.title = f"Linked from {bpy.path.basename(self.library_path)}"
        width = max(text_width(t) for t in [self.title, self.select_line] + [r[1] for r in self.rows])
        return context.window_manager.invoke_popup(self, width=int(min(width + 60, 1200)))

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.label(text=self.title, icon='LIBRARY_DATA_DIRECT')
        layout.separator()

        for type_name, text in self.rows:
            row = layout.row()
            row.alignment = 'LEFT'
            buttons = row.row(align=True)
            props = buttons.operator('pathaction.library_type_details', text='', icon='PRESET')
            props.library_path = self.library_path
            props.id_type = type_name
            props = buttons.operator('pathaction.select_library_users', text='', icon='RESTRICT_SELECT_OFF')
            props.library_path = self.library_path
            props.id_type = type_name
            row.label(text=text)

        if self.select_line:
            layout.separator()
            layout.label(text=self.select_line, icon='INFO')

    def execute(self, context):
        return {'FINISHED'}

class PATHACTION_OT_library_type_details(Operator):
    bl_idname = "pathaction.library_type_details"
    bl_label = "Linked Datablocks Details"
    bl_description = "Show details of linked datablocks of this type\
        \n(users, fake user, overrides, related objects)\
        \nwith per-datablock actions"
    bl_options = {"INTERNAL"}

    library_path: bpy.props.StringProperty(options={'SKIP_SAVE'})
    id_type: bpy.props.StringProperty(options={'SKIP_SAVE'})

    max_rows = 40

    def invoke(self, context, event):
        linked_ids = sorted(get_library_ids(self.library_path, self.id_type), key=lambda i: i.name)
        if not linked_ids:
            self.report({'WARNING'}, f"No {self.id_type} linked from: {self.library_path}")
            return {'CANCELLED'}

        user_map = bpy.data.user_map()
        ## Linked datablocks that have local overrides (user_map keys contain all datablocks)
        overridden = {k.override_library.reference for k in user_map
                      if k.override_library and k.override_library.reference}
        view_layer = context.view_layer
        view_layer_objects = set(view_layer.objects)

        ## Store plain data only (no ID references kept while popup is open)
        rows = self.rows = []
        for i in linked_ids:
            related = get_related_objects([i], user_map)
            in_layer = [ob for ob in related if ob in view_layer_objects]
            selectable = [ob for ob in in_layer if ob.visible_get(view_layer=view_layer) and not ob.hide_select]
            if i.is_missing:
                link_icon = 'LIBRARY_DATA_BROKEN'
            elif i.is_library_indirect:
                link_icon = 'LIBRARY_DATA_INDIRECT'
            else:
                link_icon = 'LIBRARY_DATA_DIRECT'
            rows.append({
                'name': i.name,
                'icon': get_id_icon(i),
                'users': i.users,
                'fake_user': i.use_fake_user,
                'overridden': i in overridden,
                'link_icon': link_icon,
                'related': len(related),
                'selectable': len(selectable),
            })

        print(f"\n{self.id_type} linked from: {self.library_path}")
        for r in rows:
            flags = [f for f, ok in (('fake user', r['fake_user']), ('overridden', r['overridden']),
                                      ('missing', r['link_icon'] == 'LIBRARY_DATA_BROKEN'),
                                      ('indirect', r['link_icon'] == 'LIBRARY_DATA_INDIRECT')) if ok]
            flags = f" [{', '.join(flags)}]" if flags else ''
            print(f"  {r['name']}: {r['users']} users, {r['related']} related objects ({r['selectable']} selectable){flags}")

        for r in rows:
            r['related_text'] = f"{r['related']} related objects"
            if r['selectable'] < r['related']:
                r['related_text'] += f" ({r['related'] - r['selectable']} not selectable)"

        ## Fixed column widths in UI units (20px at UI scale 1, scaled by Blender) keep rows aligned
        shown = rows[:self.max_rows]
        unit = 20
        self.col_units = (
            1, # select button
            max(text_width(r['name']) for r in shown) / unit + 1.6, # icon + name
            max(text_width(f"{r['users']} users") for r in shown) / unit + 1.6, # icon + users
            3.2, # 3 icon slots
            max(text_width(r['related_text']) for r in shown) / unit + 0.8,
        )
        self.title = f"{self.id_type} linked from {bpy.path.basename(self.library_path)}"
        width = max(sum(self.col_units) * unit, text_width(self.title) + 40)
        return context.window_manager.invoke_popup(self, width=int(min(width + 20, 1400)))

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.label(text=self.title, icon='LIBRARY_DATA_DIRECT')

        props = layout.operator('pathaction.select_library_users',
                                text=f"Select Objects Related To All {self.id_type} ({len(self.rows)})",
                                icon='RESTRICT_SELECT_OFF')
        props.library_path = self.library_path
        props.id_type = self.id_type
        layout.separator()

        row = layout.row()
        row.alignment = 'LEFT'
        cols = [row.column() for _ in self.col_units]
        for col, units in zip(cols, self.col_units):
            col.ui_units_x = units
        col_select, col_name, col_users, col_flags, col_related = cols

        for r in self.rows[:self.max_rows]:
            sub = col_select.row()
            sub.enabled = r['selectable'] > 0
            props = sub.operator('pathaction.select_library_users', text='', icon='RESTRICT_SELECT_OFF')
            props.library_path = self.library_path
            props.id_type = self.id_type
            props.id_name = r['name']

            col_name.label(text=r['name'], icon=r['icon'])

            col_users.label(text=f"{r['users']} users", icon='ERROR' if r['users'] == 0 else 'BLANK1')

            ## Fixed icon slots: link status, fake user, override
            flags = col_flags.row(align=True)
            flags.label(text='', icon=r['link_icon'])
            flags.label(text='', icon='FAKE_USER_ON' if r['fake_user'] else 'BLANK1')
            flags.label(text='', icon='LIBRARY_DATA_OVERRIDE' if r['overridden'] else 'BLANK1')

            col_related.label(text=r['related_text'])

        if len(self.rows) > self.max_rows:
            layout.label(text=f"... {len(self.rows) - self.max_rows} more (full list printed in console)", icon='INFO')

    def execute(self, context):
        return {'FINISHED'}

class PATHACTION_OT_check_latest_versions(Operator):
    bl_idname = "pathaction.check_latest_versions"
    bl_label = "Check Latest Versions"
    bl_description = "Check for newer versions of files in their directories"
    bl_options = {"REGISTER", "INTERNAL"}
    
    def execute(self, context):
        wm = context.window_manager
        updates_found = 0
        
        for item in wm.pa_path_list_extended:
            if not item.is_error_message:
                latest = get_latest_version(item.path)
                if latest:
                    item.latest_version = latest
                    updates_found += 1
        
        if updates_found:
            self.report({'INFO'}, f"Found {updates_found} update(s)")
        else:
            self.report({'INFO'}, "No updates found")
            
        return {'FINISHED'}

class PATHACTION_OT_update_to_latest_versions(Operator):
    bl_idname = "pathaction.update_to_latest_versions"
    bl_label = "Update All To Latest"
    bl_description = "Update all files to their latest versions"
    bl_options = {"REGISTER", "INTERNAL", "UNDO"}
    
    def execute(self, context):
        wm = context.window_manager
        updates_applied = 0
        
        for item in wm.pa_path_list_extended:
            if not item.is_error_message and item.latest_version:
                ## Do not refresh after each update
                bpy.ops.pathaction.update_file_path(source_path=item.path, target_path=item.latest_version, refresh=False)
                updates_applied += 1
        
        if updates_applied:
            self.report({'INFO'}, f"Applied {updates_applied} update(s)")
            check_links(context)  # Refresh the link data
        else:
            self.report({'INFO'}, "No updates to apply")
            
        return {'FINISHED'}

class PATHACTION_PG_path_list_extended(PropertyGroup):
    path: bpy.props.StringProperty() # options={'PATH_SUPPORTS_BLEND_RELATIVE'}
    is_checked: bpy.props.BoolProperty(default=False)
    is_valid: bpy.props.BoolProperty(default=False)
    is_error_message: bpy.props.BoolProperty(default=False)
    valid_parent_path: bpy.props.StringProperty()
    is_relative: bpy.props.BoolProperty(default=False)
    latest_version: bpy.props.StringProperty(default="")
    is_packed: bpy.props.BoolProperty(default=False)
    is_blend: bpy.props.BoolProperty(default=False)
    is_bundled: bpy.props.BoolProperty(default=False) # Inside Blender install (ex: essentials assets)

class PATHACTION_PG_links_stats(PropertyGroup):
    broken_count: bpy.props.IntProperty(default=0)
    absolute_count: bpy.props.IntProperty(default=0)
    relative_count: bpy.props.IntProperty(default=0)
    bundled_count: bpy.props.IntProperty(default=0)

class PATHACTION_OT_links_checker(Operator):
    bl_idname = "pathaction.links_checker"
    bl_label = "File Links Checker"
    bl_description = "Check states of external links in blend file"
    bl_options = {"REGISTER"}
    
    search_field: bpy.props.StringProperty(
        name='Search Filter', default='',
        description='Filter by name, case insensitive',
        options={'TEXTEDIT_UPDATE'}
    )
    
    sort_by: bpy.props.EnumProperty(
        name="Sort By",
        description="Sort the list by this criteria",
        items=[
            ('NAME', "Name", "Sort by filename"),
            ('PATH', "Path", "Sort by full path"),
            ('TYPE', "Type", "Sort by file type"),
            ('STATUS', "Status", "Sort by link status (broken first)")
        ],
        default='STATUS'
    )
    
    reverse_sort: bpy.props.BoolProperty(
        name="Reverse Sort",
        description="Reverse the sort order",
        default=False
    )

    show_bundled: bpy.props.BoolProperty(
        name="Show Bundled",
        description="Show paths shipped with Blender install (ex: essentials assets)",
        default=False
    )

    def invoke(self, context, event):
        # Call the external check_links function
        check_links(context)
        
        # Calculate popup width based on longest path
        self.popup_width = 800  # default
        
        try:
            wm = context.window_manager
            paths = [item.path for item in wm.pa_path_list_extended if not item.is_error_message]
            if paths:
                max_length = max(len(path) for path in paths)
                # Approximate width based on characters (this is a rough estimate)
                char_width = 7  # pixels per character
                button_width = 140  # space for buttons
                self.popup_width = min(max(450, int(max_length * char_width + button_width)), 1200)
        except Exception:
            pass
            
        return context.window_manager.invoke_props_dialog(self, width=self.popup_width)
    
    def sort_items(self, items):
        """Sort items based on current sort settings"""
        if self.sort_by == 'NAME':
            sorted_items = sorted(items, key=lambda x: Path(x.path).name.lower(), reverse=self.reverse_sort)
        elif self.sort_by == 'PATH':
            sorted_items = sorted(items, key=lambda x: x.path.lower(), reverse=self.reverse_sort)
        elif self.sort_by == 'TYPE':
            sorted_items = sorted(items, key=lambda x: os.path.splitext(x.path)[1].lower(), reverse=self.reverse_sort)
        else:  # 'STATUS'
            # Status priority: broken, packed, blend with update, relative, absolute, bundled
            def status_key(x):
                if not x.is_valid:
                    return 0  # Broken first
                elif x.is_packed:
                    return 1  # Then packed
                elif x.is_blend and x.latest_version:
                    return 2  # Then blend with updates
                elif x.is_relative:
                    return 3  # Then relative
                elif x.is_bundled:
                    return 5  # Bundled with Blender last
                else:
                    return 4  # Then absolute
            
            sorted_items = sorted(items, key=lambda x: (status_key(x), x.path.lower()), reverse=self.reverse_sort)
            
        return sorted_items
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        
        if not hasattr(wm, "pa_path_list_extended"):
            layout.label(text="Error: Extended path list not found", icon='ERROR')
            return
            
        list_collection = wm.pa_path_list_extended
        
        # Header with statistics
        stats = []
        if wm.pa_links_stats.broken_count:
            stats.append(f"{wm.pa_links_stats.broken_count} broken")
        if wm.pa_links_stats.absolute_count:
            stats.append(f"{wm.pa_links_stats.absolute_count} absolute")
        if wm.pa_links_stats.relative_count:
            stats.append(f"{wm.pa_links_stats.relative_count} relative")
        if wm.pa_links_stats.bundled_count:
            stats.append(f"{wm.pa_links_stats.bundled_count} bundled")
        
        if stats:
            row = layout.row()
            row.label(text=" | ".join(stats))
            
            # Add missing files search options if there are broken links
            if wm.pa_links_stats.broken_count:
                sub_row = row.row(align=True)
                sub_row.label(text="Find missing:")
                sub_row.operator('file.find_missing_files', text='All Files').directory = ''
                
                # In parent hierarchy (two levels up from blend file)
                try:
                    if bpy.data.is_saved:
                        sub_row.operator('file.find_missing_files', text='Near Blend').directory = Path(bpy.data.filepath).parents[1].as_posix()
                except (IndexError, AttributeError):
                    pass

        # Sort options and search row
        row = layout.row(align=False)
        
        row.prop(self, "sort_by", text="")
        
        row.prop(self, "reverse_sort", text="", icon='SORT_ASC' if not self.reverse_sort else 'SORT_DESC')
        
        row.prop(self, 'search_field', text="", icon='VIEWZOOM')

        if wm.pa_links_stats.bundled_count:
            row.prop(self, 'show_bundled')

        # Version check for blend files (if any)
        if any(item.is_blend and item.is_valid for item in list_collection):
            check_row = layout.row()
            check_row.operator('pathaction.check_latest_versions', text="Check Updates", icon='FILE_REFRESH')
            check_row.operator('pathaction.update_to_latest_versions', text="Apply All Updates", icon='IMPORT')

        layout.separator()
        
        if not len(list_collection):
            layout.label(text='No external links found', icon='INFO')
            return
        
        # Filter out bundled paths if disabled
        visible_items = list_collection
        if not self.show_bundled:
            visible_items = [item for item in list_collection if not item.is_bundled]
            if not visible_items:
                layout.label(text='Only bundled paths (hidden)', icon='INFO')
                return

        filtered_items = visible_items

        # Apply search filter if text entered
        search_terms = self.search_field
        if search_terms:
            ## Note: using '.removeprefix('//')' before using 'Path().name' because Pathlib starting with '//' considered as UNC path on Windows.
            ## with only one parent ("//../some_file.ext"), last part is misinterpreted as being a folder (thus Path.name returns empty string)
            filtered_items = [item for item in visible_items if search_terms.lower() in Path(item.path.removeprefix('//')).name.lower()]

            # Nothing found in name, fall back in full path search
            if not filtered_items:
                filtered_items = [item for item in visible_items if search_terms.lower() in item.path.lower()]
                if filtered_items:
                    layout.label(text=f'Match path (nothing in names)', icon='INFO')

            if not filtered_items:
                layout.label(text='Nothing found', icon='ERROR')
                return
        
        # Sort the filtered items
        sorted_items = self.sort_items(filtered_items)
        
        # Create columns layout similar to history.py
        main_row = layout.row(align=True)
        path_col = main_row.column(align=True)
        path_col.alignment = 'LEFT'
        
        action_col = main_row.column(align=True)
        action_col.alignment = 'RIGHT'
        
        # Track previous type/status for adding separators
        prev_type = None
        prev_status = None
        
        # Display items
        for i, item in enumerate(sorted_items):
            if item.is_error_message:
                error_row = path_col.row()
                error_row.label(text=item.path, icon='ERROR')
                
                # Placeholder for action
                action_row = action_col.row(align=True)
                action_row.label(text="", icon='BLANK1')
                continue
            
            # Add separators based on sorting
            if self.sort_by == 'TYPE':
                # Get current file extension
                current_type = os.path.splitext(item.path)[1].lower()
                if prev_type is not None and current_type != prev_type:
                    path_col.separator()
                    action_col.separator()
                prev_type = current_type
            
            elif self.sort_by == 'STATUS':
                # Determine current status
                if not item.is_valid:
                    current_status = "broken"
                elif item.is_packed:
                    current_status = "packed"
                elif item.is_blend and item.latest_version:
                    current_status = "update"
                elif item.is_relative:
                    current_status = "relative"
                elif item.is_bundled:
                    current_status = "bundled"
                else:
                    current_status = "absolute"
                
                if prev_status is not None and current_status != prev_status:
                    path_col.separator()
                    action_col.separator()
                prev_status = current_status
            
            path = Path(item.path)
            abs_path = os.path.abspath(bpy.path.abspath(item.path))
            # Determine status icon
            if item.is_packed:
                status_icon = 'PACKAGE'
            elif not item.is_valid:
                status_icon = 'LIBRARY_DATA_BROKEN'
            elif item.is_blend and item.latest_version:
                status_icon = 'FILE_REFRESH'
            elif item.is_relative:
                status_icon = 'LINKED'
            elif item.is_bundled:
                status_icon = 'BLENDER'
            else:
                status_icon = get_file_icon(abs_path)
            
            # Path row
            path_row = path_col.row(align=True)
            path_row.alignment = 'LEFT'
            
            # Make path clickable with appropriate action
            if not item.is_valid:
                # Disabled row for broken links
                path_row.enabled = False
                path_row.operator('wm.path_open', text=item.path, emboss=False, icon=status_icon).filepath = abs_path
            else:
                # For blend files, use open_mainfile
                if item.is_blend:
                    op = path_row.operator('wm.open_mainfile', text=item.path, emboss=False, icon=status_icon)
                    op.filepath = abs_path
                    op.display_file_selector = False
                    op.load_ui = context.preferences.filepaths.use_load_ui
                else:
                    # For other files, use path_open
                    path_row.operator('wm.path_open', text=str(path), emboss=False, icon=status_icon).filepath = abs_path
            
            # Actions row with consistent spacing
            action_row = action_col.row(align=True)
            action_row.alignment = 'RIGHT'
            
            # Open folder button (always available)
            open_path = item.path
            if not item.is_valid and item.valid_parent_path:
                open_path = item.valid_parent_path
                            
            # Special actions for blend files
            if item.is_blend:
                if item.latest_version: # and item.is_valid 
                    # Show update button if available
                    op = action_row.operator("pathaction.update_file_path", text="", icon='EMPTY_SINGLE_ARROW')
                    op.source_path = item.path
                    op.target_path = item.latest_version
                else:
                    # Add placeholder when no update is available
                    action_row.label(text="", icon='BLANK1')

                # Open in new instance (only if valid)
                if item.is_valid:
                    action_row.operator("wm.open_in_new_instance", text="", icon='FILE_BACKUP').filepath = abs_path
                else:
                    action_row.label(text="", icon='BLANK1')  # New instance placeholder
                
                # Path editing (only for blend files)
                action_row.operator("pathaction.edit_file_path", text="", icon='GREASEPENCIL').source_path = item.path
                op = action_row.operator("pathaction.replace_file_library", text="", icon='FOLDER_REDIRECT')
                op.source_path = item.path
                parent_dir = ''.join(re.split(r'([\\/])', item.path)[:-1])
                if Path(bpy.path.abspath(parent_dir)).exists():
                    op.filepath = parent_dir

                # List linked datablocks and select related objects
                action_row.operator("pathaction.select_library_users", text="", icon='RESTRICT_SELECT_OFF').library_path = item.path

            else:
                # Add placeholders for consistent spacing
                action_row.label(text="", icon='BLANK1')  # Select users placeholder
                action_row.label(text="", icon='BLANK1')  # Update target placeholder
                action_row.label(text="", icon='BLANK1')  # New instance placeholder
                action_row.label(text="", icon='BLANK1')  # Edit path placeholder
                action_row.label(text="", icon='BLANK1')  # Browse path placeholder

            ## Open and copy at the end (always available)
            if open_path:
                ## using open_path, as it can go to up several folder for broken links
                action_row.operator("path.open_browser", text="", icon='FILE_FOLDER').filepath = os.path.abspath(bpy.path.abspath(open_path))
            else:
                action_row.label(text="", icon='BLANK1')

            # Copy path button
            action_row.operator("pathaction.copy_path", text="", icon='COPYDOWN').path = item.path

    
    def execute(self, context):
        return {"FINISHED"}

class PATHACTION_PT_outliner_links_checker(Panel):
    bl_space_type = 'OUTLINER'
    bl_region_type = 'HEADER'
    bl_label = "Links"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        layout.operator("pathaction.links_checker", text="Check File Links", icon='LINKED')

def draw_outliner_header_button(self, context):
    if not bpy.context.preferences.addons[__package__].preferences.dev_mode:
        return
    if context.space_data.display_mode != 'LIBRARIES':
        return
    layout = self.layout
    # layout.separator()
    layout.operator("pathaction.links_checker", text="", icon='LINKED')

classes = (
    PATHACTION_PG_path_list_extended,
    PATHACTION_PG_links_stats,
    PATHACTION_OT_update_file_path,
    PATHACTION_OT_edit_file_path,
    PATHACTION_OT_replace_file_library,
    PATHACTION_OT_select_library_users,
    PATHACTION_OT_library_infos,
    PATHACTION_OT_library_type_details,
    PATHACTION_OT_check_latest_versions,
    PATHACTION_OT_update_to_latest_versions,
    PATHACTION_OT_links_checker,
    PATHACTION_PT_outliner_links_checker,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Create the property groups
    bpy.types.WindowManager.pa_path_list_extended = bpy.props.CollectionProperty(type=PATHACTION_PG_path_list_extended)
    bpy.types.WindowManager.pa_links_stats = bpy.props.PointerProperty(type=PATHACTION_PG_links_stats)
    
    # Add button to outliner header
    bpy.types.OUTLINER_HT_header.append(draw_outliner_header_button)

def unregister():
    # Remove button from outliner header
    bpy.types.OUTLINER_HT_header.remove(draw_outliner_header_button)
    
    # Remove the properties
    del bpy.types.WindowManager.pa_path_list_extended
    del bpy.types.WindowManager.pa_links_stats
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)