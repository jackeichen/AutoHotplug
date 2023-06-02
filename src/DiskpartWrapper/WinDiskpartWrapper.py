# -*-coding:UTF-8 -*-
""" Module contains classes/function for work with DISKPART utility
"""
from subprocess import Popen, PIPE
import re
import ctypes
import locale
from abc import ABCMeta, abstractproperty

from src.DiskpartWrapper.DiskUtilityModule import DiskUtilExceptions, DiskUtilityInterface
from src.DiskpartWrapper.SubprocessInteractive import InteractiveCommand


class WindowsDiskUtility(DiskUtilityInterface):
    """
    Do Not run the class in the different process.
    """
    def __init__(self, defaultEncoding='GBK'):
        """ Class wrapper for DISPART utility
        :param defaultEncoding: (str) Windows console output encoding
        :return: WindowsDiskUtility object
        """
        self.defaultEcoding = defaultEncoding
        #determin locale language
        windll = ctypes.windll.kernel32
        language = locale.windows_locale[ windll.GetUserDefaultUILanguage() ]
        self._locale = self._getLocale(language)
        #init Popen connection to diskpart
        try:
            p = Popen(["diskpart"], shell=True, stdin=PIPE, stdout=PIPE )
            prompt = re.compile(r"^DISKPART>", re.M)
            self.cmd = InteractiveCommand(p, prompt, self.defaultEcoding)
        except WindowsError as e:
            raise DiskUtilExceptions('Cannot start DISKPART utility! Err: ' + str(e.winerror))

    def __del__(self):
        """ Close DISKPART connection
        :return:
        """
        self.cmd.command("exit")

    def _getLocale(self, lang='en'):
        """ factory method for LocaleInterface
        :param lang: (str) language abbr
        :return: (LocaleInterface object) corresponding current language
        """
        if 'en' in lang:
            return EnLocale()
        elif 'ru' in lang:
            return RuLocale()
        elif 'zh' in lang:
            return ZhLocale()

    def _execDiskpartCmd(self, command):
        """ Execute DISKPART command
        :param command: (str) Command to execute
        :return: DISKPART output
        Raises:
          DiskpartException: If command is not valid
        """
        out = self.cmd.command(command)
        return out

    def listDisk(self):
        out = self._execDiskpartCmd('LIST DISK')
        result = re.findall(self._locale.LIST_DISK_PATTERN, out)
        if len(result)==0:
            print (out)
        for disk in result:
            print (disk[0] + ' - ' + disk[1])
        return result

    def selectDisk(self, diskID):
        """ Perform SELECT DISK command
        :param diskID: (int) Disk id
        :return: (str) DISK PART output
        Raises:
          DiskpartException: If command is not valid
          ValueError: if diskID not int
        """
        try:
            out = self._execDiskpartCmd("SELECT DISK %d" %int(diskID))
        except ValueError:
            raise DiskUtilExceptions('Select disk : Invalid Disk ID Parameter : <' + diskID + '>')
        if not self._locale.SELECT_DISK_VALIDATION_MESSAGE in out:
            raise DiskUtilExceptions('Cannot select disk : ' + out)

    def listDiskPartition(self, diskID):
        self.selectDisk(diskID)
        out = self._execDiskpartCmd("LIST PARTITION")
        result = re.findall(self._locale.LIST_PARTITION_PATTERN, out)
        if len(result) == 0:
            raise DiskUtilExceptions('List partition : ' + out)
        for partition in result:
            print (partition[0] + ' - ' + partition[1])

    def listvisibleDiskVolume(self, diskID):
        self.selectDisk(diskID)
        out = self._execDiskpartCmd("DETAIL DISK")
        result = re.findall(self._locale.LIST_VISIBLE_VOLUME_PATTERN, out)
        if len(result) == 0:
            raise DiskUtilExceptions('List volume : ' + out)
        for partition in result:
            print (partition[0] + ' - ' + partition[1] + ' - ' + partition[2])
        return result
    
    def get_OS_volume(self, diskID):
        self.selectDisk(diskID)
        out = self._execDiskpartCmd("DETAIL DISK")
        result = re.findall(self._locale.LIST_OS_PATTERN, out)
        return result

#============================================================================
class LocaleInterface():
    __metaclass__ = ABCMeta
    @property
    def LIST_PARTITION_PATTERN(self):
        """
        :return: Pattern for matching LIST PARTITION command output
        """
        raise NotImplementedError
    @property
    def LIST_DISK_PATTERN(self):
        """
        :return: Pattern for matching LIST DISK command output
        """
        raise NotImplementedError

    @property
    def SELECT_DISK_VALIDATION_MESSAGE(self):
        """
        :return: SELECT DISK SUCCESS MESSAGE
        """
        raise NotImplementedError
    
    @property
    def LIST_VISIBLE_VOLUME_PATTERN(self):
        """
        :return: Pattern for matching LIST VOLUME command output
        """
        raise NotImplementedError
    
    @property
    def LIST_OS_PATTERN(self):
        """
        :return: Pattern for matching LIST VOLUME command output
        """
        raise NotImplementedError

class RuLocale(LocaleInterface):
    LIST_DISK_PATTERN = '(Äèñê [0-9]+)\s+.+?\s+([0-9]+\s[G|M|Káàéò]?)'
    LIST_PARTITION_PATTERN = '(Ðàçäåë [0-9]+).*?([0-9]+ Gá|Ìá|Êá)'
    SELECT_DISK_VALIDATION_MESSAGE = 'Âûáðàí äèñê'

class EnLocale(LocaleInterface):
    LIST_DISK_PATTERN = '(Disk [0-9]+)\s+.+?\s+([0-9]+\s[GB|MB|KB|B]?)'
    LIST_PARTITION_PATTERN = '(Partition [0-9]+).*?([0-9]+ [GB|MB|KB|B])'
    LIST_VISIBLE_VOLUME_PATTERN = '(Volume\s+[0-9]+).*?\s([a-zA-z]{1})\s.*?([0-9]+ [GB|MB|KB|B])'
    LIST_OS_PATTERN = '\s([a-zA-z]{1})\s.*?\s(OS)\s'
    SELECT_DISK_VALIDATION_MESSAGE = 'is now the selected disk'

class ZhLocale(LocaleInterface):
    LIST_DISK_PATTERN = '(磁盘 [0-9]+)\s+.+?\s+([0-9]+\s[GB|MB|KB|B]?)'
    LIST_PARTITION_PATTERN = '(分区\s+[0-9]+).*?([0-9]+ [GB|MB|KB|B])'
    LIST_VISIBLE_VOLUME_PATTERN = '(卷\s+[0-9]+).*?\s([a-zA-z]{1})\s.*?([0-9]+ [GB|MB|KB|B])'
    LIST_OS_PATTERN = '\s([a-zA-z]{1})\s.*?\sOS\s'
    SELECT_DISK_VALIDATION_MESSAGE = '现在是所选磁盘'