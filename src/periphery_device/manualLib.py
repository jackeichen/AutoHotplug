#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#Author: Gao Zhihua
#Date: 2018/03/29
class ManualHotSwapModule(object):
    def __init__(self, ConnID):
        self.ConnID = ConnID
        self.open()
        ##
        self._identify = 'ManualLib v0.1'
        ## PLUGGED,PULLED
        self.__power_state = "PLUGGED"  # dummy value

    def open(self):
        pass

    def close(self):
        pass

    def product_name(self):
        return 'Manual Type'

    def get_power_state(self):
        return self.__power_state

    def set_power_state(self, state):
        if state == 'UP':
            answer = input("Please insert your %s, and press anykey to continue." % self.ConnID)
            self.__power_state = "PLUGGED"
        elif state == 'DOWN':
            answer = input("Please remove your %s, and press anykey to continue." % self.ConnID)
            self.__power_state = "PULLED"
        else:
            print ("Set power state should in UP|DOWN")
            return 1
        return 0

    def run_hot_swap(self, off_time):
        self.set_power_state("DOWN")
        time.sleep(off_time)
        self.set_power_state("UP")


def get_manual_module(ConnID):
    return ManualHotSwapModule(ConnID)
