#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#Author: Gao Zhihua
#Date: 2018/03/29
import os,sys
import time
import traceback
import platform
import re
import threading
import queue
from optparse import OptionParser
from src.log_hotplug import logger
from src.lib import run_cmd,win_cmd_exist
from src.periphery_device.quarchLib import scanDevices,listDevices
from src.hotplug_server import Server

sysstr = platform.system()
Version = '0.2.0'
##
cmd_exc_check = []

if sysstr == "Linux":
    cmd_exc_check = ["nvme", "lsblk", "lsscsi", "sg", "java"]
elif sysstr == "Windows":
    cmd_exc_check = ["wmic os /?", "PowerShell /?", "java -version"]

## os.linesep 
## os.altsep
class TaskDescription(object):
    def __init__(self):
        self.task_id = None
        self.args = []
        self.kwargs = {}
        self.except_rc = []


class HotPlug(Server):
    def __init__(self):
        super(HotPlug, self).__init__()
        ##
        self.__connID_mapping = {}
    
    def _check_env_1(self):
        info = 'Environment Check: ' + os.linesep
        info += ('OS: %s' % platform.system() + os.linesep)
        info += ('OS Ver: %s' % platform.platform() + os.linesep)
        ##pyt
        if sysstr == "Linux":
            nvme_version = None
            stdout = run_cmd('modinfo nvme', shell=True)
            for temp in stdout.split('\n'):
                if temp.lower().startswith('version'):
                    nvme_version = float(re.findall(r'-?\d+\.?\d*e?-?\d*?', temp)[0])   
            info += ('NVMe driver Ver: %s' % nvme_version + os.linesep)
        ## check needed tool
        for _cmd in cmd_exc_check:
            _cmd_lost = 0
            if sysstr == "Linux":
                rc = os.system("which %s > /dev/null" % _cmd)
                if rc:
                    logger.error("You may need to install %s first!" % _cmd)
                    _cmd_lost += 1
            elif sysstr == "Windows":
                rc = win_cmd_exist(_cmd)
                if not rc:
                    logger.error("You may need to install %s first!" % _cmd.split(" ")[0])
                    _cmd_lost += 1
            if _cmd_lost:
                logger.error("Lost %s tools, you may need to install os tool first!" % _cmd_lost)
                sys.exit(1)
        ## a simple check here
        if sysstr == "Linux":
            try:
                stdout = run_cmd('cat /proc/interrupts | grep pciehp', shell=True)
            except RuntimeError:
                info += ('OS Hotplug Capacity: False' + os.linesep)
            else:
                if stdout.strip():
                    info += ('OS Hotplug Capacity: True' + os.linesep)
                else:
                    info += ('OS Hotplug Capacity: False' + os.linesep)
        ##
        info += os.linesep
        logger.info(info)
    
    def _check_env_2(self):
        info += ('Support hotplug(Only for PCIe device) Slot that connect to:' + os.linesep)
        string_format = "%-30s  %-10s  %-15s"
        info += (string_format % ('SN','HotplugCap','HotPlugSurprise') + os.linesep)
        for k,v in self.hot_plug.disk_info_pool.get_disk_pool().items():
            cap = surprise = None
            a = v.pci_hotplug_cap
            b = v.pci_hotplug_surprise
            if a == 1:
                cap = "+"
            elif a == 0:
                cap = "-"
            if b == 1:
                surprise = "+"
            elif b == 0:
                surprise = "-"
            info += (string_format % (v.disk_sn, cap, surprise) + os.linesep)
        ##
        logger.info(info)
    
    def task0(self, ConnID, io_t):
        '''
        ## init the quarch with ConnID
        '''
        # start a therading
        client_id = self.start_one_client()
        # config threading
        request_id = 2
        request_data = [ConnID,          # quarch device ConnID
                        client_id,       # job id is always the same with client_id
                        io_t]            # io type, vdbench/FIO
        
        
        reply_db = self.REPQ(client_id, request_id, request_data=request_data)
        logger.info("Init client: ConnID->%s, client id->%s, tool version->%s" % (reply_db.reply_data[0],reply_db.reply_data[1],reply_db.reply_data[2]))
        self.__connID_mapping[ConnID] = client_id
        return reply_db.return_code
    
    def task1(self, ConnID):
        client_id = self.__connID_mapping[ConnID]
        ## first close hotplug
        request_id = 3
        self.REPQ(client_id, request_id)
        ## close all the client
        self.close_client(client_id)
    
    def task2(self, ConnID):
        '''
        Get the quarch device information and disk(connected to this quarch) information
        '''
        client_id = self.__connID_mapping[ConnID]
        request_id = 11
        reply = self.REPQ(client_id, request_id)
        print (reply.reply_data)
    
    def task3(self, ConnID):
        device_name = self.task8(ConnID)
        client_id = self.__connID_mapping[ConnID]
        if device_name == 'quarch':
            request_id = 12
            ##           test_id,test_cycles,quarch_source_delay
            ##            |__      ___|     _________|
            ##               |    |        |
            request_data = [[10, 10, [25,10,100,500]],
                            [0, 10, [25,10,100,500]],
                            [1, 10, [25,10,100,500]],
                            [2, 10, [25,10,100,500]],
                           ]
        elif device_name == 'manual':
            request_id = 14
            ##           test_id,test_cycles
            ##            |__      ___|    
            ##               |    |    
            request_data = [[10, 10],
                            [0, 10],
                            [1, 10],
                            [2, 10],
                           ]
        else:
            raise RuntimeError("Unmatched Periphery Device: %s" % device_name)
        self.send_request(client_id, request_id, request_data=request_data)
    
    def task4(self, ConnID):
        client_id = self.__connID_mapping[ConnID]
        # poll the result every 1s
        test_rc = None
        try:
            test_rc = self.recv_request(client_id, recv_timeout=1).reply_data
        except queue.Empty:
            pass
        return test_rc
    
    def task5(self, ConnID):
        '''
        tool test
        '''
        client_id = self.__connID_mapping[ConnID]
        request_id = 13
        reply = self.REPQ(client_id, request_id)
        print ("ConnID: %s" % ConnID)
        print ("Periphery Device Self Test: %s" % reply.reply_data[0])
        print ("IO test return code: %s" % reply.reply_data[1])
    
    def task6(self, ConnID):
        '''
        config IO job
        '''
        client_id = self.__connID_mapping[ConnID]
        request_id = 16
        cold_data = ['(0,5)', '(30,35)', '(95,100)']
        hot_data = ['(10,20)']
        request_data = [cold_data,None,hot_data]
        reply = self.REPQ(client_id, request_id, request_data=request_data)
    
    def task7(self, ConnID):
        '''
        config hot swap config
        '''
        client_id = self.__connID_mapping[ConnID]
        request_id = 5
        request_data = [0,          # hot_pull_type
                        None,       # hot_pull_para
                        0,          # hot_push_type
                        None,       # hot_push_para
                        10,         # off_time
                        30,         # on_time
                       ]
        reply = self.REPQ(client_id, request_id, request_data=request_data)

    def task8(self, ConnID):
        '''
        Get Periphery Device Name
        '''
        client_id = self.__connID_mapping[ConnID]
        request_id = 6
        reply = self.REPQ(client_id, request_id)
        return reply.reply_data[0]


