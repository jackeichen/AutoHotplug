# -*- coding: UTF-8 -*-
#Author: Gao Zhihua
#Date: 2018/03/29
import traceback

from src.hotplug import HotPlugQuarch,HotPlugManual
from src.CSProtocal import RequestDB,ReplyGen
from src.log_hotplug import logger

##
ClientReturnCodeCommon = {0: "success",
                          201: "Request ID not defined.",
                          211: "Need init hotplug before use it.",
                          255: "Common Error Code, error in function handle request."}
##

class Client(object):
    def __init__(self, queue_recv, queue_send, shared_info):
        self.__shared_info = shared_info
        self.__queue_recv = queue_send
        self.__queue_send = queue_recv
        ##
        self.request_db = RequestDB()
        self.reply_gen = ReplyGen()
        ##
        self.__hotplug = None
        self.__run_status = True

    def _handle_request(self, request):
        self.request_db.load_request(request)
        if self.request_db.request_id == 0:  # do nothing
            reply = self.reply_gen.gen_reply(0)
        elif self.request_db.request_id == 1: # close client
            self.__run_status = False
            reply = self.reply_gen.gen_reply(0)
        elif self.request_db.request_id == 2: # init hotplug
            request_data = self.request_db.request_data
            ConnID,job_id,io_t = request_data
            if "manual" in ConnID:
                self.__hotplug = HotPlugManual(ConnID,job_id,self.__shared_info)
            else:
                self.__hotplug = HotPlugQuarch(ConnID,job_id,self.__shared_info)
            self.__hotplug.setup_io_jobs(io_t)
            self.__hotplug.setup_periphery_device()
            reply = self.reply_gen.gen_reply(0, [ConnID,job_id,self.__hotplug.io_jobs.getToolVersion()])
        elif self.request_db.request_id == 3: # close hotplug
            if self.__hotplug:
                self.__hotplug.close()
                reply = self.reply_gen.gen_reply(0)
            else:
                reply = self.reply_gen.gen_reply(211, ClientReturnCodeCommon.get(211))
        elif self.request_db.request_id == 4: # run hotplug test case
            request_data = self.request_db.request_data
            args,kwargs = request_data
            if self.__hotplug:
                test_rc = self.__hotplug._test_process(*args, **kwargs)
                reply = self.reply_gen.gen_reply(0, test_rc)
            else:
                reply = self.reply_gen.gen_reply(211, ClientReturnCodeCommon.get(211))
        elif self.request_db.request_id == 5: # config hot swap
            hot_pull_type,hot_pull_para,hot_push_type,hot_push_para,off_time,on_time = self.request_db.request_data
            if self.__hotplug:
                if hot_pull_type is not None:
                    self.__hotplug.hot_swap_config.hot_pull_type = hot_pull_type
                if hot_pull_para is not None:
                    self.__hotplug.hot_swap_config.hot_pull_para = hot_pull_para
                if hot_push_type is not None:
                    self.__hotplug.hot_swap_config.hot_push_type = hot_push_type
                if hot_push_para is not None:
                    self.__hotplug.hot_swap_config.hot_push_para = hot_push_para
                if off_time is not None:
                    self.__hotplug.hot_swap_config.off_time = off_time
                if on_time is not None:
                    self.__hotplug.hot_swap_config.on_time = on_time
                reply = self.reply_gen.gen_reply(0)
            else:
                reply = self.reply_gen.gen_reply(211, ClientReturnCodeCommon.get(211))
        elif self.request_db.request_id == 6: # Get the Periphery Device Name
            if self.__hotplug:
                replay_data = [self.__hotplug.periphery_device_name,]
                reply = self.reply_gen.gen_reply(0, replay_data)
            else:
                reply = self.reply_gen.gen_reply(211, ClientReturnCodeCommon.get(211)) 
        elif self.request_db.request_id == 11: # check infomation
            if self.__hotplug:
                replay_data = []
                replay_data.append(self.__hotplug._periphery_device.periphery_identify())
                temp = []
                for _disk_info in self.__hotplug._periphery_device.disk_info:
                    temp.append([_disk_info.disk_id, _disk_info.disk_sn, _disk_info.interface, _disk_info.disk_type])
                replay_data.append(temp)
                reply = self.reply_gen.gen_reply(0, replay_data)
            else:
                reply = self.reply_gen.gen_reply(211, ClientReturnCodeCommon.get(211))
        elif self.request_db.request_id == 12: # run quarch hotplug test case special
            if self.__hotplug:
                request_data = self.request_db.request_data
                replay_data = []
                for test_id,cycles,source_delay in request_data:
                    if test_id == 0:
                        test_rc = self.__hotplug.test_case0(cycles,source_delay)
                        replay_data.append(test_rc)
                    elif test_id == 1:
                        test_rc = self.__hotplug.test_case1(cycles,source_delay)
                        replay_data.append(test_rc)
                    elif test_id == 2:
                        test_rc = self.__hotplug.test_case2(cycles,source_delay)
                        replay_data.append(test_rc)
                    elif test_id == 10:
                        test_rc = self.__hotplug.test_case10(cycles,source_delay)
                        replay_data.append(test_rc)
                    else:
                        test_rc = 250
                        replay_data.append(test_rc)
                reply = self.reply_gen.gen_reply(0, replay_data)
            else:
                reply = self.reply_gen.gen_reply(211, ClientReturnCodeCommon.get(211))
        elif self.request_db.request_id == 13: # run tool test
            if self.__hotplug:
                replay_data = []
                temp = self.__hotplug._periphery_device.periphery_test()
                replay_data.append(temp)
                temp = self.__hotplug.io_jobs.tool_test()
                replay_data.append(temp)
                reply = self.reply_gen.gen_reply(0, replay_data)
            else:
                reply = self.reply_gen.gen_reply(211, ClientReturnCodeCommon.get(211))
        elif self.request_db.request_id == 14: # run manual hotplug test case special
            if self.__hotplug:
                request_data = self.request_db.request_data
                replay_data = []
                for test_id,cycles in request_data:
                    if test_id == 0:
                        test_rc = self.__hotplug.test_case0(cycles)
                        replay_data.append(test_rc)
                    elif test_id == 1:
                        test_rc = self.__hotplug.test_case1(cycles)
                        replay_data.append(test_rc)
                    elif test_id == 2:
                        test_rc = self.__hotplug.test_case2(cycles)
                        replay_data.append(test_rc)
                    elif test_id == 10:
                        test_rc = self.__hotplug.test_case10(cycles)
                        replay_data.append(test_rc)
                    else:
                        test_rc = 250
                        replay_data.append(test_rc)
                reply = self.reply_gen.gen_reply(0, replay_data)
            else:
                reply = self.reply_gen.gen_reply(211, ClientReturnCodeCommon.get(211))
        elif self.request_db.request_id == 16: # config IO job
            if self.__hotplug:
                request_data = self.request_db.request_data
                self.__hotplug.set_io_cfg(request_data)
                reply = self.reply_gen.gen_reply(0)
            else:
                reply = self.reply_gen.gen_reply(211, ClientReturnCodeCommon.get(211))
        else:
            reply = self.reply_gen.gen_reply(201)
        return reply

    def run(self):
        while self.__run_status:
            request = self.__queue_recv.get()
            try:
                reply = self._handle_request(request)
            except:
                reply = self.reply_gen.gen_reply(255, traceback.format_exc())
            self.__queue_send.put(reply)


def run_client(queue_recv, queue_send, shared_info):
    with shared_info.get("RLockCop"):
        shared_info["AliveThread"] += 1
    try:
        client = Client(queue_recv, queue_send, shared_info)
        client.run()
    except:
        pass
    with shared_info.get("RLockCop"):
        shared_info["AliveThread"] -= 1
    return 0
        
