# autoflashgui

Utility to flash firmware to modems and run setup commands after the flash has completed

## Installation

The codebase requires Python 3.6 (on any OS) and pip; the following instructions
rely on you having the Python executables on your PATH.  If Python isn't
present on your PATH and you get a *not found* error, reference the
executables using their absolute paths.

The tool depends on the `robobrowser` package to be installed.  Either
you can install it ahead of time like so:

```
pip install robobrowser==0.5.3
```

or else the code will fail to run.

## Running

To run the tool, do the following:

```
python autoflashgui.py
```

Keep the terminal or command prompt window it runs in visible; you'll need to
refer to this in case of errors and to know the progress.
