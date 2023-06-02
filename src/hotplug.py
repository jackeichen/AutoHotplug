#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#Author: Gao Zhihua
#Date: 2018/03/29
import threading
import traceback
import platform
sysstr = platform.system()
import time
import random
from src.disk_info import DiskInfoPool
from src.vdbench.VDBenchJob import VDBenchJob
from src.periphery_device.periphery_device import QuarchDevice,ManualDevice
from src.periphery_device.quarchLib import get_quarch_module
from src.periphery_device.manualLib import get_manual_module
from src.log_hotplug import logger
from src.lib import localtime


def run_test_decorator(func):
    def wrapper(*args,**kwargs):
        logger.info("#"*50)
        logger.info("%s start at: %s" % (func.__name__,localtime()))
        try:
            rc = func(*args,**kwargs)
        except:
            logger.error(traceback.format_exc())
            rc = 201
        if rc:
            logger.error("Test FAIL")
        else:
            logger.info("Test PASS")
        logger.info("%s finish at: %s" % (func.__name__,localtime()))
        logger.info("#"*50)
        return rc
    return wrapper


class HotSwapConfig(object):
    """
    hot_pull_type: 
      value                Description
      0                    All thread do their own hot pull separately
      1                    All thread do the hot pull at the same time
      2                    Only one thread do hot pull in a hot pull process(hot pull and disk disappear)
      3                    All thread do the hot pull step by step with specific time(second)
      4                    All thread do the hot pull step by step after another hot pull success(interval time based that the disk rescan interval time)
    
    hot_push_type: 
      value                Description
      0                    All thread do their own hot push separately
      1                    All thread do the hot push at the same time
      2                    All thread do the hot push step by step after another hot push success(interval time based that the disk rescan interval time)
      3                    All thread do the hot push step by step with specific time(second)
    """
    def __init__(self):
        self.hot_pull_type = 0
        self.hot_pull_para = []
        self.hot_push_type = 0
        self.hot_push_para = []
        self.off_time = 10 # off time that between hot pull and hot push
        self.on_time = 30  # now only No IO will perform the sleep time


