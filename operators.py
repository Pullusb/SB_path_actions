import bpy
from pathlib import Path
import os
from bpy.types import Operator, Panel
from os.path import dirname, basename, realpath, split, exists

from .path_func import open_folder
from .prefs import blender_locations


class PATHACTION_PT_blend_location_ui(Panel):
    bl_space_type = "VIEW_3D"
    # bl_region_type = "HEADER"
    bl_region_type = "UI"
    bl_category = "View"
    bl_label = "Blender Locations"
    bl_options = {'INSTANCED'}

    def draw(self, context):
        layout = self.layout
        layout.operator("pathaction.blend_history", text="File History", icon='FILE_BLEND') # BLENDER
        layout.operator("path.copy_blend_path", text="Copy Formatted Blend Path", icon='COPYDOWN') # Copy Blend Path Format...
        layout.operator("pathaction.links_checker", text="Check File Links", icon='LINKED') # Check Links 
        layout.separator()
        blender_locations(layout)

        ## Limit single addon search to dev mode ?
        # if bpy.context.preferences.addons[__package__].preferences.dev_mode:
        layout.operator("path.open_addon_directory", text='Single Addon Directory', icon='VIEWZOOM') # PLUGIN

class PATHACTION_OT_copy_text_to_clipboard(Operator):
    bl_idname = "pathaction.copy_text_to_clipboard"
    bl_label = "Copy String"
    bl_description = "Copy passed string to clipboard"
    bl_options = {"REGISTER", "INTERNAL"}

    text : bpy.props.StringProperty(options={'SKIP_SAVE'})
    
    report_info : bpy.props.BoolProperty(name="Report Info", default=True)
    
    def execute(self, context):
        if not self.text:
            self.report({'WARNING'}, f'Nothing to copy!')
            return {"CANCELLED"}
        bpy.context.window_manager.clipboard = self.text
        if self.report_info:
            self.report({'INFO'}, f'Copied: {self.text}')
        return {"FINISHED"}


