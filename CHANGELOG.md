# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- ## [Unreleased] -->

## [2.5.1] - 2026-02-01

### Fixed

- ensure compatibility with 4.5+ with the new arg for relative path in string property (fixs errors in console)
- searchfield issue when path is '//../something.ext' where name will not be checked on Windows (viewed as UNC path)

### Added

- New quick open addon preferences using a search field in main menu (`Alt + Click` on folder icon)
- improved searchfield: Fallback search on path when nothing is found based on names

### Changed

- only expose `link checker` features with `dev mode` enabled (This is for advanced user or TDs as it needs to be used with caution)

## [2.5.0] - 2025-03-03

### Added

Multiple feature to link checker:
- When it's a blend, replace or edit (unlike relocate it just rewrite the filepath, blend needs to be saved and reopen for the library change to take effect)
- Open blend in new instance
- Look for updates

## [2.4.1] - 2025-02-28

### Added

`Link Checker` popup, can be called from `Alt` panel on corner icon:
- list external files linked or used within current blend file

### Fixed

Error when displaying relative file path's name and stem in "copy alternative path" operator

## [2.4.0] - 2025-02-07

### Added

Custom file history now have a search field:
- filter blend names in showed history
- when no exact result, try to fuzzy match blender name or parts of it.

### Changed

`Ctrl + Alt + Shit + O` now call file history window (from alternative actions panel) instead of recent file pure-search popup


## [2.3.2] - 2025-01-21

### Changed

`Open side blend` popup size is now fitted to longer path (could rapidly truncate long blend name before)
Swap button placement in blender filebrowser
Copy alternative path to blende in `Alt` popup.
Change licence to GPL V3 (to comply with Blender extension platform)

## [2.3.0] - 2025-01-12

### Added

The other copy buttons can be used with `Alt + click` allow to copy alternatives paths with different quote styles

Custom history display accessed from `Alt + Click` on folder icon with following feature:
- choose to inspect another blender version history (default to current blender version)
- click on a file name to open in-place (same as classic history)
- button to open in new blender instance
- button to open folder in OS
- button to copy blend path (`Alt + click` on it for alternative formatting choice)
- choices are greyed out when files are no longer available (in this case, open folder bring to the uppermost available folder).

### Changed

Now ask for confirmation when current blend is not saved and user try to open from *side blend* or from new *File history*

## [2.2.0] - 2024-12-15

### Added

Changed actions when pressing modifier keys while cliking on Folder icon button
- `Ctrl` : Copy path to blend (unchanged)
- `Ctrl + Alt` : Pop-up choices to copy alternatives representation of the path to blend + some options
- `Shit` : Open side Blend (unchanged)
- `Alt` : List app related locations, to open or copy path

### Changed

- revert shortcut changes from previous update
- Code refactor

## [2.1.0] - 2024-12-06

### Added

- "Copy chosen blend path" with Ctrl + Click on folder icon. Popup series of path versions to copy. Replace the old shortcuts that were hard to remember
- More copy otions. possibility to copy absolute or resolved path if different from native path. possible to quote the path to copy with multiple quote style.

### Removed

- Shortcut `Ctrl + Shift` and `Alt` on folder buttons. Now all those options (and more) exists on `Ctrl + Clic` popup


## [2.0.12] - 2024-12-04

### Changed

- allow shortcut assignation on `open_blender_folder` button


## [2.0.11] - 2024-06-03

### Changed

- permission list in manifest file


## [2.0.10] - 2024-05-24

### Changed

- some code now use Pathlib


## [2.0.9] - 2024-05-18

### Added

- blender Manifest toml file to submit as Blender extension
- replace preference access with new `__package__` name

## [2.0.8] - 2024-03-27

### Fixed

- using devmode reopen without second argument being a blend filepath

## [2.0.7] - 2023-07-14

### Fixed

- addon paths API changes in versions 3.6.0+ (`script_directory` -> `script_directories`)

## [2.0.6] - 2023-04-02

### Fixed

- missing new line character when using `Dump File History`

## [2.0.5] - 2022-11-29

### Changed

- Open side blend use natural sort

## [2.0.4] - 2022-11-24

### Changed

- Hide buttons in asset browser

## [2.0.3] - 2022-09-11

### Added

- dump/load history to/from an extended_history text file stored in temp files.
    - using from search `Dump File History` (path.dump_history) and `Restore File History` (path.restore_history)
    - Specific usecases, like transfering history from a blender version to another (ex: open 3.2 > Dump > open 3.3 > Restore)

## [2.0.2] - 2022-09-07

### Changed

- Developper `reopen` button is also available when file is not saved to reopen blender

## [2.0.1] - 2022-07-25

### Changed

- Pop list on`shit+click` even if there is only one blend in folder (allow to pop new instance quickly)
- Add compatibility with Mac for new blender instance

## [2.0.0] - 2022-06-30

### Added

- developper mode: add a button on upper right corner to close and reopen blender with current blend
    - Warn if file is not saved
    - `Ctrl + Clic` on the button reopen without unsaved warning

- `Shift + Clic` open a new menu to open files that are in same folder as the current blend
    - click on blend names to open "in place"
    - click on right icon to open in a new instance of blender

### Changed

- `Ctrl + Shift + Clic` to save to copy _path to directory_ (instead of `Shift` only previously)

## [1.9.1] - 2022-06-22

### Changed

- file browser UI for `blend location` and `open folder` ops changed to left bar instead of header (header is hided in basic file browser), code from `Amaranth` addon by Pablo Vasquez
- license model to oneliner `SPDX-License-Identifier: GPL-2.0-or-later`
## [1.8.3] - 2021-11-19

### Fixed
- Error in addon preference from api change in 3.0.0

## [1.8.2] - 2021-08-30

### Fixed
- Skip keymap register on background launch (prevent error in console)

## [1.8.1] - 2021-08-22

### Added
- when multiple name exists, write location and version
## [1.8.0] - 2021-08-09

### Added
- list all addon individual locations in addon prefs
- buttons to search by addon name and open directory in browser 

## [1.7.0] - 2021-07-24

### Added
- Added 5 buttons in addon preferences to open often searched locations.

### Removed
- Shortcut to reopen last blend without warning

### Fixed
- operator name to snake case
## [1.6.1] - 2021-07-05

### Added
- Added alternative functions to main button, instead of opening:
    - combine with `Ctrl` to copy _full path to file_ 
    - combine with `Shift` to copy _path to directory_ 
    - combine with `Alt` to copy _file name_


## [1.5.0] - 2021-05-18

### Added
- linux: now opening file also select pointed file (if nemo or nautilus filebrowser are found)

## [1.4.0] - 2021-05-13

### Added
- 2 new shortcuts:
    - `Ctrl + Alt+ Shift + O` Pop up a search in recent history to quickly find a previous to open.
    - `Ctrl + Alt+ Shift + P` Open last blend (revert if last in history is the current) !without warning!
- Addon preferences to customize/disable above keymaps
- Changelog file

### Changed
- Better open function:
    on windows : if pointing to a file, the opened directoy will select the file
- Heavy code refactor. Addon is now multifile
So install from zip or place entire folder in addon directory

### Fixed
- Buttons in file browser footer now work as expected
- UI: Open current folder button don't appear twice in top header anymore
now display only in top right corner



<!--
Added: for new features.
Changed: for changes in existing functionality.
Deprecated: for soon-to-be removed features.
Removed: for now removed features.
Fixed: for any bug fixes.
Security: in case of vulnerabilities.
-->