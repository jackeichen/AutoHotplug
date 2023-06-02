#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#Author: Gao Zhihua
#Date: 2018/03/29
import os,sys
import time
import random
import traceback
import platform
import re
from optparse import OptionParser
from src.hotplug import HotPlugModule
from src.log_hotplug import logger
from src.IOJobs import getIOJobs
from src.lib import localtime,run_cmd


"""
ConnID = "usb:QTL2266-02-224"
hot_plug = HotPlugModule()
hot_plug.setup_quarch_dev_pool(ConnID)
hot_plug.quarch_dev_pool.print_device_pool()
print (hot_plug.quarch_hotswapM_get_source_delay("ALL"))
hot_plug.quarch_hotswapM_setup_source_delay(0,50,150)
print (hot_plug.quarch_hotswapM_get_source_delay("ALL"))
hot_plug.close()
"""
"""
logger.debug("debug")
logger.info("info")
logger.warning("warning")
logger.error("error")
logger.critical("critical")
"""
"""
io_jobs = getIOJobs("vdbench")
io_jobs.initialize()
print ("vdbench version: ", io_jobs.getToolVersion())
print ("precondition_128k_seqw_coldData 0,1")
io_jobs.precondition_128k_seqw_coldData("/dev/nvme0n1", '(0,1)')
print ("precondition_128k_seqw_coldData 99,100")
io_jobs.precondition_128k_seqw_coldData("/dev/nvme0n1", '(99,100)')
print ("precondition_128k_seqw_coldData 20,21")
io_jobs.precondition_128k_seqw_coldData("/dev/nvme0n1", '(20,21)')

print ("test")
io_jobs.test_4k_randrw_60s("/dev/nvme0n1", '(30,60)', 50)

print ("compare 0,1")
io_jobs.precondition_128k_coldData_val("/dev/nvme0n1", '(0,1)')
print ("compare 99,100")
io_jobs.precondition_128k_coldData_val("/dev/nvme0n1", '(99,100)')
print ("compare 20,21")
io_jobs.precondition_128k_coldData_val("/dev/nvme0n1", '(20,21)')
"""
