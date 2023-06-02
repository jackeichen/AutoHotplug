# -*- coding: UTF-8 -*-
#Author: Gao Zhihua
#Date: 2018/03/29
import time
import queue
import threading
from src.hotplug_client import run_client
from src.CSProtocal import RequestGen,ReplyDB
from src.log_hotplug import logger


class ClientObj(object):
    def __init__(self):
        self.thread = None
        self.client_id = None
        self.queue_send = None
        self.queue_recv = None
    
    def send_request(self, request, send_timeout=None):
        self.queue_send.put(request, timeout=send_timeout)
    
    def recv_request(self, recv_timeout=None):
        return self.queue_recv.get(timeout=recv_timeout)


class Server(object):
    def __init__(self):
        self.__clients = {}
        self.__shared_info = {"RLockCop":threading.RLock(),
                              "RLockHotSwap": threading.RLock(),
                              "BarrierHotSwap": None,# This will be init in the test
                              "AliveThread": 0,}
        self.__max_queue_size_per_client = 10
        ##
        self.__inner_client_id = 0
        ##
        self.request_gen = RequestGen()
        self.reply_db = ReplyDB()
    
    def get_clients_pool(self):
        return self.__clients
    
    def start_one_client(self):
        client_obj = ClientObj()
        #
        client_obj.client_id = self.__inner_client_id
        self.__inner_client_id += 1
        #
        client_obj.queue_send = queue.Queue(self.__max_queue_size_per_client)
        client_obj.queue_recv = queue.Queue(self.__max_queue_size_per_client)
        #
        client_obj.thread = threading.Thread(target=run_client, args=(client_obj.queue_recv,client_obj.queue_send,self.__shared_info))
        client_obj.thread.daemon = True
        client_obj.thread.start()
        ##
        self.__clients[client_obj.client_id] = client_obj
        ## check if alive
        time.sleep(0.3)
        self.check_client_alive(client_obj.client_id)
        return client_obj.client_id
    
    def send_request(self, client_id, request_id, request_data=None, send_timeout=None):
        client_obj = self.__clients.get(client_id)
        request = self.request_gen.gen_request(request_id,request_data)
        logger.debug("%s sending request: %s" % (client_id, request))
        client_obj.send_request(request, send_timeout=send_timeout)
    
    def recv_request(self, client_id, recv_timeout=None):
        client_obj = self.__clients.get(client_id)
        reply = client_obj.recv_request(recv_timeout=recv_timeout)
        logger.debug("%s recving reply %s" % (client_id, reply))
        self.reply_db.load_reply(reply)
        if self.reply_db.return_code == 0:
            logger.debug("Request success")
        else:
            logger.debug("Request return code: %s, return data: %s" % (self.reply_db.return_code, self.reply_db.reply_data))
        return self.reply_db
    
    def REPQ(self, client_id, request_id, request_data=None, send_timeout=None, recv_timeout=None):
        self.send_request(client_id, request_id, request_data=request_data, send_timeout=send_timeout)
        return self.recv_request(client_id, recv_timeout=recv_timeout)

    def close_client(self, client_id=None):
        if client_id is None:
            # close all
            for client_id,client_obj in self.__clients.items():
                reply_db = self.REPQ(client_id, 1)
                if reply_db.return_code == 0:
                    logger.info("Client %s closed." % client_id)
                    client_obj.thread.join()
                    logger.info("Client %s Thread exit." % client_id)
                else:
                    logger.error("Client %s Not closed, return code: %s" % (client_id, reply_db.return_code))
        else:
            reply_db = self.REPQ(client_id, 1)
            if reply_db.return_code == 0:
                logger.info("Client: %s closed." % client_id)
                self.__clients.get(client_id).thread.join()
                logger.info("Client %s Thread exit." % client_id)
    
    def check_client_alive(self, client_id):
        reply_db = self.REPQ(client_id, 0)
        if reply_db.return_code == 0:
            logger.info("Client: %s alive." % client_id)
            return 0
        else:
            logger.info("Client reponse return code: %s." % reply_db.return_code)
        return 1
