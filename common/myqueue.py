#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
# author: mark.hsieh

import math  
import logging
import json

from queue import PriorityQueue
## queue module of python 3, support three type as below
# queue.Queue：FIFO 先進先出
# queue.LifoQueue：LIFO類似於堆疊 stack，即先進後出
# queue.PriorityQueue：優先級別越低越先出來，優先級用數字算就是越小越優先

class MyQueue(object):
    def __init__(self, logger, size=30, high_permission_has=0.25) -> None:
        super().__init__()
        self.__q = PriorityQueue(size+1) # avoid out of range.
        if (high_permission_has <= 0):
            self.__high_permission_max = 0
        else:
            self.__high_permission_max = round(size * high_permission_has)
        self.__normal_permission_max = size - self.__high_permission_max

        ## loop list .
        self.__high_push_count = 0
        self.__normal_push_count = 0
        self.__high_pop_count = 0
        self.__normal_pop_count = 0
        self.logger = logger
        self.logger.info("{} already loaded finish.".format(__name__))
    
    def clean(self):
        l_count_giveup_tasks = 0
        while self.isEmpty() is False:
            l_get_dict = self.__q.get_nowait()
            l_get_dict = None
            l_count_giveup_tasks += 1
        self.logger.info("{} drop {} tasks.".format(__name__, l_count_giveup_tasks))

    def __getHPIndex(self):
        l_index = 0
        l_next = -1
        l_still_been_queued = self.__high_push_count - self.__high_pop_count

        if self.__high_permission_max == 0:
            l_index = -1
        else:
            l_index = self.__high_push_count % self.__high_permission_max

        if l_index < 0:
            l_next = -1
        elif l_index >= self.__high_permission_max:
            l_next = 0
        else:
            l_next = l_index + 1

        if l_still_been_queued < self.__high_permission_max:
            return l_index, l_next
        else: # > or =
            return l_index, -1

    def __getNPIndex(self):
        l_index = (self.__normal_push_count % self.__normal_permission_max) + self.__high_permission_max
        l_still_been_queued = self.__normal_push_count - self.__normal_pop_count

        l_next = -1
        if l_index >= self.__normal_permission_max:
            l_next = 0 + self.__high_permission_max
        else:
            l_next = l_index + 1

        if l_still_been_queued < self.__normal_permission_max:
            return l_index, l_next
        else: # > or =
            return l_index, -1

    def isEmpty(self) -> bool:
        return self.__q.empty()

    def isFull(self, high_permission=False) -> bool:
        l_index_now = -1
        l_index_next = -1

        if self.__q.full() is True:
            return True
        elif high_permission is True and self.__high_permission_max > 0:
            l_index_now, l_index_next = self.__getHPIndex()
        elif high_permission is False:
            l_index_now, l_index_next = self.__getNPIndex()
        else: # no high_permission setting ... 
            l_index_now, l_index_next = self.__getNPIndex()

        if l_index_next == -1:
            return True
        else:
            return False
        # else:
        #     return False

    def getMaxLen(self) -> int:
        return self.__q.qsize()

    def push(self, item: str, high_permission=False):
        '''
        push()
        input: 
            item - string, json data 
            high_permission - boolean, let this data will 
                              queue to high priority queue or normal queue
        output:
            ack - boolean, success or not
            message - string, 
        '''
        l_resack = True
        l_resstr = "None"
        l_index_now = -1
        l_index_next = -1

        l_isFull = self.isFull(high_permission)

        if l_isFull is False and high_permission is True:
            l_index_now, l_index_next = self.__getHPIndex()
            self.__high_push_count += 1
            self.__q.put({l_index_next : item})
        elif l_isFull is True and high_permission is True:
            l_resack = False
            l_resstr = "high permission task queue already full."
        elif l_isFull is False and high_permission is False:
            l_index_now, l_index_next = self.__getNPIndex()
            self.__normal_push_count += 1
            self.__q.put({l_index_next : item})
        elif l_isFull is True and high_permission is False:
            l_resack = False
            l_resstr = "normal permission task queue already full."
        else:
            l_resack = False
            l_resstr = "unknown error"

        return l_resack, l_resstr

    def pop(self):
        # ref.:https://shengyu7697.github.io/python-queue/
        '''
        pop()
        INPUT:
            None
        OUTPUT:
            string: json data, or None
        '''
        l_get_dict = None
        l_get_keys = []
        if self.isEmpty() is True:
            return None
        else:
            '''
            ref.:
                https://stackoverflow.com/a/38560911
            '''
            try:
                # l_get_dict = self.__q.get(False)
                l_get_dict = self.__q.get_nowait()
            except Empty:
                l_get_dict = None
            self.__q.task_done()

            if l_get_dict is not None:
                for key in l_get_dict.keys():
                    l_get_keys.append(key)
                if len(l_get_keys) > 1:
                    self.logger.warning("why your queue keys: {} will be got at the same time.".format(l_get_keys) )
                    # It can be used to parse a valid JSON string and convert it into a Python Dictionary. 
                    self.logger.warning("{}".format(json.load(l_get_dict)))
                else:
                    pass
            else:
                pass

        if len(l_get_keys) > 0:
            l_index = int(l_get_keys[0])
            if self.__high_permission_max > 0 and l_index <= self.__high_permission_max:
                # high permission item
                self.__high_pop_count += 1
            else:
                self.__normal_pop_count += 1

            return l_get_dict.get(l_get_keys[0])
        else:
            return None

