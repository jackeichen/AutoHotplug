#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#Author: Gao Zhihua
#Date: 2018/03/29
import time
from abc import ABCMeta, abstractmethod

class PeripheryDevice(object):
    def __init__(self, periphery_name):
        self.__periphery_name = periphery_name
        self.periphery_device = None
        self.disk_info = []

    @property
    def periphery_name(self):
        return self.__periphery_name

    def get_disk_num(self):
        return len(self.disk_info)

    def close(self):
        if self.periphery_device:
            self.periphery_device.close()

    @abstractmethod
    def hotswapM_poweron(self):
        '''function to hot insert device'''

    @abstractmethod
    def hotswapM_poweroff(self):
        '''function to hot remove device'''

    @abstractmethod
    def hotswapM_power_status(self):
        '''function to get current power status'''

    @abstractmethod
    def periphery_identify(self):
        '''function to identify periphery'''

    @abstractmethod
    def periphery_test(self):
        '''function to periphery dedvice test'''


class QuarchDevice(PeripheryDevice):
    def __init__(self):
        super(QuarchDevice, self).__init__('quarch')

    def hotswapM_setup_delay_source(self,
                                    source1_delay,
                                    source2_delay,
                                    source3_delay,
                                    source4_delay=0,
                                    source5_delay=0,
                                    source6_delay=0,):
        self.periphery_device.set_source_delay(1,source1_delay)
        self.periphery_device.set_source_delay(2,source2_delay)
        self.periphery_device.set_source_delay(3,source3_delay)
        self.periphery_device.set_source_delay(4,source4_delay)
        self.periphery_device.set_source_delay(5,source5_delay)
        self.periphery_device.set_source_delay(6,source6_delay)

    def hotswapM_get_delay_source(self, source_index):
        if source_index.upper() == "ALL":
            temp = []
            for i in range(6):
                temp.append(self.periphery_device.get_source_delay(i+1))
            return temp
        else:
            return self.periphery_device.get_source_delay(source_index)

    def hotswapM_poweron(self):
        success = False
        for i in range(3):
            self.periphery_device.set_power_state("UP")
            ## wait device power on
            cycles = 10
            while cycles > 0:
                if self.hotswapM_power_status():
                    success = True
                    break
                time.sleep(0.1)
                cycles -= 1
            if success:
                return 0
        return 1

    def hotswapM_poweroff(self):
        success = False
        for i in range(3):
            self.periphery_device.set_power_state("DOWN")
            ## wait device power off
            cycles = 10
            while cycles > 0:
                if not self.hotswapM_power_status():
                    success = True
                    break
                time.sleep(0.1)
                cycles -= 1
            if success:
                return 0
        return 1

    def hotswapM_power_status(self):
        status = self.periphery_device.get_power_state()
        if status == 'PLUGGED':  # now power on 
            return 1
        elif status == 'PULLED': # now power off
            return 0
        else:
            raise RuntimeError("Bad descriptor!")

    def periphery_identify(self):
        return self.periphery_device.IDN()

    def periphery_test(self):
        return self.periphery_device.TST()


class ManualDevice(PeripheryDevice):
    def __init__(self):
        super(ManualDevice, self).__init__('manual')

    def hotswapM_poweron(self):
        success = False
        for i in range(3):
            self.periphery_device.set_power_state("UP")
            ## wait device power on
            cycles = 10
            while cycles > 0:
                if self.hotswapM_power_status():
                    success = True
                    break
                time.sleep(0.1)
                cycles -= 1
            if success:
                return 0
        return 1

    def hotswapM_poweroff(self):
        success = False
        for i in range(3):
            self.periphery_device.set_power_state("DOWN")
            ## wait device power off
            cycles = 10
            while cycles > 0:
                if not self.hotswapM_power_status():
                    success = True
                    break
                time.sleep(0.1)
                cycles -= 1
            if success:
                return 0
        return 1

    def hotswapM_power_status(self, retry=0, sleep=0.1):
        status = self.periphery_device.get_power_state()
        if status == 'PLUGGED':  # now power on 
            return 1
        elif status == 'PULLED': # now power off
            return 0
        else:
            raise RuntimeError("Bad descriptor!")

    def periphery_identify(self):
        return self.periphery_device._identify

    def periphery_test(self):
        return 0


'''
class QuarchDevicePool(object):
    def __init__(self):
        self.__device_pool = {}

    def get_dev_pool(self):
        return self.__device_pool

    def setup_devcie(self, quarch_module, disk_info=None, key=None):
        """Setup quarch QuarchDevStruc by key.
        
        Args:
            quarch_module: QuarchU2HotSwapModule object.
        
        Kwargs:
            disk_info: DiskInfo object
            key: the key that in device_pool, default None, which will be 
                 treated as disk_sn in the function.
        
        Returns: None
        Raises: TBD
        """
        quarch_dev = QuarchDevStruc()
        quarch_dev.quarch_hotswapM = quarch_module
        if disk_info:
            quarch_dev.disk_info = disk_info
        if key is None:
            key = quarch_module.ConnID
        if key in self.__device_pool:
            self.__device_pool[key].close()
        self.__device_pool[key] = quarch_dev
    
    def get_device(self, key):
        """Get quarch QuarchDevStruc by key.
        
        Args:
            key: the key that in device_pool
        
        Returns: QuarchDevStruc
        Raises: TBD
        """
        return self.__device_pool.get(key)
    
    def wait_disk_ready(self, key=None):
        if key is None:
            for key,quarch_dev in self.__device_pool.items():
                quarch_dev.wait_disk_ready()
        else:
            quarch_dev = self.__device_pool.get(key)
            if quarch_dev:
                quarch_dev.wait_disk_ready()
            else:
                raise RuntimeError("Key: %s not in device_pool" % key)
    
    def dump_in_test(self):
        dump_info = {}
        for key,quarch_dev in self.__device_pool.items():
            dump_info[key] = {}
            for _disk_info in quarch_dev.disk_info:
                intf = _disk_info.interface
                if intf == 'pcie':
                    disk_pci_config = _disk_info.disk_pci_config
                    dump_info[key][_disk_info.disk_id] = {"LinkSpeed": disk_pci_config.express_link.cur_speed,
                                                          "LinkWidth": disk_pci_config.express_link.cur_width}
                elif intf == 'sata':
                    dump_info[key][_disk_info.disk_id] = {"LinkSpeed": _disk_info.sata_speed[1]}
                elif intf == 'sas':
                    pass
        return dump_info
    
    def print_device_pool(self):
        print ("="*35)
        for key,quarch_dev in self.__device_pool.items():
            print ("Key: ", key)
            print ("")
            quarch_device = quarch_dev.quarch_hotswapM
            print (quarch_device.product_name())
            print (quarch_device.IDN())
            print ('')
            for disk_info in quarch_dev.disk_info:
                print ("Disk ID: ", disk_info.disk_id)
                print ("Disk Path: ", disk_info.disk_path)
                print ("Disk Name: ", disk_info.disk_name)
                print ("Disk SN: ", disk_info.disk_sn)
                print ("Disk Inf: ", disk_info.interface)
                print ("Disk Type: ", disk_info.disk_type)
                print ("Disk PCI-Link: ", disk_info.pci_links)
                disk_pci_config = disk_info.disk_pci_config
                if disk_pci_config:
                    print ("PCIe Link speed: ",disk_pci_config.express_link.cur_speed)
                    print ("PCIe Link width: ",disk_pci_config.express_link.cur_width)
                    print ("PCIe Power Slot: ",disk_info.get_pcie_power_slot())
                print ("")
            print ("-"*30)
        print ("="*35)
'''
