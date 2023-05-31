#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
# author: mark.hsieh
import os
import logging
import time
import math
import json

from common import myqueue

class MySendTools(object):
    def __init__(self, logger) -> None:
        super().__init__()
        self.logger = logger
        self.__run = False
        self.__event_stop = None
        self.__queue_request = None
        self.__queue_result = None
        self.__callback = None
        self.logger.info("{} already loaded finish.".format(__name__))
    
    def run(self, event, queue_req, queue_res, cb):
        self.__run = True
        self.__event_stop = event
        self.__queue_request = queue_req
        self.__queue_result = queue_res
        self.__callback = cb
        
        while self.__run is True:
            if self.__event_stop.is_set():
                self.__run = False
                self.__event_stop.clear()
                
                self.logger.info("{} stoping...".format(__name__))
            else:
                l_dict = self.__popFromQueueRes()
                if l_dict is not None:
                    self.__callback(l_dict)
                else:
                    time.sleep(0.1)

    def __popFromQueueRes(self):
        '''
        __popFromQueueRes ()
        PARAMETER:
            NONE
        OUTPUT:
            dict data
        '''
        l_msg = None
        l_msg = self.__queue_result.pop()

        if l_msg is None:
            return None
        else:
            # It can be used to parse a valid JSON string and convert it into a Python Dictionary. 
            return json.loads(l_msg)

