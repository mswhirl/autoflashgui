# AutoFlashGUI

Utility to inject commands and firmware upgrades via WebUI flaws of next-generation Technicolor gateways.

Please see [hack-technicolor.readthedocs.io](https://hack-technicolor.readthedocs.io) for the full guide for using the utility.

## Installation

The codebase requires Python 3.7 (on any OS) and pip; the following instructions
rely on you having the Python executables on your PATH.  If Python isn't
present on your PATH and you get a *not found* error, reference the
executables using their absolute paths.

The tool depends on the `robobrowser` and `Werkzeug` packages to be installed.  Either
you can install it ahead of time like so:

```
pip install robobrowser==0.5.3
pip install Werkzeug==0.16.1
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

AutoFlashGUI implements most common rooting strategies and is hereby described in detail. It has been tested working with some firmware's for various models. Unfortunately, most people gets root access on older firmware's then stop testing AutoFlashGUI on newer ones, so it's pretty difficult to maintain an updated list of tested firmware versions.

 | Model Number    | Mnemonic | ISP Product Names
 |:----------------|:---------|:--------------------------
 | TG797n v3       | DANT-O   | Telstra T-Gateway
 | TG789vac v2     | VANT-6   | -
 | TG789vac (v1)   | VANT-D   | -
 | TG799vac        | VANT-F   | Telstra Gateway Max
 | TG799vac        | VANT-R   | Telia Trådlös router
 | TG800vac        | VANT-Y   | Telstra Gateway Max 2
 | TG789vac v3     | VBNT-1   | -
 | TG799vac Xtream | VBNT-H   | -
 | DJN2130         | VBNT-J   | Telstra Frontier Gateway
 | TG789vac v2 HP  | VBNT-L   | MyRepublic WiFi Hub+
 | DJA0231         | VCNT-A   | Telstra Smart Modem Gen2

## Rooting example (Type 2)

In this example we will be working with the `VANT-F` Gateway on `16.3.7567` which is a `Type 2` firmware.

Using AutoFlashGUI, allow it to run through getting root. If you have changed any of the default settings (eg. Gateway IP, Web Interface Password), you must change the defaults in the AutoFlashGUI window. Leave "Flash firmware?" unchecked.

![AFG for Type 2](https://github.com/kevdagoat/hack-technicolor/raw/master/docs/images/autoflashgui_type2.png)

If you are unable to fill your profile correctly or AutoFlashGUI is not working, have a look on your local forums for detailed model-specific root commands. If you manage to find a root command not listed in AutoFlashGUI, create an issue and we will get it added in. Being a `Type 2` firmware, a working root guide surely exists.

Once AutoFlashGUI succeed, continue to [Final Type 2 steps](https://hack-technicolor.readthedocs.io/en/stable/Hack%20Type%201&2/#final-type-2-steps) on the wiki.

## Flashing example (Type 1)

Very similarly, you can use AutoFlashGUI to downgrade/upgrade a Type 1 image to another one. possibly of Type 2. In this case you need to check "Flash firmware?" option and pick a valid RBI to flash. This use case is better explained in the wiki for [rooting Type 1](https://hack-technicolor.readthedocs.io/en/stable/Hack%20Type%201&2/#type-1-flash-of-type-2-then-root) firmwares.

## Very old firmware compatibility issues

> My Firmware is so Old that AutoFlashGUI can't Authenticate!

*This is because they changed the web authentication method to SRPv6 with firmware v15, and this is the only method that the AutoFlashGUI tool knows how to authenticate with.*

You are going to have to flash a newer (let's say v16.3) RBI file via `sysupgrade` after using the original manual procedure to get a shell.

Go to *Advanced > Diagnostics*, and click on the *Ping & Traceroute* tab. (If your Gateway doesn’t display the Diagnostics tile, factory reset the Gateway. This only happens when the config is corrupted.) In the IP address section, enter your Gateway's IP and run:

```bash
:::::::;echo root:root | chpasswd; dropbear -p 6666;
```

Give it 30 seconds to generate SSH host keys and then try to SSH into your Gateway on port 6666 with root/root.

Copy the RBI to a USB stick (FAT32 formatted is most likely to work on old firmware) and insert it into the Gateway's USB port.

If you type `cd /mnt/` and keep hitting tab it should eventually get to the end of the USB stick path, then hit enter. (You can also run `mount` and try to work out the path the USB stick is mounted on.)

To be on the on the safe side we will copy the RBI to RAM, then flash it. Do the following with the correct RBI file name (keeping in mind that this is case sensitive):

```bash
cp filename.rbi /tmp
cd /tmp
sysupgrade filename.rbi
```

All things going well you should see it progress along and reboot, then you can run AutoFlashGUI normally.