## Popup to copy alternative path from a single generic path
class PATHACTION_OT_copy_alternative_path(bpy.types.Operator):
    bl_idname = "pathaction.copy_alternative_path"
    bl_label = "Copy Alternative Path"
    bl_description = "Copy a chosen alternative path in a list from a single path"
    bl_options = {"REGISTER", "INTERNAL"}

    path : bpy.props.StringProperty(options={'SKIP_SAVE'})

    # probe : bpy.props.BoolProperty(name="Probe",
    #     description="Check if path is valid",
    #     default=False, options={'SKIP_SAVE'})

    relative_to_blend : bpy.props.BoolProperty(name="Relative to Blend",
        description="Show path absolute/relative to current blend file, like libraries or links",
        default=False)

    quote_style : bpy.props.EnumProperty(
        name="Quote Style",
        description="Choose the quote style",
        items=(
            ('PLAIN', "Plain", "No quotes", 0),
            ('DOUBLE', "Double Quote", 'Wrap with "', 1),
            ('SINGLE', "Single Quote", "Wrap with '", 2),
            ('BACK', "Back Quote", "Wrap with `", 3)
        ),
        default='PLAIN',
        # options={'SKIP_SAVE'}
    )

    report_info : bpy.props.BoolProperty(name="Report Info", default=True)

    def invoke(self, context, event):
        if not self.path:
            return {"CANCELLED"}
        self.pathes = []

        print('self.path: ', self.path)
        try:
            path_obj = Path(self.path)
            absolute = Path(os.path.abspath(bpy.path.abspath(self.path)))
            resolved = Path(bpy.path.abspath(self.path)).resolve()
        except:
            # case of invalid / non-accessable path
            bpy.context.window_manager.clipboard = self.path
            self.report({'INFO'}, f'Copied: {self.path}')
            return self.execute(context)

        self.pathes.append(('Path', self.path))
        self.pathes.append(('Parent', dirname(self.path)))

        ## Show absolute path if different
        if absolute != path_obj:        
            self.pathes.append(('Absolute', str(absolute)))
            self.pathes.append(('Absolute Parent', str(absolute.parent)))

        ## Show resolved path if different
        if absolute != resolved:
            self.pathes.append(('Resolved', str(resolved)))
            self.pathes.append(('Absolute Parent', str(resolved.parent)))

        ## TODO: If current Blend file is saved, also show relative path to blend (if path is not already relative)
        ## Moslty interesting for libraries (could be shown only if a dedicated operator prop is enabled)
        # /wip relative_path
        # if self.relative_to_blend and bpy.data.is_saved:
        #     ## if it's a relative path, show absolute path
        #     ## how to detect if it's relative to blend ? (could be a library or a link)
        #     if path_obj.is_absolute():
        #         blend_path = Path(bpy.data.filepath)
        #         # if not blend_path.is_absolute():
        #         #     blend_path = blend_path.resolve()
        #         relative = path_obj.relative_to(blend_path.parent)
        #         self.pathes.append(('Relative to Blend', str(relative))
        #     )
        #     blend_path = Path(bpy.data.filepath)
        #     # if not blend_path.is_absolute():
        #     #     blend_path = blend_path.resolve()
        #     relative = path_obj.relative_to(blend_path.parent)
        #     self.pathes.append(('Relative to Blend', str(relative)))
        ## wip /
        

        ## Get name and stem using bpy.path as pathlib can be problematic with path starting with // (add an extra `/`)
        if name := bpy.path.basename(self.path):
            self.pathes.append(('Name', name))
        if (stem := bpy.path.display_name_from_filepath(self.path)) and stem != name:
            self.pathes.append(('Stem', stem))

        maxlen = max(len(l[1]) for l in self.pathes)
        popup_width = 800 
        if maxlen < 50:
            popup_width = 500
        elif maxlen > 100:
            popup_width = 1000
        return context.window_manager.invoke_props_dialog(self, width=popup_width)
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        # with align True, path are probably too close visually
        col = layout.column(align=False)
        row = col.row()
        # row.use_property_split = False # <- only on row
        row.prop(self, 'quote_style', text='Quote Style', expand=True)

        col.separator()

        for action_name, filepath in self.pathes:

            if self.quote_style == 'DOUBLE':
                filepath = f'"{filepath}"'
            elif self.quote_style == 'SINGLE':
                filepath = f"'{filepath}'"
            elif self.quote_style == 'BACK':
                filepath = f"`{filepath}`"

            split=col.split(factor=0.2, align=True)

            op = split.operator('pathaction.copy_text_to_clipboard', text=action_name, icon='COPYDOWN')
            op.text = filepath
            op.report_info = self.report_info

            split.label(text=filepath)

    def execute(self, context):
        return {"FINISHED"}


## Same as copy_text_to_clipboard, but dedicated to path, and with optional popup for alternative
class PATHACTION_OT_copy_path(Operator):
    bl_idname = "pathaction.copy_path"
    bl_label = "Copy Path To Clipboard"
    bl_description = "Click: Copy path\
        \nAlt + Click: Pop-up alternative path to copy (with optional quote styles)"
    bl_options = {"REGISTER", "INTERNAL"}

    path : bpy.props.StringProperty(options={'SKIP_SAVE'})
    
    report_info : bpy.props.BoolProperty(name="Report Info", default=True)

    def invoke(self, context, event):
        if event.alt:
            return bpy.ops.pathaction.copy_alternative_path('INVOKE_DEFAULT', path=self.path)
        return self.execute(context)

    def execute(self, context):
        ## Could also just call the other operator:
        # bpy.ops.pathaction.copy_text_to_clipboard(path=self.path, report_info=self.report_info)
        # return {"FINISHED"}
        if not self.path:
            self.report({'WARNING'}, f'Nothing to copy!')
            return {"CANCELLED"}
        bpy.context.window_manager.clipboard = self.path
        if self.report_info:
            self.report({'INFO'}, f'Copied: {self.path}')
        return {"FINISHED"}


