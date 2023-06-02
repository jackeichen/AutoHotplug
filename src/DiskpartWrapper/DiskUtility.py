import sys

from WinDiskpartWrapper import WindowsDiskUtility
from DiskUtilityModule import DiskUtilExceptions


def main():
    """  Main method of application.
    Usage:
        View Disk information when run script without input parameters
        View Partition information for disk id (int) passed as first input parameters
    """
    try:
        if(len(sys.argv))==1:
            diskUtil = WindowsDiskUtility()
            diskUtil.listDisk()

        if(len(sys.argv))==2:
                diskUtil = WindowsDiskUtility()
                diskUtil.listDiskPartition(sys.argv[1])
    except DiskUtilExceptions as e:
        print ("ERROR! " + e.message)

if __name__=="__main__":
    main()