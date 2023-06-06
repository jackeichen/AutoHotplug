#
import os
import time
import shutil
import subprocess

def sb_convert(target, out_t):
    '''
    string or bytes convert what we want
    
    args:
      target   target object
      out_t    output type in (bytes,str)
    output:
      handled object
    '''
    if out_t in (bytes, str):
        if not isinstance(target, out_t):
            if out_t == bytes:
                target = target.encode()
            else:
                for encode_t in ("UTF-8", "GBK", "GB2312"):
                    try:
                        target = target.decode(encoding=encode_t)
                    except:
                        pass
                    else:
                        break
        return target

def subprocess_run(cmd, shell=False):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
    (stdout, stderr) = p.communicate()
    stdout = sb_convert(stdout, str)
    stderr = sb_convert(stderr, str)
    return p.returncode,stdout,stderr

def run_cmd(cmd, shell=False, check_stderr=True): # self
    rc,stdout,stderr = subprocess_run(cmd, shell=shell)
    if rc or (check_stderr and stderr):
        raise RuntimeError("Run cmd error: %s, return code->%s, err->%s" % (cmd,rc,stderr))
    return stdout

def win_cmd_exist(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (stdout, stderr) = p.communicate()
    return (p.returncode == 0)


def string2dictBycolon(string):
    d = {}
    for i in string.split('\n'):
        index = i.find(":")
        if index > 0:
            key = i[0:index].strip()
            value = i[(index+1):].strip()
            if key:
                d[key] = value
    return d


class NonBlockSubprocess(object):
    def __init__(self, std_file_path):
        self.std_file_path = std_file_path
        self.__stdout_file_path = open("%s.stdout" % self.std_file_path, 'w')
        self.__stderr_file_path = open("%s.stderr" % self.std_file_path, 'w')
        self.proc = None
        self.__cmd = ''
    
    def close(self):
        self.proc.wait()
        self.__stdout_file_path.close()
        self.__stderr_file_path.close()
    
    def wait_done(self):
        self.proc.wait()
        self.close()
        return self.proc.returncode

    def run_cmd(self, cmd):
        self.__cmd = cmd
        self.proc = subprocess.Popen(cmd, shell=True, stdout=self.__stdout_file_path,stderr=self.__stderr_file_path,universal_newlines=True)
        return self
    
    def get_cmd(self):
        return self.__cmd
    
    
class ConfigF(object):
    def __init__(self):
        self._config_file = None
        self.__para_dict = {}
    
    @property
    def para_dict(self):
        return self.__para_dict
    
    def _handle_value(self, v):
        if v.isdigit():
            v = int(v)
        elif v == 'True':
            v = True
        elif v == 'False':
            v = False
        return v
    
    def load(self, file_path):
        if not os.path.exists(file_path):
            raise RuntimeError("Config file not found")
        self._config_file = file_path
        self.__para_dict.clear()
        with open(self._config_file, 'r') as f:
            while True:
                temp = f.readline()
                index = temp.find('#')
                if index >= 0:
                    temp = temp[0:index]
                if temp:
                    index = temp.find(":")
                    if index >= 0:
                        key = temp[0:index].strip()
                        value = temp[(index+1):].strip()
                        self.__para_dict[key] = self._handle_value(value)
                else:
                    break
    def save(self):
        if self._config_file:
            with open(self._config_file, 'w') as f:
                for k,v in sorted(self.__para_dict.items()):
                    f.write(k)
                    f.write(': ')
                    f.write(str(v))
                    f.write('\n')
        else:
            raise RuntimeError("Load config first")
    
    def _gen_raw(self, file_path, raw_dict, force_create=False):
        if os.path.exists(os.path.dirname(file_path)):
            self._config_file = file_path
        elif force_create:
            os.makedirs(os.path.dirname(file_path))
            self._config_file = file_path
        else:
            raise RuntimeError("file path should exist")
        if isinstance(raw_dict, dict):
            self.__para_dict = raw_dict.copy()
        else:
            raise RuntimeError("")
        self.save()

def localtime():
    return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))

def localtime1():
    return time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))

def check_dir(dir, create=True):
    if os.path.exists(dir):
        return 1
    else:
        if create:
            os.makedirs(dir)
            return 1
        else:
            return 0
            
def remake_dir(d):
    if os.path.exists(d):
        shutil.rmtree(d)
    return os.makedirs(d)
