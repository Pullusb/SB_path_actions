# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- ## [Unreleased] -->

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
Added for new features.
Changed for changes in existing functionality.
Deprecated for soon-to-be removed features.
Removed for now removed features.
Fixed for any bug fixes.
Security in case of vulnerabilities.
-->