class HotPlugBase(object):
    def __init__(self, job_id, shared_info, periphery_device):
        self._periphery_device = periphery_device
        self._job_id = job_id
        self._shared_info = shared_info
        ##
        self.disk_info_pool = DiskInfoPool()
        ##
        self.io_jobs = None
        # IO config
        self.__io_hot_data_range = []
        self.__io_cold_data_range = []
        self.__io_cold_data_prepare_flag = False
        ## hot swap config
        self.hot_swap_config = HotSwapConfig()

    @property
    def _io_hot_data_range(self):
        return self.__io_hot_data_range

    @property
    def _io_cold_data_range(self):
        return self.__io_cold_data_range

    @property
    def _io_cold_data_prepare_flag(self):
        return self.__io_cold_data_prepare_flag

    @_io_cold_data_prepare_flag.setter
    def _io_cold_data_prepare_flag(self, value):
        if value in (True, False):
            self.__io_cold_data_prepare_flag = value    

    @property
    def periphery_device_name(self):
        return self._periphery_device.periphery_name

    def setup_periphery_device(self):
        ##
        logger.info("setup periphery device: %s" % self._periphery_device.periphery_name)
        ## when setup quarch dev, just one thread do
        with self._shared_info.get("RLockHotSwap"):
            # get old disk info
            self.disk_info_pool.scan_disk()
            old_disk = self.disk_info_pool.disk_pool.keys()
            ## get the correct disk
            if self._periphery_device.hotswapM_power_status() == 1:  # now power on 
                # we will shutdown the quarch and check which disks disappear
                self._periphery_device.hotswapM_poweroff()
                differ = self._wait_somedisk_disappear(old_disk)
                if differ:
                    # disk should not perform very fast hot-swap, in case of disk hang
                    time.sleep(3)
                    # open the connection again
                    self._periphery_device.hotswapM_poweron()
                    if self._wait_device_appear_by_ids(differ):
                        raise RuntimeError("Cannot detect correct Disk info")
                    ## take multi-namespace into consideration
                    for disk_id in differ:
                        self._periphery_device.disk_info.append(self.disk_info_pool.disk_pool.get(disk_id))
                else:
                    logger.critical("Cannot identidy disks correct to the periphery device, please check your device status Or reset the periphery device")
                    self._periphery_device.close()
                    raise RuntimeError("Cannot detect Disk")
            elif self._periphery_device.hotswapM_power_status() == 0: # now power off
                self._periphery_device.hotswapM_poweron()
                differ = self._wait_somedisk_appear(old_disk)
                if differ:
                    for disk_id in differ:
                        self._periphery_device.disk_info.append(self.disk_info_pool.disk_pool.get(disk_id))
                else:
                    logger.critical("Cannot identidy disks correct to the periphery device, please check your device status Or reset the periphery device")
                    self._periphery_device.close()
                    raise RuntimeError("Cannot detect Disk")

    def close_periphery_device(self):
        self._periphery_device.close()

    #
    def _wait_device_disappear_by_id(self, dev_id, total_cycles=10, intervals=3):
        for i in range(total_cycles):
            self.disk_info_pool.scan_disk()
            if dev_id not in self.disk_info_pool.disk_pool.keys():
                break
            else:
                time.sleep(intervals)
        else:
            print ("Disk not disappear")
            return 1
        return 0

    def _wait_device_disappear_by_ids(self, dev_ids, total_cycles=10, intervals=3):
        for i in range(total_cycles):
            self.disk_info_pool.scan_disk()
            for dev_id in dev_ids:
                if dev_id in self.disk_info_pool.disk_pool.keys():
                    break
            else:
                break
            time.sleep(intervals)
        else:
            print ("Disk not disappear")
            return 1
        return 0 

    def _wait_device_appear_by_id(self, dev_id, total_cycles=10, intervals=3):
        for i in range(total_cycles):
            self.disk_info_pool.scan_disk()
            if dev_id in self.disk_info_pool.disk_pool.keys():
                break
            else:
                time.sleep(intervals)
        else:
            print ("Disk not appear")
            return 1
        return 0

    def _wait_device_appear_by_ids(self, dev_ids, total_cycles=10, intervals=3):
        for i in range(total_cycles):
            self.disk_info_pool.scan_disk()
            for dev_id in dev_ids:
                if dev_id not in self.disk_info_pool.disk_pool.keys():
                    break
            else:
                break
            time.sleep(intervals)
        else:
            print ("Disk not appear")
            return 1
        return 0

    def _wait_disk_appear_by_top_id(self, top_dev_id, wait_num,total_cycles=10, intervals=3):
        def get_e_num(l):
            num = 0
            for i in l:
                if i == top_dev_id:
                    num += 1
            return num
        for i in range(total_cycles):
            self.disk_info_pool.scan_disk()
            temp = [_disk_info.top_device_id for _disk_info in self.disk_info_pool.disk_pool.values()]
            if top_dev_id in temp and (get_e_num(temp) == wait_num):
                break
            else:
                time.sleep(intervals)
        else:
            print ("%s not appear" % top_dev_id)
            return 1
        return 0

    def _wait_disk_disappear_by_top_id(self, top_dev_id, total_cycles=10, intervals=3):
        for i in range(total_cycles):
            self.disk_info_pool.scan_disk()
            temp = [_disk_info.top_device_id for _disk_info in self.disk_info_pool.disk_pool.values()]
            if top_dev_id in temp:
                time.sleep(intervals)
            else:
                break
        else:
            print ("%s not disappear" % top_dev_id)
            return 1
        return 0

    def _wait_somedisk_appear(self, old_disk, wait_num=1, total_cycles=10, intervals=3):
        for i in range(total_cycles):
            self.disk_info_pool.scan_disk()
            new_disk = set(self.disk_info_pool.disk_pool.keys())
            differ = new_disk.difference(set(old_disk))
            if len(differ) >= wait_num:
                return differ
            else:
                time.sleep(intervals)

    def _wait_somedisk_disappear(self, old_disk, wait_num=1, total_cycles=10, intervals=3):
        for i in range(total_cycles):
            self.disk_info_pool.scan_disk()
            new_disk = set(self.disk_info_pool.disk_pool.keys())
            differ = set(old_disk).difference(new_disk)
            if len(differ) >= wait_num:
                return differ
            else:
                time.sleep(intervals)

    def _get_disk_info(self, dev_id):
        self._wait_device_appear_by_id(dev_id)
        return self.disk_info_pool.disk_pool.get(dev_id)

    def _get_all_disk_ids(self):
        disk_ids = []
        for _disk_info in self._periphery_device.disk_info:
            disk_ids.append(_disk_info.disk_id)
        return disk_ids

    def setup_io_jobs(self, io_t):
        logger.info("setup IO Tool: %s" % io_t)
        if io_t == "vdbench":
            self.io_jobs = VDBenchJob(self._job_id)
            self.io_jobs.initialize()
        elif io_t == "fio": 
            raise RuntimeError("Not support for now.")

    def close_io_jobs(self):
        self.io_jobs.clean_job()

    #############################
    def _set_io_cold_data(self, value):
        if isinstance(value, list) or isinstance(value, tuple):
            self.__io_cold_data_range = value
            self.__io_cold_data_prepare_flag = False
    
    def _set_io_hot_data(self, value):
        if isinstance(value, list) or isinstance(value, tuple):
            self.__io_hot_data_range = value
    
    def set_io_cfg(self, cfg):
        """
        Args:
          cfg: list type
            [[cold_data_range], [warm_data_range], [hot_data_range]]
        """
        if (isinstance(cfg, list) or isinstance(cfg, tuple)):
            for index,v in enumerate(cfg):
                if v is None:
                    continue
                if index == 0:
                    self._set_io_cold_data(v)
                elif index == 2:
                    self._set_io_hot_data(v)

    ### close all
    def close(self):
        self.close_periphery_device()
        self.close_io_jobs()

    ####
    def periphery_poweron(self):
        self._periphery_device.hotswapM_poweron()
    
    def periphery_poweroff(self, notify_power=False):
        if notify_power:
            for _disk_info in self._periphery_device.disk_info:
                _disk_info.set_device_power(power='off')
            for _disk_info in self._periphery_device.disk_info:
                disk_id = _disk_info.disk_id
                # check if disk disappear
                if self._wait_device_disappear_by_id(disk_id):
                    logger.error("Disk %s cannot power off by power notify" % disk_id)
                    raise RuntimeError("Disk %s cannot power off by power notify" % disk_id)
                else:
                    logger.debug("Disk %s power off by power notify" % disk_id)
        self._periphery_device.hotswapM_poweroff()

    def dump_in_test(self):
        dump_info = {}
        for _disk_info in self._periphery_device.disk_info:
            intf = _disk_info.interface
            if intf == 'pcie':
                disk_pci_config = _disk_info.disk_pci_config
                dump_info[_disk_info.disk_id] = {"LinkSpeed": disk_pci_config.express_link.cur_speed,
                                                 "LinkWidth": disk_pci_config.express_link.cur_width}
            elif intf == 'sata':
                dump_info[_disk_info.disk_id] = {"LinkSpeed": _disk_info.sata_speed[1]}
            elif intf == 'sas':
                dump_info[_disk_info.disk_id] = {"LinkSpeed": "dummy"}
        return dump_info


