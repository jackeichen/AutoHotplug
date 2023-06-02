''' @package VDBenchJob
A module realizing a vdbench job run.
'''
import os
import re
import timeit
import platform
sysstr = platform.system()
# for accross a show issue
timeit.default_timer()
#
from src.log_hotplug import logger
from src.lib import subprocess_run,shutil,check_dir,localtime1,NonBlockSubprocess
from src.script_path import vdbench_tool_path,temp_path,vdbench_para_file_path,LOGS_path

class VDBenchJob(object):
    def __init__(self, job_id):
        self.__job_id = str(job_id)
        if len(self.__job_id) > 3:
            raise RuntimeError("job_id too long in VDBenchJob, it should be no more than 6 bytes")
        ## vdbench path
        self.__vdbenchPath = vdbench_tool_path
        #
        if sysstr == "Linux":
            os.system("chmod 755 %s" % self.__vdbenchPath)
        ## vdbench version
        self.__vdbenchVersion = None
        ##
        self.__normal_output = os.path.join(LOGS_path,"vdbenchoutput")
        check_dir(self.__normal_output)
        ##
        self.__disk_index_mapping = {}
        #
        self.__disk_index = 0
        
    def get_disk_index(self, disk_id):
        if disk_id not in self.__disk_index_mapping:
            self.__disk_index_mapping[disk_id] = str(self.__disk_index)
            self.__disk_index += 1
            if len(str(self.__disk_index)) > 3:
                raise RuntimeError("Too many disk stoerd in vdbench disk_index")
        return self.__disk_index_mapping[disk_id]

    @property
    def sd_name_with_job_id(self):
        return ("sd%s" % self.__job_id)
    
    def sd_name_full(self, disk_id):
        return ("%s%s" % (self.sd_name_with_job_id, self.get_disk_index(disk_id)))
    
    def __get_std_file_path(self, dev_id):
        return os.path.join(temp_path, self.sd_name_full(dev_id))

    def clean_job(self, file_path=None):
        if not file_path:
            file_path = os.path.abspath('.')
        for root,dirs,files in os.walk(file_path, topdown=True):
            ## just check the root dir
            if root == file_path:
                for file in files:
                    if self.sd_name_with_job_id in file and (".jnl" in file or ".map" in file):
                        full_path = os.path.join(root, file)
                        os.remove(full_path)
                break
        ##
        self.__disk_index_mapping.clear()
        self.__disk_index = 0

    def getToolVersion(self):
        ''' Return the current Vdbench version string. '''
        return self.__vdbenchVersion

    def setToolVersion(self,VerStr):
        ''' Set the used VDBench version (useful if loading from xml). '''
        self.__vdbenchVersion = VerStr
    
    def tool_test(self):
        output_temp = os.path.join(temp_path, 'vdbench_test_output')
        cmd = "%s -t -o %s" % (self.__vdbenchPath, output_temp)
        return os.system(cmd)
    
    def initialize(self):
        ''' Initialize VDBench path and version. '''
        output_temp = os.path.join(temp_path, 'vdbench_test_output')
        cmd = [self.__vdbenchPath, '-t', '-o', output_temp]
        if sysstr == "Windows":
            rc,stdout,stderr = subprocess_run(cmd, shell=True)
        else:
            rc,stdout,stderr = subprocess_run(cmd)
        if rc != 0:
            logger.error("# Error: command %s returned an error code." % ' '.join(cmd))
            raise RuntimeError("ReturnCode: %s, Error: %s" % (rc,stderr))

        stdout = stdout.split('/n')
        for i in stdout:
            if "Vdbench distribution:" in i:
                g = re.search(r"vdbench(\d+)", i)
                if g:
                    self.__vdbenchVersion = g[1]
        ##
        self.clean_job()
    
    def precondition_128k_seqw_coldData(self, disk_id, disk_path, io_range):
        output = os.path.join(self.__normal_output, 'precondition_128k_seqw_coldData_%s' % disk_id)
        para_file = os.path.join(vdbench_para_file_path,'precondition_128k_seqw_coldData.vd')
        if sysstr == "Windows":
            cmd = "%s -o %s -f %s -vr -jm sd_name=%s lun=%s range=%s" % (self.__vdbenchPath, output, para_file, self.sd_name_full(disk_id), disk_path, io_range)
        else:
            cmd = "%s -o %s -f %s -vr -jm sd_name=%s lun=%s range='%s'" % (self.__vdbenchPath, output, para_file, self.sd_name_full(disk_id), disk_path, io_range)
        my_run = NonBlockSubprocess(self.__get_std_file_path(disk_id))
        my_run.run_cmd(cmd)
        return my_run

    def precondition_128k_coldData_val(self, disk_id, disk_path, io_range):
        output = os.path.join(self.__normal_output, 'precondition_128k_coldData_val_%s' % disk_id)
        para_file = os.path.join(vdbench_para_file_path,'precondition_128k_coldData_val.vd')
        if sysstr == "Windows":
            cmd = "%s -o %s -f %s -jro sd_name=%s lun=%s range=%s" % (self.__vdbenchPath, output, para_file, self.sd_name_full(disk_id), disk_path, io_range)
        else:
            cmd = "%s -o %s -f %s -jro sd_name=%s lun=%s range='%s'" % (self.__vdbenchPath, output, para_file, self.sd_name_full(disk_id), disk_path, io_range)
        my_run = NonBlockSubprocess(self.__get_std_file_path(disk_id))
        my_run.run_cmd(cmd)
        return my_run
        
    def test_4k_randrw_60s(self, disk_id, disk_path, io_range, rdpct):
        output = os.path.join(self.__normal_output, 'test_4k_randrw_60s_%s_%s' % (localtime1(), disk_id))
        if sysstr == "Windows":
            para_file = os.path.join(vdbench_para_file_path,'test_4k_randrw_60s_forwin.vd')
            cmd = "%s -o %s -f %s sd_name=%s lun=%s range=%s" % (self.__vdbenchPath, output, para_file, self.sd_name_full(disk_id), disk_path, io_range) 
        else:
            para_file = os.path.join(vdbench_para_file_path,'test_4k_randrw_60s.vd')
            cmd = "%s -o %s -f %s -vr sd_name=%s lun=%s range='%s' rdpct=%s" % (self.__vdbenchPath, output, para_file, self.sd_name_full(disk_id), disk_path, io_range, rdpct) 
        my_run = NonBlockSubprocess(self.__get_std_file_path(disk_id))
        my_run.run_cmd(cmd)
        return my_run
