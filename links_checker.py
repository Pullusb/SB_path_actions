import bpy
import os
from pathlib import Path

## TODO: Add Version update based on name:
# - Add option to update path to latest version if any in directory (based on stem number suffix, needs to be at the end to be valid, )
# - Operator to make the update check (don't make it automatically at invoke): Either for one or all
# - Operator to actually update the path
# - Note: need to store a reference to the library path somewhere... not sure if item can hold the property

## TODO: Operator to edit a file path
# - one to edit directly as string. Specify in the popup that, unlike relocate, Blend should be saved and reopen for the change to take effect... and that it's a good idea to increment before proceeding)
# - one to open a file browser to select a new file to replace

## TODO: Optional: Show icon based on file extension ? (maybe not needed for a chain icon since all are external link ? not sure))
# - can compare extension using following functions:
# - bpy.path.extensions_audio
# - bpy.path.extensions_image
# - bpy.path.extensions_movie


## TODO: When path is a Blend:
# - Check if the file is a blend file
# - Add a button to open the blend file in place or in a new instance

## TODO: Add possibility to reorder UI:
# - By path validity (broken or not)
# - By file type (blend, image, etc) ?

## TODO: Add a label displaying the number of users of a link (with an added shield icon if there is a fake user)

## TODO: Add an icon in the BlendFile outliner header to open the links checker

## TODO: make the popup window width the size of the longest path (+ margin for all icons)

class PATHACTION_OT_links_checker(bpy.types.Operator):
    bl_idname = "pathaction.links_checker"
    bl_label = "File Links Checker"
    bl_description = "Check states of external links in blend file"
    bl_options = {"REGISTER"}
    
    search_field : bpy.props.StringProperty(
        name='Search Filter', default='',
        description='Filter by name, case insensitive',
        options={'TEXTEDIT_UPDATE'}
    )
    
    def invoke(self, context, event):
        self.check_links(context)
        return context.window_manager.invoke_props_dialog(self, width=480)
    
    def check_links(self, context):
        wm = context.window_manager
        wm.pa_path_list.clear()
        
        # Get all paths
        viewed = []
        self.broken_count = 0
        self.absolute_count = 0
        self.relative_count = 0
        
        for current, lib in zip(bpy.utils.blend_paths(local=True), bpy.utils.blend_paths(absolute=True, local=True)):
            # Avoid relisting same path multiple times
            if current in viewed:
                continue
            viewed.append(current)
            
            try:
                realib = Path(current) # path as-is
                lfp = Path(lib) # absolute path
                
                item = wm.pa_path_list.add()
                item.path = current
                item.is_checked = True
                
                if not lfp.exists():
                    item.is_valid = False
                    self.broken_count += 1
                    
                    # Try to find a valid parent path
                    for i in range(len(lfp.parts) - 2):
                        parent = lfp.parents[i]
                        if parent.exists():
                            item.valid_parent_path = str(parent)
                            break
                else:
                    item.is_valid = True
                    if current.startswith('//'):
                        self.relative_count += 1
                        item.is_relative = True
                    else:
                        self.absolute_count += 1
                        item.is_relative = False
            except:
                item = wm.pa_path_list.add()
                item.path = f'Error checking: {current}'
                item.is_checked = True
                item.is_valid = False
                item.is_error_message = True
                self.broken_count += 1
    
    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        
        list_collection = wm.pa_path_list
        
        # Header with statistics
        stats = []
        if self.broken_count:
            stats.append(f"{self.broken_count} broken")
        if self.absolute_count:
            stats.append(f"{self.absolute_count} absolute")
        if self.relative_count:
            stats.append(f"{self.relative_count} relative")
        
        if stats:
            layout.label(text=" | ".join(stats))
        
        # Add missing files search options if there are broken links
        if self.broken_count:
            layout.label(text="You can try to scan for missing files:")
            
            # In parent hierarchy (two levels up from blend file)
            try:
                layout.operator('file.find_missing_files', text='In Parent Hierarchy').directory = Path(bpy.data.filepath).parents[1].as_posix()
            except (IndexError, AttributeError):
                pass

        layout.separator()
        
        layout.prop(self, 'search_field', text="", icon='VIEWZOOM')
        
        if not len(list_collection):
            layout.label(text='No external links found', icon='INFO')
            return
        
        search_terms = self.search_field
        if search_terms:
            result = [item for item in list_collection if search_terms.lower() in Path(item.path).name.lower()]
            
            if not result:
                layout.label(text='Nothing found', icon='ERROR')
                return
                
            list_collection = result
        
        # Create columns for path and actions
        main_row = layout.row(align=True)
        path_col = main_row.column(align=True)
        path_col.alignment = 'LEFT'
        
        action_col = main_row.column(align=True)
        action_col.alignment = 'RIGHT'
        
        for item in list_collection:
            path_row = path_col.row(align=True)
            action_row = action_col.row(align=True)
            action_row.alignment = 'RIGHT'
            
            if item.is_error_message:
                path_row.label(text=item.path, icon='ERROR')
                action_row.label(text='', icon='BLANK1')
                continue
            
            path = Path(item.path)
            
            # Set appropriate icon based on path type
            icon = 'LINKED' if item.is_relative else 'LIBRARY_DATA_INDIRECT'
            if not item.is_valid:
                icon = 'LIBRARY_DATA_BROKEN'
            
            path_row.label(text=str(path), icon=icon)
            
            # Actions
            open_path = item.path
            if not item.is_valid and item.valid_parent_path:
                open_path = item.valid_parent_path
            
            if open_path:
                # Open folder button
                # action_row.operator("wm.path_open", text="", icon='FILE_FOLDER').filepath = str(Path(open_path).parent) # native function
                action_row.operator("path.open_browser", text="", icon='FILE_FOLDER').filepath = open_path # Custom with file select
                
                # Open/execute the file button (only if the file exists)
                if item.is_valid:
                    action_row.operator("wm.path_open", text="", icon='FILE_TICK').filepath = open_path # Native function
            
            # Copy path button
            action_row.operator("pathaction.copy_path", text="", icon='COPYDOWN').path = item.path
    
    def execute(self, context):
        return {"FINISHED"}

classes = (
    PATHACTION_OT_links_checker,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)