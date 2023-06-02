""" Module contains interfaces for working with HDD utility """
from abc import ABCMeta, abstractmethod

class DiskUtilityInterface(object):
    """ Class for working with HDD utility
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def listDisk(self):
        """ View size of each disk in the computer
        :return:list[diskId, disk size]
        """
        pass

    @abstractmethod
    def listDiskPartition(self, diskID):
        """View size of each partition on the in-focus disk"
        :param diskID: (int) Disk id
        :return: list[partitionId, partitionSize]
        """
        pass

class DiskUtilExceptions(Exception):
    pass