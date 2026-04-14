import bpy
import sys
import subprocess
from os.path import isfile, dirname, normpath, abspath
from shutil import which

def open_folder(folderpath):
    """
    open the folder at the path given
    with cmd relative to user's OS
    on window, select
    """
    import subprocess

    myOS = sys.platform
    if myOS.startswith(('linux','freebsd')):
        cmd = 'xdg-open'

    elif myOS.startswith('win'):
        cmd = 'explorer'
        if not folderpath:
            return('/')
    else:
        cmd = 'open'

    if not folderpath:
        return('//')

    if isfile(folderpath): # When pointing to a file
        select = False
        if myOS.startswith('win'):
            # Keep same path but add "/select" the file (windows cmd option)
            cmd = 'explorer /select,'
            select = True

        elif myOS.startswith(('linux','freebsd')):
            if which('nemo'):
                cmd = 'nemo --no-desktop'
                select = True
            elif which('nautilus'):
                cmd = 'nautilus --no-desktop'
                select = True

        if not select:
            # Use directory of the file
            folderpath = dirname(folderpath)

    folderpath = normpath(folderpath)
    fullcmd = cmd.split() + [folderpath]
    # print('Opening command :', fullcmd)
    subprocess.Popen(fullcmd)
    return ' '.join(fullcmd)

def open_blend_new_instance(filepath=None, strip_extra_args=False):
    """Open the passed blend file in a new instance of blender
    filepath (str): path to blend file, if None, will use current blend file
    strip_extra_args (bool, default False): 
        False: Replicate exactly original command with blend filepath
        True: Command will be only [blender-binary filepath], stripping all initial args.

    """
    filepath = filepath or bpy.data.filepath

    filepath = str(filepath)
    if filepath.startswith('//'):
        filepath = abspath(bpy.path.abspath(filepath))
        print(filepath)

    cmd = sys.argv

    # If no filepath, use command as is to reopen blender
    if filepath != '':
        ## Sometimes filepath is not directly second argument
        if len(cmd) > 1 and next((arg for arg in cmd[1:] if arg.endswith('.blend')), None):
            # Iterate and replace first occurence with current blend``
            for i in range(1, len(cmd)):
                if cmd[i].endswith('.blend'):
                    cmd[i] = filepath
                    break
        else:
            cmd.insert(1, filepath)

    if strip_extra_args:
        cmd = [sys.argv[0], filepath]

    # print('cmd: ', cmd)
    system = sys.platform.lower()
    if system.startswith('linux'):
        cmd = ['gnome-terminal', '--'] + cmd
    elif system.startswith('darwin'):
        cmd = ['open', '-W', '-a', 'Terminal.app'] + cmd
    #elif system == 'Windows': # do not seem to be needed
    #     cmd = ['start', '--']+ cmd

    subprocess.Popen(cmd) #, shell=True
    
    ## potential flag for windows, seem to work without
    # subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)