class HotPlugQuarch(HotPlugBase):
    def __init__(self, ConnID, job_id, shared_info):
        self.__conn_id = ConnID.strip()
        periphery_device = QuarchDevice()
        periphery_device.periphery_device = get_quarch_module(self.__conn_id)
        if not periphery_device.periphery_device:
            raise RuntimeError("Cannot initialize Quarch device %s" % self.__conn_id)
        ##
        super(HotPlugQuarch, self).__init__(job_id, shared_info, periphery_device)
        ###
        ## quarch source  config
        self.__quarch_source_delay = [25,10,100,500]
        self.__quarch_source_bounce_length = []
        self.__quarch_source_bounce_period = []
        self.__quarch_source_duty_cycle = []

    def DoHotPull(self, notify_power):
        def func():
            # pull
            self.periphery_poweroff(notify_power=notify_power)
            # wait all disk disappear,_info.keys()
            all_disk_ids = self._get_all_disk_ids()
            if self._wait_device_disappear_by_ids(all_disk_ids):
                logger.error("Disk Not disappear %s" % all_disk_ids)
            else:
                logger.info("All Disk disappear %s" % all_disk_ids)
        ##
        if self.hot_swap_config.hot_pull_type == 0:
            func()
        elif self.hot_swap_config.hot_pull_type == 1:
            barrier = self._shared_info.get("BarrierHotSwap")
            if barrier is None or barrier.broken:
                ## create a new one
                with self._shared_info.get("RLockCop"):
                    barrier = self._shared_info.get("BarrierHotSwap")
                    if barrier is None or barrier.broken:
                        self._shared_info["BarrierHotSwap"] = threading.Barrier(self._shared_info["AliveThread"])
                        barrier = self._shared_info.get("BarrierHotSwap")
            try:
                bid = barrier.wait(timeout=self.hot_pull_para[0])
            except threading.BrokenBarrierError: # now we occur timeout now
                # abort all the waitting 
                barrier.abort()
                logger.warning("Occur BrokenBarrierError when do hot pull")
            ## continue to do hot pull
            func()
        elif self.hot_swap_config.hot_pull_type == 2:
            ##
            with self._shared_info.get("RLockHotSwap"):
                func()
        elif self.hot_swap_config.hot_pull_type == 3:
            # step 1. acqiure Lock
            with self._shared_info.get("RLockHotSwap"):
                # start backend hot swap
                func()
                #
                time.sleep(self.hot_pull_para[0])
        elif self.hot_swap_config.hot_pull_type == 4:
            barrier = self._shared_info.get("BarrierHotSwap")
            if barrier is None or barrier.broken:
                ## create a new one
                with self._shared_info.get("RLockCop"):
                    barrier = self._shared_info.get("BarrierHotSwap")
                    if barrier is None or barrier.broken:
                        self._shared_info["BarrierHotSwap"] = threading.Barrier(self._shared_info["AliveThread"])
                        barrier = self._shared_info.get("BarrierHotSwap")
            try:
                bid = barrier.wait(timeout=self.hot_pull_para[0])
            except threading.BrokenBarrierError: # now we occur timeout now
                # abort all the waitting 
                barrier.abort()
                logger.warning("Occur BrokenBarrierError when do hot pull")
            ## continue to do hot pull
            with self._shared_info.get("RLockHotSwap"):
                func()
        else:
            func()

    def DoHotPush(self):
        def func():
            self.periphery_poweron()
            # wait all disk appear by sn
            if self._wait_device_appear_by_ids(self._get_all_disk_ids()):
                logger.error("Disk Not appear %s" % self._get_all_disk_ids())
            else:
                logger.info("All Disk appear %s" % self._get_all_disk_ids())
        ##
        if self.hot_swap_config.hot_push_type == 0:
            func()
        elif self.hot_swap_config.hot_push_type == 1:
            barrier = self._shared_info.get("BarrierHotSwap")
            if barrier is None or barrier.broken:
                ## create a new one
                with self._shared_info.get("RLockCop"):
                    barrier = self._shared_info.get("BarrierHotSwap")
                    if barrier is None or barrier.broken:
                        self._shared_info["BarrierHotSwap"] = threading.Barrier(self._shared_info["AliveThread"])
                        barrier = self._shared_info.get("BarrierHotSwap")
            try:
                bid = barrier.wait(timeout=self.hot_push_para[0])
            except threading.BrokenBarrierError: # now we occur timeout now
                # abort all the waitting 
                barrier.abort()
                logger.warning("Occur BrokenBarrierError when do hot pull")
            ## continue to do hot pull
            func()
        elif self.hot_swap_config.hot_push_type == 2:
            ##
            with self._shared_info.get("RLockHotSwap"):
                func()
        elif self.hot_swap_config.hot_push_type == 3:
            # step 1. acqiure Lock
            with self._shared_info.get("RLockHotSwap"):
                # start backend hot swap
                func()
                #
                time.sleep(self.hot_push_para[0])
        elif self.hot_swap_config.hot_push_type == 4:
            barrier = self._shared_info.get("BarrierHotSwap")
            if barrier is None or barrier.broken:
                ## create a new one
                with self._shared_info.get("RLockCop"):
                    barrier = self._shared_info.get("BarrierHotSwap")
                    if barrier is None or barrier.broken:
                        self._shared_info["BarrierHotSwap"] = threading.Barrier(self._shared_info["AliveThread"])
                        barrier = self._shared_info.get("BarrierHotSwap")
            try:
                bid = barrier.wait(timeout=self.hot_push_para[0])
            except threading.BrokenBarrierError: # now we occur timeout now
                # abort all the waitting 
                barrier.abort()
                logger.warning("Occur BrokenBarrierError when do hot pull")
            ## continue to do hot pull
            with self._shared_info.get("RLockHotSwap"):
                func()
        else:
            func()
    
    def set_quarch_source_cfg(self, cfg):
        """
        Args:
          cfg: list type
            [[source_delay], [Bounce length], [Bounce Period],[ Duty Cycle]]
        """
        if (isinstance(cfg, list) or isinstance(cfg, tuple)):
            for index,v in enumerate(cfg):
                if v is None:
                    continue
                if index == 0:
                    self.__quarch_source_delay = v
                elif index == 1:
                    self.__quarch_source_bounce_length = v
                elif index == 2:
                    self.__quarch_source_bounce_period = v
                elif index == 3:
                    self.__quarch_source_duty_cycle = v

    def quarch_hotswapM_get_source_delay(self, source_index):
        return self._periphery_device.hotswapM_get_delay_source(source_index)

    def quarch_hotswapM_setup_source_delay(self, 
                                           source1_delay,
                                           source2_delay,
                                           source3_delay):
        return self._periphery_device.hotswapM_setup_delay_source(source1_delay,source2_delay,source3_delay)

    def _test_process(self, cycles, source_delay, cold_data=None, hot_data=None, skip_hot_data=False, io_block_time=None, off_time=None, on_time=None, notify_power=False):
        """function to run config hot-plug test
        
        Args:
          cycles: int type, test cycles in every source_delay;
          source_delay: list type, source delay to setup quarch hotplug module
          cold_data: list type, cold data will be done before the test, and will not be writtten in test process, data will be valiadation after all test done;
          hot_data: list type, hot data will be written in test and will not be valadited;
        
        Kwargs:
          cold_data: list type(default None), cold data will be done before the test, and will not be writtten in test process, data will be valiadation after all test done;
          hot_data: list type(default None), hot data will be written in test and will not be valadited;
          io_block_time: int type(default None), if None will do block IO, or will block the io in io_block_time;
          off_time: int type(default None), unit second, that the time between power off and power on
          on_time: int type(default None), unit second, if io_block_time is not None, stands the time between power on and power off
        
        Returns：
            0: success
            1: disk cannot poweroff
            2: disk cannot poweron
            3: disk info changed
            4: IO error
        
        Raise:
            TBD.
        """
        self.set_io_cfg([cold_data,None,hot_data])
        self.set_quarch_source_cfg([source_delay,])
        if off_time is None:
            off_time = self.hot_swap_config.off_time
        if on_time is None:
            on_time = self.hot_swap_config.on_time
        ## get old information of disk
        old_info = self.dump_in_test()
        logger.info("RAW Disk Info:")
        for disk_id,disk_cfg in old_info.items():
            logger.info("Disk ID: %s, Disk Info: %s" % (disk_id,str(disk_cfg)))
        ## prepare data
        if self._io_cold_data_range and self.io_jobs and (not self._io_cold_data_prepare_flag):
            logger.info("Prepare Cold Data: %s" % str(self._io_cold_data_range))
            for io_range in self._io_cold_data_range:
                process_pool = []
                for _disk_info in self._periphery_device.disk_info:
                    _disk_id = _disk_info.disk_id
                    ## wait device ready
                    temp_disk_info = self._get_disk_info(_disk_id)
                    logger.info("Prepare Cold Data: disk_id->%s, disk_path->%s, io_range->%s" % (temp_disk_info.disk_id, temp_disk_info.disk_path, io_range))
                    p = self.io_jobs.precondition_128k_seqw_coldData(_disk_id, temp_disk_info.disk_path, io_range)
                    process_pool.append(p)
                # wait all done and run next workload
                for p in process_pool:
                    if p.wait_done() != 0:
                        logger.error("Run IO error: %s" % p.get_cmd())
                        return 4
            self._io_cold_data_prepare_flag = True
        ## setup quarch source delay
        for delay_index in range(len(self.__quarch_source_delay)):
            delay = self.__quarch_source_delay[delay_index]
            self.quarch_hotswapM_setup_source_delay(0,delay,2*delay)
            temp = self.quarch_hotswapM_get_source_delay("ALL")
            logger.info("Config quarch source delay: %s/%s, Setup source delay: %sms" % (delay_index+1,len(self.__quarch_source_delay),str(temp)))
            ## wait device after setup quarch
            self._wait_device_appear_by_ids(self._get_all_disk_ids())
            for i in range(cycles):
                logger.info("Current loop: %s/%s" % (i+1,cycles))
                # do io
                process_pool = []
                if self._io_hot_data_range and self.io_jobs and (not skip_hot_data):
                    for io_range in self._io_hot_data_range:
                        process_pool = []
                        for _disk_info in self._periphery_device.disk_info:
                            _disk_id = _disk_info.disk_id
                            ## wait device ready
                            temp_disk_info = self._get_disk_info(_disk_id)
                            ##
                            rdpct = random.randint(0,30)
                            logger.info("Hot Data: disk_id->%s, disk_path->%s, io_range->%s" % (temp_disk_info.disk_id, temp_disk_info.disk_path, io_range))
                            p = self.io_jobs.test_4k_randrw_60s(_disk_id, temp_disk_info.disk_path, io_range, rdpct)
                            process_pool.append(p)
                        if io_block_time is None:
                            # wait all done and run next workload
                            for p in process_pool:
                                if p.wait_done() != 0:
                                    logger.error("Run IO error: %s" % p.get_cmd())
                                    return 4
                        else:
                            time.sleep(io_block_time)
                            ## we will check if IO is still in process
                            for p in process_pool:
                                if p.proc.returncode == None:
                                    logger.debug("IO is running well")
                                elif p.proc.returncode == 0:
                                    logger.warning("IO is running done, you should set a smaller io_block_time")
                                else:
                                    logger.error("IO error while checking IO status in test hot_data")
                                    return 4
                            break
                else:
                    logger.debug("Will sleep %ss to poweroff" % on_time)
                    time.sleep(on_time)
                # pull and wait all disk disappear,_info.keys()
                self.DoHotPull(notify_power)
                # now that we check if all IO stopped
                if self._io_hot_data_range and self.io_jobs and (io_block_time is not None):
                    logger.info("Checking all IO ...")
                    for p in process_pool:
                        rc = p.wait_done()
                        if rc == 0:
                            logger.warning("cmd: %s , error code: %s" % (p.get_cmd(), rc)) 
                        else:
                            logger.debug("cmd: %s , error code: %s" % (p.get_cmd(), rc)) 
                    logger.info("All IO stopped!")      
                # wait 10s, and plug
                logger.debug("Will sleep %ss to poweron" % off_time)
                time.sleep(off_time)
                # plug and wait all disk appear by sn
                self.DoHotPush()
                # check old info with new info
                new_info = self.dump_in_test()
                if old_info == new_info:
                    logger.info("Check info done!")
                else:
                    logger.info("Old info:")
                    logger.info(str(old_info))
                    logger.info("New info:")
                    logger.info(str(new_info))
                    logger.error("Check info failed!")
                    return 3
                #
        ## compare cold data
        if self._io_cold_data_range and self.io_jobs:
            logger.info("Compare Cold Data: %s" % str(self._io_cold_data_range))
            for io_range in self._io_cold_data_range:
                process_pool = []
                for _disk_info in self._periphery_device.disk_info:
                    _disk_id = _disk_info.disk_id
                    ## wait device ready
                    temp_disk_info = self._get_disk_info(_disk_id)
                    logger.info("Compare Cold Data: disk_id->%s, disk_path->%s, io_range->%s" % (temp_disk_info.disk_id, temp_disk_info.disk_path, io_range))
                    p = self.io_jobs.precondition_128k_coldData_val(temp_disk_info.disk_id, temp_disk_info.disk_path, io_range)
                    process_pool.append(p)
                # wait all done and run next workload
                for p in process_pool:
                    if p.wait_done() != 0:
                        logger.error("Run IO error: %s" % p.get_cmd())
                        return 4
        return 0
    
    @run_test_decorator
    def test_case0(self, cycles=50, source_delay = [25,10,100,500]):
        """
        Do hotplug without IO
        """
        return self._test_process(cycles, source_delay, skip_hot_data=True)

    @run_test_decorator
    def test_case1(self, cycles=50, source_delay = [25,10,100,500]):
        """
        Do hotplug with integrated IO
        """
        return self._test_process(cycles, source_delay)

    @run_test_decorator
    def test_case2(self, cycles=50, source_delay = [25,10,100,500]):
        """
        Do hotplug with running IO
        """
        return self._test_process(cycles, source_delay, io_block_time=30)

    @run_test_decorator
    def test_case10(self, cycles=50, source_delay = [25,10,100,500]):
        """
        Do notify hotplug without IO
        """
        return self._test_process(cycles, source_delay, notify_power=True, skip_hot_data=True)