### --
## Copy *blend* path and alternatives
## 

class PATH_OT_copy_blend_path(Operator):
    bl_idname = "path.copy_blend_path"
    bl_label = "Copy Blend Path"
    bl_description = "Copy path to blend from a list of proposed alternative"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return bpy.data.is_saved

    quote_style : bpy.props.EnumProperty(
        name="Quote Style",
        description="Choose the quote style",
        items=(
            ('PLAIN', "Plain", "No quotes", 0),
            ('DOUBLE', "Double Quote", 'Wrap with "', 1),
            ('SINGLE', "Single Quote", "Wrap with '", 2),
            ('BACK', "Back Quote", "Wrap with `", 3)
        ),
        default='PLAIN',
        # options={'SKIP_SAVE'}
    )

    def invoke(self, context, event):
        self.path = bpy.data.filepath
        if not self.path:
            return {"CANCELLED"}
        self.pathes = []

        path_obj = Path(self.path)
        absolute = Path(os.path.abspath(bpy.path.abspath(self.path)))
        resolved = Path(bpy.path.abspath(self.path)).resolve()

        self.pathes.append(('Blend', self.path))
        self.pathes.append(('Folder', dirname(self.path)))

        ## Show absolute path if different
        if absolute != path_obj:        
            self.pathes.append(('Absolute', str(absolute)))
            self.pathes.append(('Absolute Parent', str(absolute.parent)))

        ## Show resolved path if different
        if absolute != resolved:
            self.pathes.append(('Resolved', str(resolved)))
            self.pathes.append(('Resolved Parent', str(resolved.parent)))

        if path_obj.name:
            self.pathes.append(('Name', path_obj.name))
        
            ## Show stem only if different from name
            if path_obj.stem != path_obj.name:
                self.pathes.append(('Stem', path_obj.stem))

        maxlen = max(len(l[1]) for l in self.pathes)
        popup_width = 800 
        if maxlen < 50:
            popup_width = 500
        elif maxlen > 100:
            popup_width = 1000
        return context.window_manager.invoke_props_dialog(self, width=popup_width)
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        # with align True, path are probably too close visually
        col = layout.column(align=False)
        row = col.row()
        # row.use_property_split = False # <- only on row
        row.prop(self, 'quote_style', text='Quote Style', expand=True)

        col.separator()

        for action_name, filepath in self.pathes:

            if self.quote_style == 'DOUBLE':
                filepath = f'"{filepath}"'
            elif self.quote_style == 'SINGLE':
                filepath = f"'{filepath}'"
            elif self.quote_style == 'BACK':
                filepath = f"`{filepath}`"

            split=col.split(factor=0.12, align=True)
            split.operator('pathaction.copy_text_to_clipboard', text=action_name, icon='COPYDOWN').text = filepath
            split.label(text=filepath)

    def execute(self, context):
        return {"FINISHED"}

class PATH_OT_browser_to_blend_folder(Operator):
    """current blend path to the browser filepath"""
    bl_idname = "path.browser_to_blend_folder"
    bl_label = "Browser to blend folder"

    def execute(self, context):
        bpy.ops.file.select_bookmark(dir="//")
        return {"FINISHED"}

class PATH_OT_open_filepath_folder(Operator):
    """Open browser filepath directory in OS explorer"""
    bl_idname = "path.open_filepath"
    bl_label = "Open Current filepath"

    def execute(self, context):
        try: #handle error if context isn't filebrowser (if operator is launched from search)
            folder = context.space_data.params.directory #give the path, params.filename give the tail (file)
            open_folder(folder.decode())
        except:
            self.report({'WARNING'}, "Only works in fileBrowser context")
        return {"FINISHED"}

