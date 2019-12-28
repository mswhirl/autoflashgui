# AutoFlashGUI forked for VANT-9 & VBNT-Z

**Still experimental - a work in progress...**
See: https://github.com/kevdagoat/hack-technicolor/issues/68
and: https://github.com/mswhirl/autoflashgui/issues/28

Utility to automate process to get ssh root access to Technicolor Vodafone Ultrahub (VANT-9) and Ultrahub plus (VBNT-Z) from New Zealand

Please see [hack-technicolor.readthedocs.io](https://hack-technicolor.readthedocs.io) for the full guide for using the utility.

## Installation

The codebase requires Python 3.7 (on any OS) and pip; the following instructions
rely on you having the Python executables on your PATH.  If Python isn't
present on your PATH and you get a *not found* error, reference the
executables using their absolute paths.

The tool depends on the `robobrowser` & `beautifulsoup4` packages to be installed.  Either
you can install it ahead of time like so:

```
pip install robobrowser==0.5.3
pip install beautifulsoup4
```
or else the code will fail to run.

## Running

To run the tool, do the following:

```
python autoflashgui.py
```

Keep the terminal or command prompt window it runs in visible; you'll need to
refer to this in case of errors and to know the progress.

## Compatibility


| Model Number    | Mnemonic | ISP Product Names
|:----------------|:---------|:--------------------------
| DGA0130VDF-NZ   | VANT-9   | Vodafone Ultrahub
| DNA0130VDF-NZ   | VBNT-Z   | Vodafone Ultrahub Plus
 
