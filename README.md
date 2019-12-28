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

Set your PC to static IP 192.168.1.100. This will be used as the server IP for the http call-back from the router to collect the shell script to do the magic. If you're on Windows, ensure you run as Administrator, allow python to open port 8000, and you may need to disable Windows firewall...

To run the tool, do the following:

```
python autoflashgui.py
```

Keep the terminal or command prompt window it runs in visible; you'll need to
refer to this in case of errors and to know the progress.

## Compatibility


| Model Number    | Mnemonic | ISP Product Names         | Firmware Version
|:----------------|:---------|:--------------------------|:--------------------------
| DGA0130VDF-NZ   | VANT-9   | Vodafone Ultrahub | 17.1.7988-2461009-CRF846-V2.4.6
| DNA0130VDF-NZ   | VBNT-Z   | Vodafone Ultrahub Plus | 17.4.0182-0841014-20180413074043
 
## Firmware Downloads
You can grab a copy of a compatible firmware file from here. These files are over the 25MB limit for github so are hosted elsewhere:
Vodafone Ultrahub Plus VBNT-Z

http://downloads.vodafone.co.nz/ultrahub-plus/UHP-2-0-1-Prod.rbi
https://drive.google.com/uc?export=download&id=1fI971apBMPDv7-czSh6yEnH5e1ZQDj4S

Vodafone Ultrahub VANT-9

17.1.7988-2461009-20180510014336-RC2.4.6_prod_AUTH_vant-9
https://drive.google.com/uc?export=download&id=11ncIoTOvrUrIy2LQ4GA42b1gUeWJq_Li

## Firmware Downgrade Process
Its likely that your router will be on a newer firmware version that doesnt have the DDNS bug. So you may need to downgrade. AFAIK you have to do the downgrade using the TFTP process described here (because downgrading through the regular webUI isn't allowed): https://hack-technicolor.readthedocs.io/en/stable/Recovery/#set-up-tftp

If you try the TFTP process and it seems to flash, but the router starts up with a different firmware version than you were expecting, then you need to do a Bank Switch, and then re-flash with TFTP:
To Bank Switch, simply use webUI to re-flash the same firmware version that it is already running. After it reboots, it will be running on Bank_1, which can be flashed by the TFTP process above.

https://hack-technicolor.readthedocs.io/en/stable/Recovery/#set-up-tftp
