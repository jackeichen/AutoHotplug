#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#Author: Gao Zhihua
#Date: 2018/05/11
#This is for logging the test
from src.script_path import LOGS_path
from src.get_config import get_config
from src.log_module.logger import Logger


class LogHotPlug(Logger):
    def __init__(self):
        super(LogHotPlug, self).__init__(LOGS_path, 'AutoHotplug')
        self._config = get_config()
    
    def log(self):
        self.init_settings(self._config.get("run_log"))
        logger = self.get_logger()
        return logger

logger = LogHotPlug().log()
