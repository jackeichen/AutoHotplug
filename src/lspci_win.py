'''
Implements basic control over lspci utilities, so that we can identify and check the
status of PCIe devices on the host

########### VERSION HISTORY ###########

25/04/2018 - Andy Norrie	- First version

####################################
'''

import subprocess
import platform
import os
import re
import ctypes

from src.script_path import lspci_win_path as lspciPath

'''
Lists all PCIe devices on the bus
'''
def getPcieDevices(mappingMode):
    pcieDevices = []

    # Choose mapping mode to use
    if mappingMode == True:
        proc = subprocess.Popen([lspciPath, '-M'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        proc = subprocess.Popen([lspciPath], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Execute the process
    out, err = proc.communicate()
    out = out.decode("utf-8")
    err = err.decode("utf-8")
    # Handle error output
    if (err):
        print ("ERROR: " + err)

    # Add valid device lines to the list
    for pciStr in iter(out.splitlines ()):
        matchObj = re.match ('[0-9a-fA-F]+:[0-9a-fA-F]+.[0-9a-fA-F]', pciStr)
        try:
            matchStr = matchObj.group(0)
        except:
            matchStr = ""
        if (len(matchStr) > 0):
            if pciStr.find ('##') == -1:
                pcieDevices.append (pciStr)

    # Return the list
    return pcieDevices

'''
Checks if the specified device exists in the list
'''
def devicePresentInList (deviceList, deviceStr):
    for pciStr in deviceList:
        if deviceStr in pciStr:
            return True
    return False

'''
Returns the link status and speed of the device specified
'''
def getLinkStatus (deviceStr, mappingMode):
    if mappingMode == False:
        proc = subprocess.Popen([lspciPath, '-vv', '-s ' + deviceStr], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        proc = subprocess.Popen([lspciPath, '-M','-vv', '-s ' + deviceStr], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Execute the process
    out, err = proc.communicate()
    out = out.decode("utf-8")
    err = err.decode("utf-8")
    # Handle error output
    if (err):
        print ("ERROR: " + err)

    # Locate the link status section    
    strPos = out.find ('LnkSta:')    
    out = out[strPos:]

    # Get the link speed
    matchObj = re.search ('Speed (.*?),', out)
    linkSpeed = matchObj.group(0)
    # Get the link width
    matchObj = re.search ('Width (.*?),', out)
    linkWidth = matchObj.group(0)

    return linkSpeed, linkWidth

'''
Checks if the given device string is visible on the bus
'''
def devicePresent (deviceStr, mappingMode):
    # Get current device list
    deviceList = getPcieDevices (mappingMode)
    # Loop through devices and see if our module is there
    for pcieStr in deviceList:
        if deviceStr in pcieStr:
            return True
    return False

'''
Prompts the user to view the list of PCIe devices and select the one to work with
'''
def pickPcieTarget (deviceStr, mappingMode):
    
    # Get the curent devices
    deviceList = getPcieDevices (mappingMode)

    while devicePresentInList (deviceList, deviceStr) == False:
        print ("PCI Device was not specified")
        print ("Select from the detected Devices:")
        print ("")

        # Print the list of devices
        count = 0
        for pcieStr in deviceList:
            print (str(count) + ")  " + str(deviceList[count]))
            count = count + 1

        # Ask for selection
        selection = input('Enter a numerical selection and press enter: ')
        # exit on 'q'
        if "q" in selection:
            return 0
        # Validate selection
        if re.match ('[0-9]+', selection):
            if int(selection) < len(deviceList):
                deviceStr = deviceList[int(selection)]
                matchObj = re.match ('[0-9a-fA-F]+:[0-9a-fA-F]+.[0-9a-fA-F]', deviceStr)
                deviceStr = matchObj.group(0)

    # Return the device
    return deviceStr

'''
Checks if the script is runnin under admin permissions
'''
def checkAdmin():
    if platform.system() == 'Windows':
        if is_winAdmin () == False:
            print ("ERROR - Script required admin permissions to run!")
            quit ()
    else:
        if is_linuxAdmin () == False:
            print ("ERROR - Script required root permissions to run!")
            quit ()

'''
Checks for a windows admin user
'''
def is_winAdmin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

'''
Checks for a linux admin user
'''
def is_linuxAdmin():
    if os.getuid() == 0:
        return True
    else:
        return False


class PCIWinExLink(object):
    def __init__(self):
        self.cur_speed = "Dummy Value"
        self.cur_width = "Dummy Value"


class PCIWinLib(object):
    def __init__(self, device_name):
        self.device_name = device_name
        self.express_link = PCIWinExLink()
        
