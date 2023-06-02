#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#Author: Gao Zhihua
#Date: 2018/03/29
import sys,os,platform
import time
sysstr = platform.system()
if sysstr == "Windows":
    import wmi
    import pythoncom
import json
import threading
import traceback

from src.lib import subprocess,run_cmd
from src.pci_lib import map_pci_device
#from src.DiskpartWrapper.WinDiskpartWrapper import WindowsDiskUtility
from src.script_path import devcon_path
from src.log_hotplug import logger
##
MaxDiskPoolGetCycle = 3
SomeTempValue = {"PS_GetPhysicalDisk": None}

def PSGetPhysicalDisk():
    stdout = run_cmd(["Powershell", "Get-PhysicalDisk"])
    stdout = stdout.split("\r\n")
    while '' in stdout:
        stdout.remove('')
    return stdout


class DiskInfoError(Exception):
    pass


class Com(object):
    def __init__(self):
        self.need_com_init = not self._is_main_thread()

    def _is_main_thread(self):
        return threading.current_thread().name == 'MainThread'

    def __enter__(self):
        if self.need_com_init:
            logger.debug("Initializing COM library")
            pythoncom.CoInitialize()

    def __exit__(self, exc_type, exc_value, traceback):
        if self.need_com_init:
            logger.debug("Uninitializing COM library")
            pythoncom.CoUninitialize()


