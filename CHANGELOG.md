# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- ## [Unreleased] -->

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