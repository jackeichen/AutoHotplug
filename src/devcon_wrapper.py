#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#Author: Gao Zhihua
#Date: 2021/11/28
from src.lib import run_cmd


class DevHWIds(object):
    def __init__(self):
        self.ids = ''
        self.Name = ''
        self.Hardware_IDs = []
        self.Compatible_IDs = []
    
    def load(self, string):
        pass


class DevCon(object):
    def __init__(self, cmd_path):
        self._cmd = cmd_path
    
    def run_cmd(self, string_args):
        args = [self._cmd]
        args.extend(string_args.split(' '))
        stdout = run_cmd(args)
        return stdout
    
    def find(self, matched):
        return self.run_cmd('find %s' % matched)
    
    def hwids(self, matched):
        hw_ids = {}
        stdout = self.run_cmd('hwids %s' % matched)
        stdout = stdout.split("\r\n")
        for i in stdout:
            pass
        
        
    
        
