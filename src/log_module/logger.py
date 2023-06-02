#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#Author: Gao Zhihua
#Date: 2018/05/11
#This is for logging the test

import os
import logging
from logging.handlers import TimedRotatingFileHandler


class Logger(object):
    def __init__(self, LOG_PATH, logger_name='AutoHotplug'):
        self.logger = logging.getLogger(logger_name)
        self._set_log_path(LOG_PATH)
    
    def init_settings(self, kwargs):
        # 日志输出文件路径和名称
        self.log_file_name = kwargs.get("file_name")
        self.err_file_name = kwargs.get("err_file_name")
        #back up file保留个数
        self.backup_count = kwargs.get("backup")
        # 日志输出级别
        self.console_output_level = kwargs.get("console_level")
        self.file_output_level = kwargs.get("file_level")
        # 日志输出格式
        self.pattern = kwargs.get("pattern")
        # 日志备份
        self.when = kwargs.get("when")
        self.interval = kwargs.get("interval")
    
    def _set_log_path(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
        self.log_file_path = path
        
    def get_logger(self):
        '''
        在logger中添加日志句柄并返回，如果logger已有句柄，则直接返回
        我们这里添加两个句柄，一个输出日志到控制台，另一个输出到日志文件。
        两个句柄的日志级别不同，在配置文件中可设置。
        '''
        logging.root.setLevel(logging.NOTSET)
        #日志输出完整文件路径
        formatter = logging.Formatter(self.pattern)
        
        if not self.logger.handlers:  # 避免重复日志
            if self.console_output_level:
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(formatter)
                console_handler.setLevel(self.console_output_level)
                self.logger.addHandler(console_handler)

            if self.log_file_name:
                log_full_name = os.path.join(self.log_file_path, self.log_file_name)
                # interval重新创建一个日志文件，最多保留backup_count份
                file_handler = TimedRotatingFileHandler(filename=log_full_name,
                                                        when=self.when,
                                                        interval=self.interval,
                                                        backupCount=self.backup_count,
                                                        delay=True,
                                                        encoding='utf-8'
                                                        )
                file_handler.setFormatter(formatter)
                file_handler.setLevel(self.file_output_level)
                self.logger.addHandler(file_handler)
            #
            if self.err_file_name:
                err_full_name =  os.path.join(self.log_file_path, self.err_file_name)
                file_err_handler = TimedRotatingFileHandler(filename=err_full_name,
                                                            when=self.when,
                                                            interval=self.interval,
                                                            backupCount=self.backup_count,
                                                            delay=True,
                                                            encoding='utf-8'
                                                            )
                file_err_handler.setFormatter(formatter)
                file_err_handler.setLevel("ERROR")
                self.logger.addHandler(file_err_handler)
        return self.logger