class HotPlugManual(HotPlugBase):
    def __init__(self, ConnID, job_id, shared_info):
        self.__conn_id = ConnID.strip()
        periphery_device = ManualDevice()
        periphery_device.periphery_device = get_manual_module(self.__conn_id)
        if not periphery_device.periphery_device:
            raise RuntimeError("Cannot initialize Quarch device %s" % self.__conn_id)
        ##
        super(HotPlugManual, self).__init__(job_id, shared_info, periphery_device)

    def DoHotPull(self, notify_power):
        def func():
            # pull
            self.periphery_poweroff(notify_power=notify_power)
            # wait all disk disappear,_info.keys()
            all_disk_ids = self._get_all_disk_ids()
            if self._wait_device_disappear_by_ids(all_disk_ids, total_cycles=100000):
                logger.error("Disk Not disappear %s" % all_disk_ids)
            else:
                logger.info("All Disk disappear %s" % all_disk_ids)
        ##
        func()

    def DoHotPush(self):
        def func():
            self.periphery_poweron()
            # wait all disk appear by sn
            if self._wait_device_appear_by_ids(self._get_all_disk_ids(), total_cycles=100000):
                logger.error("Disk Not appear %s" % self._get_all_disk_ids())
            else:
                logger.info("All Disk appear %s" % self._get_all_disk_ids())
        ##
        func()

    def _test_process(self, cycles, cold_data=None, hot_data=None, skip_hot_data=False, io_block_time=None, off_time=None, on_time=None, notify_power=False):
        """function to run config hot-plug test
        
        Args:
          cycles: int type, test cycles in every source_delay;
          cold_data: list type, cold data will be done before the test, and will not be writtten in test process, data will be valiadation after all test done;
          hot_data: list type, hot data will be written in test and will not be valadited;
        
        Kwargs:
          cold_data: list type(default None), cold data will be done before the test, and will not be writtten in test process, data will be valiadation after all test done;
          hot_data: list type(default None), hot data will be written in test and will not be valadited;
          io_block_time: int type(default None), if None will do block IO, or will block the io in io_block_time;
          off_time: int type(default None), unit second, that the time between power off and power on
          on_time: int type(default None), unit second, if io_block_time is not None, stands the time between power on and power off
        
        Returns：
            0: success
            1: disk cannot poweroff
            2: disk cannot poweron
            3: disk info changed
            4: IO error
        
        Raise:
            TBD.
        """
        self.set_io_cfg([cold_data,None,hot_data])
        if off_time is None:
            off_time = self.hot_swap_config.off_time
        if on_time is None:
            on_time = self.hot_swap_config.on_time
        ## get old information of disk
        old_info = self.dump_in_test()
        logger.info("RAW Disk Info:")
        for disk_id,disk_cfg in old_info.items():
            logger.info("Disk ID: %s, Disk Info: %s" % (disk_id,str(disk_cfg)))
        ## prepare data
        if self._io_cold_data_range and self.io_jobs and (not self._io_cold_data_prepare_flag):
            logger.info("Prepare Cold Data: %s" % str(self._io_cold_data_range))
            for io_range in self._io_cold_data_range:
                process_pool = []
                for _disk_info in self._periphery_device.disk_info:
                    _disk_id = _disk_info.disk_id
                    ## wait device ready
                    temp_disk_info = self._get_disk_info(_disk_id)
                    logger.info("Prepare Cold Data: disk_id->%s, disk_path->%s, io_range->%s" % (temp_disk_info.disk_id, temp_disk_info.disk_path, io_range))
                    p = self.io_jobs.precondition_128k_seqw_coldData(_disk_id, temp_disk_info.disk_path, io_range)
                    process_pool.append(p)
                # wait all done and run next workload
                for p in process_pool:
                    if p.wait_done() != 0:
                        logger.error("Run IO error: %s" % p.get_cmd())
                        return 4
            self._io_cold_data_prepare_flag = True

        ## wait device after setup quarch
        self._wait_device_appear_by_ids(self._get_all_disk_ids())
        for i in range(cycles):
            logger.info("Current loop: %s/%s" % (i+1,cycles))
            # do io
            process_pool = []
            if self._io_hot_data_range and self.io_jobs and (not skip_hot_data):
                for io_range in self._io_hot_data_range:
                    process_pool = []
                    for _disk_info in self._periphery_device.disk_info:
                        _disk_id = _disk_info.disk_id
                        ## wait device ready
                        temp_disk_info = self._get_disk_info(_disk_id)
                        ##
                        rdpct = random.randint(0,30)
                        logger.info("Hot Data: disk_id->%s, disk_path->%s, io_range->%s" % (temp_disk_info.disk_id, temp_disk_info.disk_path, io_range))
                        p = self.io_jobs.test_4k_randrw_60s(_disk_id, temp_disk_info.disk_path, io_range, rdpct)
                        process_pool.append(p)
                    if io_block_time is None:
                        # wait all done and run next workload
                        for p in process_pool:
                            if p.wait_done() != 0:
                                logger.error("Run IO error: %s" % p.get_cmd())
                                return 4
                    else:
                        time.sleep(io_block_time)
                        ## we will check if IO is still in process
                        for p in process_pool:
                            if p.proc.returncode == None:
                                logger.debug("IO is running well")
                            elif p.proc.returncode == 0:
                                logger.warning("IO is running done, you should set a smaller io_block_time")
                            else:
                                logger.error("IO error while checking IO status in test hot_data")
                                return 4
                        break
            else:
                logger.debug("Will sleep %ss to poweroff" % on_time)
                time.sleep(on_time)
            # pull and wait all disk disappear,_info.keys()
            self.DoHotPull(notify_power)
            # now that we check if all IO stopped
            if self._io_hot_data_range and self.io_jobs and (io_block_time is not None):
                logger.info("Checking all IO ...")
                for p in process_pool:
                    rc = p.wait_done()
                    if rc == 0:
                        logger.warning("cmd: %s , error code: %s" % (p.get_cmd(), rc)) 
                    else:
                        logger.debug("cmd: %s , error code: %s" % (p.get_cmd(), rc)) 
                logger.info("All IO stopped!")      
            # wait 10s, and plug
            logger.debug("Will sleep %ss to poweron" % off_time)
            time.sleep(off_time)
            # plug and wait all disk appear by sn
            self.DoHotPush()
            # check old info with new info
            new_info = self.dump_in_test()
            if old_info == new_info:
                logger.info("Check info done!")
            else:
                logger.info("Old info:")
                logger.info(str(old_info))
                logger.info("New info:")
                logger.info(str(new_info))
                logger.error("Check info failed!")
                return 3
        ## compare cold data
        if self._io_cold_data_range and self.io_jobs:
            logger.info("Compare Cold Data: %s" % str(self._io_cold_data_range))
            for io_range in self._io_cold_data_range:
                process_pool = []
                for _disk_info in self._periphery_device.disk_info:
                    _disk_id = _disk_info.disk_id
                    ## wait device ready
                    temp_disk_info = self._get_disk_info(_disk_id)
                    logger.info("Compare Cold Data: disk_id->%s, disk_path->%s, io_range->%s" % (temp_disk_info.disk_id, temp_disk_info.disk_path, io_range))
                    p = self.io_jobs.precondition_128k_coldData_val(temp_disk_info.disk_id, temp_disk_info.disk_path, io_range)
                    process_pool.append(p)
                # wait all done and run next workload
                for p in process_pool:
                    if p.wait_done() != 0:
                        logger.error("Run IO error: %s" % p.get_cmd())
                        return 4
        return 0

    @run_test_decorator
    def test_case0(self, cycles=50):
        """
        Do hotplug without IO
        """
        return self._test_process(cycles, skip_hot_data=True)

    @run_test_decorator
    def test_case1(self, cycles=50):
        """
        Do hotplug with integrated IO
        """
        return self._test_process(cycles)

    @run_test_decorator
    def test_case2(self, cycles=50):
        """
        Do hotplug with running IO
        """
        return self._test_process(cycles, io_block_time=30)

    @run_test_decorator
    def test_case10(self, cycles=50):
        """
        Do notify hotplug without IO
        """
        return self._test_process(cycles, notify_power=True, skip_hot_data=True)

