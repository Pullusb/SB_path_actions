# Path-Actions

Add buttons in Blender UI to open directory of blend file or output path in the OS explorer.

**[Get it on Gumroad ](https://pullusb.gumroad.com/l/path_actions)**

**[Download latest](https://github.com/Pullusb/SB_path_actions/archive/refs/heads/master.zip)**

For old blender 2.7 version go [here](https://github.com/Pullusb/SB_blender_addons_old_2_7)

**[Demo Youtube](https://youtu.be/DBHRc0oE7rI)**  
  
--------

## Description:

Consult [changelog here](CHANGELOG.md)

## Upper right button

Add a folder icon button at the right of the topbar that open Blend's current directory

![OpenBlendFolder](https://github.com/Pullusb/images_repo/blob/master/Bl_PathAction_OpenBlendFolder28.png)
  
Alternative functions to _Open folder_ button, instead of opening:

- combine with `Ctrl` to copy _full path to file_ 
- combine with `Ctrl + Shift` to copy _path to directory_ 
- combine with `Alt` to copy _file name_
- `Shift + Clic` open a new menu to open files that are in same folder as the current blend:
  - click on blend names to open "in place"
  - click on right icon to open in a new instance of blender

Check _Developer mode_ in preferences to add a button on upper right corner to close and reopen blender with current blend (`Ctrl + Clic` on the button reopen without unsaved warning)

## Quick go in asset browser

Add 2 buttons in the footer of the file/asset browser:
  
"Blend location" button bring the file/asset browser where the blend is saved (button doesn't appear if not saved)
  
"Open folder" button open the path of the file/asset browser in the OS explorer.

![Browser](https://github.com/Pullusb/images_repo/blob/master/Bl_PathAction_Browser28.png)
  

## operators in search menu

Also add two Operators accessible through search (F3 in 2.8):

"Open output folder" just open output path in OS.

![openOutput](https://github.com/Pullusb/images_repo/blob/master/Bl_PathAction_openOutput28.png)
  
"Switch output path mode" simply toggle the output path between relative and absolute.

![switchPath](https://github.com/Pullusb/images_repo/blob/master/Bl_PathAction_switchPath28.png)


Add Shortcut : `Ctrl + Alt+ Shift + O` pop up a search in recent history to quickly find a previous to open.

--------

### Older version for 2.7 :
Add 2 buttons in the Properties>Output pannel

![Output pannel with Path-Actions Addon enabled](http://www.samuelbernou.fr/imgs/git/Addon_PathAction_screen_output-tab.PNG)

Add 2 buttons in the header of the filebrowser
"Blend location" button bring the filebrowser where the blend is saved (button does'nt appear if not saved)

"Open folder" button open the path of the filebrowser in the OS explorer.

![Filebrowser header with Path-Actions Addon enabled](http://www.samuelbernou.fr/imgs/git/Addon_PathAction_screen_filebrower-tab.png)