def main():
    usage="usage: %prog [OPTION] or %prog [OPTION] [args...]"
    parser = OptionParser(usage,version="HotPlug " + Version)
    parser.add_option("-i", "--ConnID", dest="conn_id", action="store", type=str, default='',
            help="Specify the HotPlug Module Connection IDs(like usb:QTLxxx-xx-xxx), multi quarch with ','.")
    parser.add_option("-t", "--test", dest="tool_test", action="store_true", default=False,
            help="Do not run actuall test, but do a tool test.")
    parser.add_option("", "--scan_quarch", dest="scan_quarch", action="store_true", default=False,
            help="Scan all quarch device and show them.")
    parser.add_option("", "--no_check", dest="no_check", action="store_true", default=False,
            help="Do not check and run test anyway.")
    parser.add_option("", "--detail_quarch", dest="detail_quarch", action="store_true", default=False,
            help="Print quarch detail information.")
    ####
    (options, args) = parser.parse_args()
    if options.scan_quarch:
        foundDevices = scanDevices()
        listDevices(foundDevices)
        sys.exit()
    ## check if given
    if options.conn_id:
        conn_ids = options.conn_id
        conn_ids = conn_ids.split(',')
    else:
        parser.error("parameter -i/--ConnID required")
    if options.detail_quarch:
        print ("TO Do Functions(TBD).")
        sys.exit()
    hot_plug = HotPlug()
    hot_plug._check_env_1()
    ##
    while (not options.no_check):
        answer = input("Please check above Env, and ensure yor DUT support hot-plug(y/n): ")
        if answer.lower() == 'y' or answer.lower() == 'yes':
            break
        elif answer.lower() == 'n' or answer.lower() == 'no':
            sys.exit()
        else:
            continue
    ###
    ## first setup quarch
    tested_ids = []
    for conn_id in conn_ids:
        if hot_plug.task0(conn_id, "vdbench") == 0:
            tested_ids.append(conn_id)
    ## check the threading config
    for conn_id in tested_ids:
        hot_plug.task2(conn_id)
    ###
    if options.tool_test:
        for conn_id in tested_ids:
            hot_plug.task5(conn_id)
    else:
        ### main test
        ## config IO
        for conn_id in tested_ids:
            hot_plug.task6(conn_id)
            hot_plug.task7(conn_id)
        ## run test
        # start send non_block request
        for conn_id in tested_ids:
            hot_plug.task3(conn_id)
        # and then pool the recv queue
        while (tested_ids):
            for conn_id in tested_ids:
                test_rc = hot_plug.task4(conn_id)
                if test_rc is not None:
                    logger.info("ConnID %s finish test, test return code=%s" % (conn_id,test_rc))
                    tested_ids.remove(conn_id)
    ## close them
    for conn_id in conn_ids:
        hot_plug.task1(conn_id)
    sys.exit()

#Calling the main() function
if __name__=="__main__":
    main()
