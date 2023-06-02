#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#Author: Gao Zhihua
#Date: 2018/03/29
import time
from quarchpy import *
from quarchpy.device.scanDevices import scanDevices,listDevices


class QuarchDeviceBase(object):
    '''
    arg:
      ConnID: Specifies the device to connect to by COM port, IP address or USB ID
    '''
    def __init__(self, ConnID):
        self.ConnID = ConnID
        self.device = None
    
    def __del__(self):
        if self.device:
            self.close()
    
    def open(self):
        if self.device is None:
            self.device = quarchDevice(self.ConnID)
            return 0
        else:
            print ("You should close the connection before start a new one")
            return 1
    
    def close(self):
        self.device.closeConnection()
        self.device = None
    
    def send_cmd(self, cmd):
        return self.device.sendCommand(cmd)
    
    def product_name(self):
        temp = self.send_cmd("hello?")
        return temp
        
        
class QuarchU2HotSwapModule(QuarchDeviceBase):
    def __init__(self, ConnID):
        super(QuarchU2HotSwapModule, self).__init__(ConnID)
        self.open()

    def RST(self):
        return self.send_cmd("*RST")

    def IDN(self, output="string"):
        temp = self.send_cmd("*IDN?")
        if output == "format_out":
            _temp = temp.split('\r\n')
            temp = {}
            for i in _temp:
                index = i.find(":")
                if index > 0:
                    temp[i[0:index].strip()] = i[(index+1):].strip()
        return temp

    def TST(self):
        temp = self.send_cmd("*TST?")
        if temp == "OK":
            return 0
        else:
            print ("Quarch device Error Occur:")
            print (temp)
            return 1

    def get_config_messages(self):
        return self.send_cmd("CONFig:MESSages?")

    def get_12v_vol(self, locate):
        if locate in ("12vin","12vout","12vin_chg","12vout_chg"):
            return self.send_cmd("MEASure:VOLTage %s?" % locate)
        else:
            print ("Locate should be 12vin|12vout|12vin_chg|12vout_chg")

    def _check_source_delay_para(self, source_index=None, delay=None, unit=None):
        rc = 0
        if source_index:
            if source_index not in (1,2,3,4,5,6,'ALL'):
                rc += 1
                print("source index should be [1-6|ALL]")
        if delay:
            if isinstance(delay, int) and (delay >= 0):
                if delay > 127:
                    if (delay % 10) != 0:
                        rc += 1
                        print("delay value should be in steps of 10ms when > 127!")
            else:
                rc += 1
                print("delay value should be a positive integer!")
        if unit:
            if unit not in ("uS", "mS", "S"):
                rc += 1
                print("unit value should be a [uS|mS|S]")
        return rc

    def get_source_delay(self, source_index):
        self._check_source_delay_para(source_index=source_index)
        return self.send_cmd("SOURce:%s:DELAY?" % source_index)

    def set_source_delay(self, source_index, delay, unit=None):
        self._check_source_delay_para(source_index, delay, unit)
        if not unit:
            unit = ''
        cmd = "SOURce:%s:DELAY %s %s" % (source_index, delay, unit)
        cmd = cmd.strip()
        self.send_cmd(cmd)

    def get_power_state(self):
        return self.send_cmd("RUN:POWer?")

    def set_power_state(self, state):
        if state not in ("UP","DOWN"):
            print ("Set power state should in UP|DOWN")
            return 1
        self.send_cmd("RUN:POWer %s" % state)

    def run_hot_swap(self, off_time):
        self.set_power_state("DOWN")
        time.sleep(off_time)
        self.set_power_state("UP")


QuarchDeviceClass = {
    "QTL2266": QuarchU2HotSwapModule,
    "QTL1999": None,
    "QTL2207": QuarchU2HotSwapModule,
    }

def get_quarch_module(ConnID):
    for _id,v in QuarchDeviceClass.items():
        if _id in ConnID:
            return v(ConnID)
    raise RuntimeError("No correctable Quarch ConnID input.")


