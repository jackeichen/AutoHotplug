## AutoHotplug is a disk auto-hotplug test script.


## Requirements
AutoHotplug requirements
* OS tools
  * java
  * python3
  * smartmontools
  * Linux tools are required:
    * nvme-cli
    * lsscsi
    * lsblk
* python3 modules
  * quarchpy
  * pyyaml
* Quarch Hardware
  * QTL2266-xx-xxx
  * QTL1999-xx-xxx
  * QTL1260-xx-xx kit

## Installing AutoHotplug
This is a script tool and Do Not need install,
Get it from https://github.com/jackeichen/AutoHotplug.git  \
Windows is not all the same as it was in Linux, you need install quarch device USB driver if 
you want connect in USB Mode.

## Running a test
    An example to test by Quarch control Kit:
    $ python3 HotPlug.py -i <Quarch Device ConnID>(Example usb:QTL2266-xx-xxx)
    
    An example to test by Manual:
    $ python3 HotPlug.py -i manual:<Disk ID> (Disk ID is just a ID, no more important significance, Disk SN is recommended)

## Log File
The log file included in "LOGS" driectory. Vdbench logs is in "LOGS/vdbenchoutput".

## Help Text

### HotPlug
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