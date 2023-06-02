''' @package FioJob
A module realizing a fio job run.
'''
import re
import timeit
# for accross a show issue
timeit.default_timer()
#
from src.log_hotplug import logger
from src.lib import subprocess_run


class FioJob(object):
    '''
    A class configuring the fio job.
    '''
    ## Position of read IOPS in the fio terse output.
    terseIOPSReadPos = 7

    ## Position of write IOPS in the fio terse output.
    terseIOPSWritePos = 48

    ## Position of write total IO in the fio terse output
    terseTotIOWritePos = 46

    ## Start Position of write latencies in fio terse output
    terseLatStartWritePos = 78

    ## Start Position of read latencies in fio terse output
    terseLatStartReadPos = 37

    ## Postion of total read throughput.
    terseTPReadPos = 6

    ## Postion of total write throughput.
    terseTPWritePos = 47
    
    ## Postion of total read_kb.
    terseTPRead_kb = 5 
    
    ## Postion of total write_kb.
    terseTPWrite_kb = 46
    
    ## Postion of cpu_sys.
    terseCpuSys = 88

    def __init__(self):
        ''' The constructor '''
        ## Fio path
        self.__fioPath = None
        ## Fio version
        self.__fioVersion = None
        ##

    def __str__(self):
        ''' Return a string representation of the fio executable. '''   
        res = "fio: " + self.__fioPath + ", " + self.__fioVersion
        return res

    def initialize(self):
        ''' Initialize Fio path and version. '''
        rc,stdout,stderr = subprocess_run(['which', 'fio'])
        if rc != 0:
            logger.error("# Error: command 'which fio' returned an error code.")
            raise RuntimeError("which fio command error")

        self.__fioPath = stdout.rstrip("\n")
        rc,stdout,stderr = subprocess_run(['fio','--version'])
        self.__fioVersion = stdout

    def getToolVersion(self):
        ''' Return the current Fio version string. '''
        return self.__fioVersion

    def setToolVersion(self,fioStr):
        ''' Set the used Fio version (useful if loading from xml). '''
        self.__fioVersion = fioStr
    
    def tool_test(self):
        print ("TBD now")

    def checkToolVersion(self):
        ''' Check if the Fio version is high enough. '''
        if self.__fioVersion != None:
            match = re.search(r'[\d\.]+',self.__fioVersion)
            if match == None:
                logger.error("# Error: checking fio version returned a none string.")
                raise RuntimeError("fio version string error")
            version = match.group().split('.')
            if int(version[0]) < 2:
                logger.error("# Error: the fio version is to old, ensure to use > 2.0.3.")
                raise RuntimeError("fio version to old error")
            if int(version[0]) >= 2:
                if int(version[1]) == 0:
                    if int(version[2]) < 3:
                        logger.error("# Error: the fio version is to old, ensure to use > 2.0.3.")
                        raise RuntimeError("fio version to old error")

    def getKVArgs(self):
        ''' Return the current configured Fio key value arguments. '''
        return self.__fioKVArgs
    
    def getSglArgs(self):
        ''' Return the current configured Fio single key arguments. '''
        return self.__fioSglArgs
    
    def addKVArg(self,key,value):
        ''' Add a key value pair as an argument to fio.
        @param key Name of the option for Fio.
        @param value Value for the given Fio option.
        '''
        self.__fioKVArgs[key] = value
        
    def addSglArg(self,key):
        ''' Add a single value option to fio argument list.
        @param key Name of the option being added.
        ''' 
        self.__fioSglArgs.append(key)
    
    def removeKVArgs(self, key):
        if key in self.__fioKVArgs:
            self.__fioKVArgs.pop(key)
    
    def removeSglArg(self,key):
        while key in self.__fioSglArgs:
            self.__fioSglArgs.remove(key)
        
    def prepKVArgs(self):
        ''' Generate an argument list out of the dictionary suited for fio. '''
        argList = [self.__fioPath]
        for k,v in self.__fioKVArgs.items():
            argList.append('--' + k + '=' + v)
        return argList
    
    def prepSglArgs(self,argList):
        ''' Generate an argument list out of the single key arguments. '''
        for k in self.__fioSglArgs:
            argList.append('--' + k)
        return argList
        
    def start(self, get_runtime=False):
        ''' Start a Fio job with its argument list.
        The argument list defines the parameters given to Fio.
        @return [True,standard output] of the Fio test or [False,0] on error.
        '''
        args = self.prepKVArgs()
        args = self.prepSglArgs(args)
        logger.info('%s',args)
        if len(args) == 0:
            logger.error("Error: Fio argument list is empty.")
            exit(1)
        if self.__TurnOffIO:
            import time
            print ("Sleeping 0.5s to simulate fio.")
            print (args)
            time.sleep(0.5)
            rc = 0
            stdout = '3;fio-3.7;my_perf;0;0;108759296;1812503;28320;60005;1;707;20.805113;8.930855;232;11885;4494.007157;108.520682;1.000000%=4292;5.000000%=4358;10.000000%=4358;20.000000%=4423;30.000000%=4423;40.000000%=4489;50.000000%=4489;60.000000%=4489;70.000000%=4554;80.000000%=4554;90.000000%=4620;95.000000%=4685;99.000000%=4751;99.500000%=4816;99.900000%=4947;99.950000%=5013;99.990000%=6062;0%=0;0%=0;0%=0;259;11915;4515.545253;108.518330;444800;460800;24.998278%;453094.533333;1156.494563;0;0;0;0;0;0;0.000000;0.000000;0;0;0.000000;0.000000;1.000000%=0;5.000000%=0;10.000000%=0;20.000000%=0;30.000000%=0;40.000000%=0;50.000000%=0;60.000000%=0;70.000000%=0;80.000000%=0;90.000000%=0;95.000000%=0;99.000000%=0;99.500000%=0;99.900000%=0;99.950000%=0;99.990000%=0;0%=0;0%=0;0%=0;0;0;0.000000;0.000000;0;0;0.000000%;0.000000;0.000000;7.119168%;17.978118%;1234704;0;5254;0.1%;0.1%;0.1%;0.1%;0.1%;100.0%;0.0%;0.00%;0.00%;0.00%;0.00%;0.00%;0.00%;0.01%;0.01%;0.01%;0.01%;0.01%;0.05%;99.94%;0.01%;0.00%;0.00%;0.00%;0.00%;0.00%;0.00%;0.00%;0.00%;nvme0n1;1695997;0;0;0;7608157;0;6782784;99.95%'
            stderr = ''
            return True,stdout
        else:
            if get_runtime:
                t = timeit.default_timer()
                rc,stdout,stderr = subprocess_run(args)
                t = timeit.default_timer() - t
                # output
                if stderr != '':
                    logger.error("Fio encountered an error: " + stderr)
                    return [False,'',t]
                else:
                    return [True,stdout,t]
            else:
                rc,stdout,stderr = subprocess_run(args)
                ## output
                if stderr != '':
                    logger.error("Fio encountered an error: " + stderr)
                    return [False,'']
                else:
                    return [True,stdout]
        
    def getIOPS(self,fioOut):
        '''
        Parses the average IOPS out of the Fio result output.
        @param fioOut The output of the Fio performance test.
        @return Sum of read IOPS and write IOPS.
        '''
        #index 7 iops read
        #index 48 iops write
        fioTerse = fioOut.split(';')
        return int(fioTerse[FioJob.terseIOPSReadPos]) + int(fioTerse[FioJob.terseIOPSWritePos])
       
    def getIOPSRead(self,fioOut):
        '''
        Parses the average read IOPS out of the fio result output.
        @param fioOut The output of the fio performance test.
        @return Read IOPS
        '''
        #index 7 iops read
        fioTerse = fioOut.split(';')
        return int(fioTerse[FioJob.terseIOPSReadPos])
    
    def getIOPSWrite(self,fioOut):
        '''
        Parses the average write IOPS out of the Fio result output.
        @param fioOut The output of the Fio performance test.
        @return Write IOPS
        '''
        #index 48 iops write
        fioTerse = fioOut.split(';')
        return int(fioTerse[FioJob.terseIOPSWritePos])
       
    def getTotIOWrite(self,fioOut):
        '''
        Parses the write total IO out of the Fio result output.
        @param fioOut The output of the Fio performance test.
        @return Write total IO in KB.
        '''
        #index 46 write total IO
        fioTerse = fioOut.split(';')
        return int(fioTerse[FioJob.terseTotIOWritePos])
    
    def getWriteLats(self,fioOut):
        '''
        Parses the write total latencies out of the Fio result output.
        @param fioOut The output of the Fio performance test.
        @return [min,max,mean] total write latencies in microseconds.
        '''
        #index 78 write total latency
        fioTerse = fioOut.split(';')
        return [float(fioTerse[FioJob.terseLatStartWritePos]),
                float(fioTerse[FioJob.terseLatStartWritePos + 1]),
                float(fioTerse[FioJob.terseLatStartWritePos + 2])]
        
    def getReadLats(self,fioOut):
        '''
        Parses the read total latencies out of the Fio result output.
        @param fioOut The output of the Fio performance test.
        @return [min,max,mean] total read latencies in microseconds.
        '''
        #index 78 write total latency
        fioTerse = fioOut.split(';')
        return [float(fioTerse[FioJob.terseLatStartReadPos]),
                float(fioTerse[FioJob.terseLatStartReadPos + 1]),
                float(fioTerse[FioJob.terseLatStartReadPos + 2])]
        
    def getTotLats(self,fioOut):
        '''
        Parses the read+write total latencies out of the Fio result output.
        @param fioOut The output of the Fio performance test.
        @return [min,max,mean] total latencies in microseconds.
        '''
        #index 78 write total latency
        fioTerse = fioOut.split(';')
        return [float(fioTerse[FioJob.terseLatStartReadPos]) + 
                      float(fioTerse[FioJob.terseLatStartWritePos]),
                float(fioTerse[FioJob.terseLatStartReadPos + 1]) + 
                      float(fioTerse[FioJob.terseLatStartWritePos + 1]),
                float(fioTerse[FioJob.terseLatStartReadPos + 2]) + 
                      float(fioTerse[FioJob.terseLatStartWritePos + 2])]

    def getTPRead(self,fioOut):
        '''
        Parses the read bandwidth of the Fio result output.
        @param fioOut The output of the Fio performance test.
        @return Read total bandwidth.
        '''
        #index 6 write total IO
        fioTerse = fioOut.split(';')
        return int(fioTerse[FioJob.terseTPReadPos])
        
    def getTPWrite(self,fioOut):
        '''
        Parses the write bandwidth of the Fio result output.
        @param fioOut The output of the Fio performance test.
        @return Write total bandwidth.
        '''
        #index 47 write total IO
        fioTerse = fioOut.split(';')
        return int(fioTerse[FioJob.terseTPWritePos])
    
    def getRWBytes(self, fioOut):
        '''
        Parses the read_kb of the Fio result output.
        @param fioOut The output of the Fio performance test.
        @return .
        '''
        #index 5 read_kb,46 write_kb
        fioTerse = fioOut.split(';')
        return (int(fioTerse[FioJob.terseTPRead_kb])+int(fioTerse[FioJob.terseTPWrite_kb]))*1024
        
    def getCpuSys(self,fioOut):
        '''
        Parses the cpu syst of the Fio result output.
        @param fioOut The output of the Fio performance test.
        @return sys cpu.
        '''
        #index 47 write total IO
        fioTerse = fioOut.split(';')
        return float(fioTerse[FioJob.terseCpuSys].strip("%"))
        