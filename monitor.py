#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
# author: mark.hsieh
# import os
# import logging
# import asyncio
# import random
# import re
from datetime import datetime
import pytz
# import yaml
import json
import subprocess
import re
import time
    
# for conversation handler, linking number
FATAL, ERROR, WARN, INFO, DEBUG = range(5)

# TIMEZONE = "Asia/Taipei"

class MonitorSrv(object):
    def __init__(self, logger=None, timezone="Asia/Taipei", stop_system=None, target_name=None, queue_req=None, queue_res=None) -> None:
        super().__init__()
        
        self.__queue_request = None 
        self.__queue_result = None 
        self.__target_name = None
        self.__run = False
        self.__pause = False
        self.__event_stop = None
        self.__logger = None
        
        self.__manualTimezone = pytz.timezone(timezone)
        
        if (queue_req != None):
            self.__queue_request = queue_req
        if (queue_res != None):
            self.__queue_result = queue_res
        if (stop_system != None):
            self.__event_stop = stop_system
        if (target_name != None):
            self.__target_name = target_name
        if (logger != None):
            self.__logger = logger
            
        self.__printf("already loaded finish.", WARN)
        
    # def FATAL(self):
    #         return 'FATAL'
    # def ERROR(self):
    #         return 'ERROR'
    # def WARN(self):
    #         return 'WARN'
    # def INFO(self):
    #         return 'INFO'
    # def DEBUG(self):
    #         return 'DEBUG'
    def indirect(self, num):
        switcher={
                0:'FATAL',
                1:'ERROR',
                2:'WARN',
                3:'INFO',
                4:'DEBUG'
                }
        
        return switcher.get(num,lambda :'Invalid')
        
    def __printf(self, STR:str, TYPE:int):
        l_date = datetime.now(self.__manualTimezone) 
        if (self.__logger == None):
            l_level = self.indirect(TYPE)
            print("{}]] {} - {} - {}".format(l_date, __name__, l_level, STR), end="\n")
        elif (TYPE == FATAL):
            self.__logger.critical("{}]] {}".format(l_date, STR))
        elif (TYPE == ERROR):
            self.__logger.error("{}]] {}".format(l_date, STR))
        elif (TYPE == WARN):
            self.__logger.warning("{}]] {}".format(l_date, STR))
        elif (TYPE == DEBUG):
            self.__logger.debug("{}]] {}".format(l_date, STR))
        elif (TYPE == INFO):
            self.__logger.info("{}]] {}".format(l_date, STR))
        else:
            # ALL = INFO
            self.__logger.info("{}]] {}".format(l_date, STR))
            
    def __scan_logs_from_docker_container(self, target_name):
        # command
        command = "sudo docker logs --tail 10 " + target_name
        errors = []
        result = "Success"
        try:
            returned_value = subprocess.run( 
                command, shell=True, check=True, 
                capture_output=True, text=True,
                ) #stdout=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            errors.append(str(e))
            result = "CalledProcessError"
        except subprocess.TimeoutExpired as e:
            errors.append(str(e))
            result = "TimeoutExpired"
        except subprocess.SubprocessError as e:
            errors.append(str(e))
            result = "SubprocessError"
            
        # return_msg = returned_value.stdout
        # message.append("{}:".format(returned_value.returncode))
        # message.append("{}".format(returned_value.stderr))
        errors.append(returned_value.stderr)
        output_msg = "{}: {}".format(returned_value.returncode, returned_value.stdout)
        
        return output_msg, result, errors
            
    def __start(self):
        # stop_signals=[SIGINT, SIGTERM, SIGABRT]
        
        # self.__queue_request = queue_req
        # self.__queue_result = queue_res
        
        l_dict = {}
        l_res = {}
        
        if self.__queue_request is None or self.__queue_result is None:
            # l_date = datetime.now(self.__manualTimezone)
            self.__printf("request and result queue not allow to set None as default.", ERROR)
            self.__run = False
        else:
            self.__run = True
        
        while self.__run is True:
            # l_date = datetime.now(self.__manualTimezone)
            
            ## print the action server return message
            l_res = self.__popFromQueueRes()
            if l_res and l_res is not None:
                self.__printf("{}.".format(json.dumps(l_res)), INFO)
                
            ## make sure monitor server is accept running? what message shell notice?
            if self.__event_stop.is_set():
                self.__run = False
                self.__event_stop.clear()
                self.__printf("stoping...", WARN)
            else:
                ## deliver 
                res_msg, res_state, res_errs = self.__scan_logs_from_docker_container(self.__target_name)
                if (res_state != "Success"):
                    l_errors = ', '.join(res_errs)
                    self.__printf("{}: {}.".format(res_state, l_errors), ERROR)
                else:
                    ## convert to queue for actions
                    l_errors_count = 0
                    for line in res_msg:
                        l_search = re.search('connection reset by peer', line)
                        if l_search != None:
                            self.__printf("{}.".format(line), FATAL)
                            l_errors_count = l_errors_count + 1
                            if l_dict is False or l_dict is None:
                                l_dict = {
                                    "state": "critical",
                                    "action": "restart"
                                }
                                continue
                            
                        l_search = re.search('KLine取得發生錯誤', line)
                        if l_search != None:
                            self.__printf("{}.".format(line), FATAL)
                            l_errors_count = l_errors_count + 1
                            if l_dict is False or l_dict is None:
                                l_dict = {
                                    "state": "critical",
                                    "action": "restart"
                                }
                                continue
                            
                    if l_errors_count >= 1:    
                        self.__pause = True
                        if l_dict["state"] == "critical":
                            self.__pushToQueueReq(l_dict, True)
                        # else:
                        #     self.__pushToQueueReq(l_dict, False)
                    else:
                        self.__pause = False
                        l_dict = {}
                    
            if self.__pause is True:
                time.sleep(5) # ... just 
            else:        
                time.sleep(2)         
                
    def __pushToQueueReq(self, item: dict, important=False):
        '''
        __pushToQueueReq (item: dict, important: boolean)
        PARAMETER: 
            'item' is dict data
            'important' mean task permission
        OUTPUT:
            NONE
        '''
        # TODO self.__queue_request
        l_res = False
        l_msg = "None"
        # It can be used to parse a Python Dictionary string and convert it into a valid JSON.
        l_dict_2_json = json.dumps(item)
        l_res, l_msg = self.__queue_request.push(l_dict_2_json, important)
        if l_res:
            pass
        else:
            # l_date = datetime.now(self.__manualTimezone)
            self.__printf("add result into queue fail. {}".format(l_msg), WARN)

    def __popFromQueueRes(self):
        '''
        __popFromQueueRes ()
        PARAMETER:
            NONE
        OUTPUT:
            dict data
        '''
        # TODO self.__queue_result
        l_msg = None
        l_msg = self.__queue_result.pop()
        if l_msg is None:
            return {}
        else:
            # It can be used to parse a valid JSON string and convert it into a Python Dictionary. 
            return json.loads(l_msg)
        
    def run(self):
        # l_date = datetime.now(self.__manualTimezone)
        self.__printf("start running.", WARN)
        self.__start()