class PATH_OT_open_blend_folder(Operator):
    bl_idname = "wm.open_blend_folder"
    bl_label = "Open blend folder"
    bl_description = "Open blend's directory in OS explorer\
        \n\
        \nCtrl: Copy path to blend\
        \nShift: Open a side blend\
        \nAlt: History and blend app locations\
        \nCtrl+Alt: Copy formatted blend path"
    bl_options = {'REGISTER'}

    # @classmethod
    # def poll(cls, context):
    #     return bpy.data.is_saved

    def invoke(self, context, event):
        self.ctrl = event.ctrl
        self.alt = event.alt
        self.shift = event.shift
        if not bpy.data.is_saved and not (self.alt and not self.ctrl and not self.shift):
            self.report({'ERROR'}, "Blend not saved: No folder to open or copy")
            return {'CANCELLED'}
        return self.execute(context)

    def execute(self, context):
        fileloc = bpy.data.filepath # bpy.context.blend_data.filepath
        # folder = dirname(fileloc)

        # if self.ctrl and self.shift:
        #     bpy.context.window_manager.clipboard = fileloc
        #     self.report({'INFO'}, f'Copied: {fileloc}')
        #     return {'FINISHED'}
        
        if self.ctrl and self.alt:
            ## Alternative path to blend
            bpy.ops.path.copy_blend_path('INVOKE_DEFAULT')
            return {'FINISHED'}
        
        elif self.ctrl:
            ## Direct raw path copy
            bpy.context.window_manager.clipboard = fileloc
            self.report({'INFO'}, f'Copied: {fileloc}')
            return {'FINISHED'}
        
        elif self.shift:
            ## Open side blend
            bpy.ops.wm.open_side_blend('INVOKE_DEFAULT')
            self.report({'INFO'}, f'Open side blend')
            return {'FINISHED'}
        
        elif self.alt:
            ## Blend user/config/addon locations
            bpy.ops.wm.call_panel(name="PATHACTION_PT_blend_location_ui", keep_open=True)
            return {'FINISHED'}

        open_folder(fileloc)

        self.report({'INFO'}, "Blend's folder opened")
        return {'FINISHED'}


## Only accessible trough search
class PATH_OT_open_output_folder(Operator):
    """open output directory in OS explorer"""
    bl_idname = "path.open_output"
    bl_label = "Open output folder"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        outfileloc = bpy.context.scene.render.filepath # get filepath from blender
        folder = dirname(outfileloc) # get last dir

        if folder.startswith("/"): #Convert root/relative path to absolute
            folder = realpath(bpy.path.abspath(folder))

        fhead, _ftail = split(folder)
 
        
        if exists(folder):
            self.report({'INFO'}, "Open " + folder)
            open_folder(folder)

        elif exists(fhead):
           self.report({'INFO'}, "Open " + fhead)
           open_folder(fhead)

        else:
            self.report({'INFO'}, "Can't open " + folder)

        return {'FINISHED'}

       
## Only accessible through search (when developper extras is enabled)
class PATH_OT_switch_path_operator(Operator):
    """toggle path absolute/relative"""
    bl_idname = "path.switch_output_path_mode"
    bl_label = "Switch output path mode"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        compare = open_folder(False) # return "//" for windows, "/" for other OS
        
        fpath = bpy.context.scene.render.filepath
        if fpath.startswith(compare):
            bpy.context.scene.render.filepath = realpath(bpy.path.abspath(fpath))
        else:
            bpy.context.scene.render.filepath = bpy.path.relpath(fpath)

        return {'FINISHED'}


classes = (
    PATHACTION_OT_copy_text_to_clipboard,
    PATHACTION_OT_copy_alternative_path,
    PATHACTION_OT_copy_path,
    PATH_OT_copy_blend_path,
    PATH_OT_switch_path_operator,
    PATH_OT_open_output_folder,
    PATH_OT_open_blend_folder,
    PATH_OT_browser_to_blend_folder,
    PATH_OT_open_filepath_folder,
    PATHACTION_PT_blend_location_ui,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

