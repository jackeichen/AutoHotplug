AutoHotplug
===========
AutoHotplug is a disk auto-hotplug test script, and no need to install.


Support and Requirements
========================
AutoHotplug support bellow OS:
* Linux
* Windows

and support bellow Quarch device:
* QTL2266-xx-xxx (U.2 HotPlug Module)
* QTL1260-xx-xxx (Control Kit)

AutoHotplug requirements:
* OS tools
  * python3
  * java
  * smartmontools
  * Extra Linux tools are required:
    * nvme-cli
    * lsscsi
    * lsblk
  * Extra Windows tools are required:
    * wmic
    * PowerShell
    * Quarch USB Driver (When use Quarch->USB mode)
* python3 modules
  * quarchpy
  * pyyaml
  * Extra Windows modules are required:
    * wmi
* Quarch Hardware
  * QTL2266-xx-xxx
  * QTL1260-xx-xx kit


Installing AutoHotplug
======================
This is a script tool and Do Not need install,
Get it from https://github.com/jackeichen/AutoHotplug.git  \
Windows is not all the same as it was in Linux, you need install quarch device USB driver if 
you want connect Quarch device in USB Mode.


Running a test
==============
An example to test by Quarch control Kit:
```
$ python3 HotPlug.py -i <Quarch Device ConnID>(Example usb:QTL2266-xx-xxx)
```
    
An example to test by Manual:
```
$ python3 HotPlug.py -i manual:<Disk ID>
```
Disk ID is just a ID, no more important significance, Disk SN is recommended.


Configuration File
==================
The configuration files are included in "config" directory.


Log File
========
The log file included in "LOGS" directory. Vdbench logs is in "LOGS/vdbenchoutput".


Help Text
=========
HotPlug
-------
```
Usage: HotPlug.py [OPTION] or HotPlug.py [OPTION] [args...]

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -i CONN_ID, --ConnID=CONN_ID
                        Specify the HotPlug Module Connection IDs(like
                        usb:QTLxxx-xx-xxx), multi quarch with ','.
  -t, --test            Do not run actuall test, but do a tool test.
  --scan_quarch         Scan all quarch device and show them.
  --no_check            Do not check and run test anyway.
  --detail_quarch       Print quarch detail information.

```
