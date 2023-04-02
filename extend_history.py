import bpy
from pathlib import Path
from bpy.types import Operator
import tempfile
import shutil

class PATH_OT_dump_history(Operator) :
    bl_idname = "path.dump_history"
    bl_label = 'Dump File History'
    bl_description = 'Add the file history to a single file'

    def execute(self, context):
        
        history = Path(bpy.utils.user_resource('CONFIG', path='recent-files.txt'))
        if not history.exists():
            self.report({'WARNING'}, 'No history file found')
            return {'CANCELLED'}
        blends = []
        try:
            # with open(history, 'r') as fd:
            with history.open('r') as fd:
                # blends = [fd.readline().strip() for line in fd]
                blends = [line.strip() for line in fd]
        except:
            self.report({'ERROR'}, f'error accessing recent-file.txt : {history}')
            return {'CANCELLED'}
        if not blends:
            self.report({'WARNING'}, f'Empty history !')
            return {'CANCELLED'}
        
        tmp = Path(tempfile.gettempdir())

        all_blends = []

        ext_history = tmp / 'blender_extended_history.txt'
        if ext_history.exists():
            with ext_history.open('r') as fd:
                all_blends = [fd.readline().strip() for line in fd]
        
        # remove duplicate from existing extended history (bring existing to top)
        for l in blends:
            if l in all_blends:
                all_blends.remove(l)
        
        new_history = blends + all_blends
        
        # add trailing return
        new_history = [f'{path_str.strip()}\n' for path_str in new_history]

        with ext_history.open('w') as fd:
            fd.writelines(new_history)
        
        self.report({'INFO'}, f'History dumped: {ext_history}')
        return {'FINISHED'}

class PATH_OT_restore_history(Operator) :
    bl_idname = "path.restore_history"
    bl_label = 'Restore File History'
    bl_description = 'Replace the current history file by the tmp '

    def execute(self, context):
        
        tmp = Path(tempfile.gettempdir())
        ext_history = tmp / 'blender_extended_history.txt'
        if not ext_history.exists():
            self.report({'WARNING'}, f'No extended history file found at: {ext_history}')
            return {'CANCELLED'}
        
        history = Path(bpy.utils.user_resource('CONFIG', path='recent-files.txt'))

        try:
            shutil.copyfile(ext_history, history)
            self.report({'INFO'}, f'Copied {ext_history} >> {history}')
            return {'FINISHED'}

        # If source and destination are same
        except shutil.SameFileError:
            self.report({'ERROR'}, "Source and destination represents the same file.")
        # If destination is a directory.
        except IsADirectoryError:
            self.report({'ERROR'}, "Destination is a directory.")
        # If there is any permission issue
        except PermissionError:
            self.report({'ERROR'}, "Permission denied.")
        # For other errors
        except:
            self.report({'ERROR'}, "Error occurred while copying file.")

        return {'CANCELLED'}


classes = (
PATH_OT_dump_history,
PATH_OT_restore_history
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)