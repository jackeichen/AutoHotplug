#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#Author: Gao Zhihua
#Date: 2023/09/26
import re
import subprocess
from collections import namedtuple
from src.lib import os_type,sb_convert
from src.pciutils.pci_parser import PCIParser

class CommandWrapper(object):
    def __init__(self, cmd_path):
        self._cmd = [cmd_path,]

    def run_cmd(self, cmd):
        cmd = self._cmd + cmd
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout, stderr) = p.communicate()
        if p.returncode or stderr:
            print ("Return code=%s" % p.returncode)
            print (sb_convert(stderr, str))
            raise RuntimeError("Run command: %s error" % cmd)
        else:
            return sb_convert(stdout, str)


class lspciWrapper(CommandWrapper):
    def __init__(self, cmd_path=None):
        if not cmd_path:
            if os_type == 'Linux':
                cmd_path = 'lspci'
            elif os_type == 'Windows':
                from src.script_path import lspci_win_path
                cmd_path = lspci_win_path
            else:
                raise RuntimeError("Non-support OS: %s" % os_type)
        super(lspciWrapper, self).__init__(cmd_path)

    def get_version(self):
        stdout = self.run_cmd(["--version",])
        g = re.match(r'lspci version (.*)', stdout.strip())
        if g and g[1]:
            return g[1].strip()


class setpciWrapper(CommandWrapper):
    def __init__(self, cmd_path=None):
        if not cmd_path:
            if os_type == 'Linux':
                cmd_path = 'setpci'
            elif os_type == 'Windows':
                from src.script_path import setpci_win_path
                cmd_path = setpci_win_path
            else:
                raise RuntimeError("Non-support OS: %s" % os_type)
        super(setpciWrapper, self).__init__(cmd_path)

    def get_version(self):
        stdout = self.run_cmd(["--version",])
        g = re.match(r'setpci version (.*)', stdout.strip())
        if g and g[1]:
            return g[1].strip()


class PCIeDevice(object):
    def __init__(self, pci_addr):
        self.lspci = lspciWrapper()
        self.setpci = setpciWrapper()
        ##
        self.__pci_addr = pci_addr

    def lspci_runcmd(self, cmd):
        cmd.extend(['-s', self.__pci_addr])
        return self.lspci.run_cmd(cmd)

    def setpci_runcmd(self, cmd):
        cmd.extend(['-s', self.__pci_addr])
        return self.setpci.run_cmd(cmd)

    @property
    def pci_addr(self):
        return self.__pci_addr

    @property
    def lspci_vvd(self):
        temp = self.lspci_runcmd(['-D', '-vv',])
        parser = PCIParser([temp.splitlines(),])
        return parser.devices[0]
