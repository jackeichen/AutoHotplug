#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#Author: Gao Zhihua
#Date: 2018/03/29
class RequestDB(object):
    def __init__(self):
        self.request_raw = []
    
    def load_request(self, request_raw):
        self.request_raw = request_raw
    
    @property
    def request_id(self):
        return self.request_raw[0]
    
    @property
    def request_data(self):
        return self.request_raw[1]


class RequestGen(object):
    def __init__(self):
        self.request_raw = []
    
    def gen_request(self, request_id, request_data=None):
        self.request_raw.clear()
        self.request_raw.append(request_id)
        self.request_raw.append(request_data)
        return self.request_raw

    
class ReplyDB(object):
    def __init__(self):
        self.reply_raw = []
    
    def load_reply(self, reply_raw):
        self.reply_raw = reply_raw
    
    @property
    def return_code(self):
        return self.reply_raw[0]
    
    @property
    def reply_data(self):
        return self.reply_raw[1]


class ReplyGen(object):
    def __init__(self):
        self.reply_raw = []
    
    def gen_reply(self, return_code, reply_data=None):
        self.reply_raw.clear()
        self.reply_raw.append(return_code)
        self.reply_raw.append(reply_data)
        return self.reply_raw

        