class DiskInfo(object):
    def __init__(self):
        self.__disk_path = ''
        self.__interface = ''
        self.__disk_sn = ''
        self.__disk_id = ''
        self.__disk_type = ''
        self.__pci_links = ''
        self.__sata_speed = None
        self.__scsi_host_id = ''
        self.__pcie_power_slot = ''
        ##
        self.__linux_path_prefix = "/dev/"
        self.__win_path_prefix = "\\\\.\\PHYSICALDRIVE"
        ##
        self.__win_wmi_obj = None
    
    def set_win_wmi_obj(self, value):
        if isinstance(value, wmi._wmi_object):
            self.__win_wmi_obj = value
        else:
            raise DiskInfoError("You need set a wmi._wmi_object.")
    
    def wait_device_ready(self, cycles=60,interval=1):
        if sysstr == 'Linux':       
            for i in range(cycles):
                if os.path.exists(self.__disk_path):
                    return 0
                else:
                    time.sleep(interval)
        elif sysstr == 'Linux':
            cmd = ["wmic", "diskdrive"]
            for i in range(cycles):
                stdout = run_cmd(cmd)
                if self.__disk_path in stdout:
                    return 0
                else:
                    time.sleep(interval)
        return 1
    
    @property
    def win_wmi_obj(self):
        if isinstance(self.__win_wmi_obj, wmi._wmi_object):
            return self.__win_wmi_obj
        else:
            # rescan by disk path
            pass
    
    def _check_disk_path(self):
        if self.__disk_path and (self.__linux_path_prefix in self.__disk_path or "PHYSICALDRIVE" in self.__disk_path):
            return True
        raise DiskInfoError("No disk path now")
    
    def get_interface(self):
        """
        disk interface: sata/sas/pcie 
        """
        if sysstr == "Linux":
            stdout = run_cmd(["lsscsi", "-t"], check_stderr=False)
            stdout = stdout.split("\n")
            #
            for i in stdout:
                if self.disk_path in i:
                    if "sata" in i:
                        return "sata"
                    elif "sas" in i:
                        return "sas"
                    elif "pcie" in i:
                        return "pcie"
                    else: # it may be through a raid card, before it you need make jbod in the raid
                        # detect if sata
                        try:
                            stdout = run_cmd(["sg_sat_identify", self.disk_path])
                        except:
                            # detect if sas
                            try:
                                stdout = run_cmd(["sg_inq", self.disk_path])
                            except:
                                print ("No interface detected!")
                            else:
                                return "sas"
                        else:
                            return "sata"
            # it maybe nvme disk
            # check here
            stdout = run_cmd(["nvme", "list", "-o", "json"])
            stdout = json.loads(stdout)
            stdout = stdout.get("Devices")
            for i in stdout:
                if self.disk_path == i.get("DevicePath"):
                    return "pcie"
        elif sysstr == "Windows":
            if "NVME" in self.win_wmi_obj.PNPDeviceID:
                return "pcie"
            else:
                return "sata"
        raise DiskInfoError("Cannot detect inetrface type")        

    def get_disk_sn(self):
        self._check_disk_path()
        if sysstr == "Linux":
            stdout = run_cmd(["lsblk", "-d", "-n", "-o", "KNAME,SERIAL"])
            stdout = stdout.split("\n")
            ##
            for i in stdout:
                index = i.find(" ")
                if index > 0:
                    disk_name = i[0:index].strip()
                    disk_sn = i[(index+1):].strip()
                    if disk_name == self.disk_name:
                        return disk_sn
        elif sysstr == "Windows":
            return self.win_wmi_obj.SerialNumber
    
    def get_disk_id(self):
        if sysstr == "Windows":
            return self.disk_sn
        elif self.interface == 'pcie':
            stdout = run_cmd(["nvme", "id-ns", self.disk_path, "-o", "json"])
            stdout = json.loads(stdout)
            return stdout.get("nguid")
        return self.disk_sn
    
    def get_disk_type(self):
        """
        disk type: HDD,SSD
        """
        if sysstr == "Linux":
            stdout = run_cmd(["lsblk", "-d", "-n", "-o", "KNAME,ROTA"])
            stdout = stdout.split("\n")
            disk_name = self.disk_name
            for i in stdout:
                if disk_name in i:
                    rota = i.replace(disk_name, "")
                    if "0" in rota:
                        return "SSD"
                    elif "1" in rota:
                        return "HDD"
        elif sysstr == "Windows":
            tmp = SomeTempValue.get("PS_GetPhysicalDisk")
            if not tmp:
                tmp = PSGetPhysicalDisk()
            for i in tmp:
                if self.disk_sn in i:
                    if "SSD" in i:
                        return "SSD"
                    elif "HDD" in i:
                        return "HDD"
                    else:
                        raise DiskInfoError("Unknown Disk MediaType")
            raise DiskInfoError("Cannot detect disk type")    
    
    def get_pci_links(self):
        if sysstr == "Linux":
            
            stdout = run_cmd(["readlink", "-f", "/sys/block/%s" % self.disk_name])
            if stdout:
                stdout = stdout.split("/")
                # remove all ''
                while '' in stdout:
                    stdout.remove('')
                intf = self.interface
                if intf == "sata" or intf == "sas":
                    return stdout[3:-2]
                elif intf == "pcie":
                    if stdout[3].startswith("pci"):
                        return stdout[3:-3]
                    else:
                        temp = self.disk_name.lstrip("nvme")
                        i = temp.find("n")
                        temp = "nvme%s" % temp[0:i]
                        stdout = run_cmd(["readlink", "-f", "/sys/class/nvme/%s" % temp])
                        stdout = stdout.split("/")
                        return stdout[3:-2]
            else:
                raise DiskInfoError("readlink command error")
        elif sysstr == "Windows":
            ## TODO, windows should not use it, so igive it a dummy value
            return ["PCIROOT(0)", "PCI(1700)", "RAID(P03T00L00)"]
    
    def get_sata_speed(self):
        """
        Return:
            MaxSpeed,CurrentSpeed
        """
        if sysstr == "Linux" and self.interface == 'sata':
            p = subprocess.Popen(["sg_sat_identify", '-r', self.disk_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (stdout, stderr) = p.communicate()
            if p.returncode == 0 and stdout:
                current_speed = ((stdout[154] & 0x0E) >> 1)
                support_speed = ((stdout[152] & 0x0E) >> 1)
                max_speed = 0
                if support_speed == 7:
                    max_speed = 3
                elif support_speed == 3:
                    max_speed = 2
                elif support_speed == 1:
                    max_speed = 1
                return max_speed,current_speed
            else:
                print ("Run command error")
        elif sysstr == "Windows":
            ## TODO, it's a dumy value
            return 3,3
    
    def get_pcie_power_slot(self):
        ## only for linux pcie device
        slot = None
        if self.interface == 'pcie':
            pcie_addr = self.pci_links[-1]
            if sysstr == "Linux" and pcie_addr:
                power_slot_dir = "/sys/bus/pci/slots/"
                for root,dirs,files in os.walk(power_slot_dir, topdown=False):
                    if 'address' in files:
                        addr = os.path.join(root, 'address')
                        with open(addr, 'r') as f:
                            temp = f.read()
                        temp = temp.strip()
                        if temp in pcie_addr:
                            slot = os.path.join(root, 'power')
                            break
                return slot
    
    def get_scsi_host_id(self):
        intf = self.interface
        if sysstr == "Linux":
            if intf == "sata" or intf == "sas":
                for i in self.pci_links:
                    if "host" in i:
                        return i
    
    def set_device_power(self, power='off'):
        if sysstr == "Linux":
            if self.interface == 'pcie':
                ## ensure disk exist
                if os.path.exists(self.disk_path):
                    if not self.__pcie_power_slot:
                        logger.error("Invalid power slot.")
                    elif not os.path.isfile(self.__pcie_power_slot):
                        logger.warning("Disk Power slot Not exist, you may set it power off in other function.")
                    else:
                        if power.lower() == 'off':
                            os.system("echo 0 > %s" % self.__pcie_power_slot)
                        elif power.lower() == 'on':
                            os.system("echo 1 > %s" % self.__pcie_power_slot)
                        else:
                            raise DiskInfoError("power should be off|on")
                else:
                    logger.warning("Disk path Not exist, you may set it power off in other function.")
            else:
                if power == "off":
                    addr = "/sys/block/%s/device/delete" % self.disk_name
                    if os.path.exists(addr):
                        os.system("echo 1 > %s" % addr)
                    else:
                        # ToDo
                        raise DiskInfoError("No %s exists" % addr)
                else:
                    addr = "/sys/class/scsi_host/%s/scan" % self.__scsi_host_id
                    if os.path.exists(addr):
                        os.system('echo "- - -" > %s' % addr)
                    else:
                        raise DiskInfoError("No %s exists" % addr)
        elif sysstr == "Windows":
            logger.warning("Not support notify poweroff in windows now")
            '''
            # get disk ids
            stdout = run_cmd([devcon_path, "hwids", "*disk*"])
            stdout = stdout.split("/r/n")
            
            ## TODO, based on devcon
            PNPDeviceID = self.win_wmi_obj.PNPDeviceID.replace("&", "^&")
            cmd = "%s remove %s" % (devcon_path,PNPDeviceID)
            #os.system(cmd)
            '''
    
    @property
    def disk_path(self):
        return self.__disk_path
    
    @disk_path.setter
    def disk_path(self, value):
        self.__disk_path = value
        self._check_disk_path()
        # get disk interface
        self.__interface = self.get_interface()
        # get disk sn
        self.__disk_sn = self.get_disk_sn()
        # get disk disk_id
        self.__disk_id = self.get_disk_id()
        # disk type: HDD,SSD
        self.__disk_type = self.get_disk_type()
        #
        self.__pci_links = self.get_pci_links()
        # 
        if self.__interface == 'sata':
            self.__sata_speed = self.get_sata_speed()
        #
        if self.__interface == 'sata' or self.__interface == 'sas':
            self.__scsi_host_id = self.get_scsi_host_id()
        elif self.__interface == 'pcie':
            self.__pcie_power_slot = self.get_pcie_power_slot()
    
    @property
    def disk_name(self):
        self._check_disk_path()
        if sysstr == "Linux":
            return self.__disk_path.lstrip(self.__linux_path_prefix)
        elif sysstr == "Windows":
            return self.__disk_path.split("PHYSICALDRIVE")[1].strip()
        else:
            raise DiskInfoError("No support OS(%s)" % sysstr)
    
    @disk_name.setter
    def disk_name(self, value):
        if value:
            if sysstr == "Linux":
                disk_path = self.__linux_path_prefix+value
                if os.path.exists(disk_path):
                    self.disk_path = disk_path
                else:
                    raise DiskInfoError("No support device path(%s)" % disk_path)
            elif sysstr == "Windows":
                disk_path = self.__win_path_prefix + value
                self.disk_path = disk_path
            else:
                raise DiskInfoError("No support OS(%s)" % sysstr)
        else:
            raise DiskInfoError("Value should exist")
    
    @property
    def interface(self):
        return self.__interface
    
    @property
    def disk_sn(self):
        return self.__disk_sn
    
    @property
    def disk_id(self):
        return self.__disk_id
    
    @property
    def top_device_id(self):
        return self.disk_sn
    
    @property
    def disk_type(self):
        """
        disk type: HDD,SSD
        """
        return self.__disk_type     

    @property
    def pci_links(self):
        return self.__pci_links
        
    @property
    def disk_pci_config(self):
        if sysstr == "Linux" and self.interface == "pcie":
            return map_pci_device(self.pci_links[-1])
        elif sysstr == "Windows" and self.interface == "pcie":
            from src.lspci_win import PCIWinLib
            return PCIWinLib(self.pci_links[-1])

    @property
    def sata_speed(self):
        """
        Return:
            MaxSpeed,CurrentSpeed
        """
        return self.__sata_speed

    @property
    def pci_hotplug_cap(self):
        # check parent capacity
        if sysstr == "Linux":
            if self.interface == 'pcie':
                parent = self.disk_pci_config.parent
                return parent.express_slot.hot_plug_cap
        elif sysstr == "Windows":
            return "Unkonwn"

    @property
    def pci_hotplug_surprise(self):
        # check parent capacity
        if sysstr == "Linux":
            if self.interface == 'pcie':
                parent = self.disk_pci_config.parent
                return parent.express_slot.hot_plug_surprise
        elif sysstr == "Windows":
            return "Unkonwn"


class DiskInfoPool(object):
    '''
    Need tool:
      * sg3_util
      * nvme-cli
      * lsblk
      * lsscsi
    SATA/SAS/NVMe disk support.

    '''
    def __init__(self):
        self.__disk_pool = {}
        #
        self.scan_disk()
    
    @property
    def disk_pool(self):
        """
        priority to use this function.
        
        """
        return self.__disk_pool
    
    def scan_disk(self):
        self.__disk_pool = {}
        if sysstr == "Linux":
            ## Get all disk and disk path and SN
            for i in range(100):
                stdout = run_cmd(["lsblk", "-d", "-n", "-o", "KNAME"])
                stdout = stdout.split("\n")
                for i in stdout:
                    temp = i.strip()
                    if temp:
                        try:
                            disk_info = DiskInfo()
                            disk_info.disk_name = temp
                            self.__disk_pool[disk_info.disk_id] = disk_info
                        except DiskInfoError:
                            continue
                        except:
                            logger.debug("Some disk status abnormal, rescan")
                            time.sleep(0.1)
                            break
                else:
                    break
            else:
                raise RuntimeError("Error when rescan disk!")
                
        elif sysstr == "Windows":
            with Com():
                diskScan = wmi.WMI()
                #
                SomeTempValue["PS_GetPhysicalDisk"] = PSGetPhysicalDisk()
                #
                for disk_wmi in diskScan.Win32_diskdrive():
                    try:
                        disk_info = DiskInfo()
                        try:
                            disk_info.set_win_wmi_obj(disk_wmi)
                            disk_info.disk_path = disk_wmi.DeviceID
                        except:
                            pass
                        else:
                            self.__disk_pool[disk_info.disk_id] = disk_info
                    except DiskInfoError:
                        print (traceback.format_exc())
                        continue
