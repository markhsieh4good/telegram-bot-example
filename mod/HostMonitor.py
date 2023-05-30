#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
# author: mark.hsieh
import random, os
import logging
import psutil
import time
import math
import json
import subprocess

from datetime import datetime
import pytz
 
from common import myqueue

class MyHostSrv(object):
    def __init__(self, logger) -> None:
        super().__init__()
        self.logger = logger
        self.__run = False
        self.__event_stop = None
        self.__queue_request = None
        self.__queue_result = None
        self.__system_info = { 
            "cpu": "0%",
            "memory": "0 MB free / 0 MB total ( 100% )",
            "disk": "0 GB free / 0 GB total ( 100% )",
            "ip": "168.95.0.1, 192.168.0.1"
            }

        self.logger.info("{} already loaded finish.".format(__name__))

    def run(self, event, queue_req, queue_res):
        self.__run = True
        self.__event_stop = event
        self.__queue_request = queue_req
        self.__queue_result = queue_res

        while self.__run is True:
            if self.__event_stop.is_set():
                self.__run = False
                self.__event_stop.clear()
                self.logger.info("{} stoping...".format(__name__))
            else:
                ## action 
                # 1. check queue req.: empty? pass, have job? pop and disp. to method.
                # 2. get the result or error
                # 3. check queue res.: full? pass and send errors. or just push 
                #    answer into queue result.
                l_dict = self.__popFromQueueReq()
                l_result = None
                if l_dict is not None:
                    l_result = self.__whichTask(l_dict)
                    self.__pushToQueueRes(l_result)
                else:
                    time.sleep(0.1)
                    
    def __pushToQueueRes(self, item: dict, important=False):
        '''
        __pushToQueueRes (item: dict, important: boolean)
        PARAMETER: 
            'item' is dict data
            'important' mean task permission
        OUTPUT:
            NONE
        '''
        # TODO self.__queue_result
        l_res = False
        l_msg = "None"
        # It can be used to parse a Python Dictionary string and convert it into a valid JSON.
        l_dict_2_json = json.dumps(item)
        l_res, l_msg = self.__queue_result.push(l_dict_2_json, important)
        if l_res is False:
            self.logger.warning("add result into queue fail. {}".format(l_msg))

    def __popFromQueueReq(self):
        '''
        __popFromQueueReq ()
        PARAMETER:
            NONE
        OUTPUT:
            dict data
        '''
        # TODO self.__queue_request
        l_msg = None
        l_msg = self.__queue_request.pop()
        if l_msg is None:
            return None
        else:
            # It can be used to parse a valid JSON string and convert it into a Python Dictionary. 
            return json.loads(l_msg)

    def __whichTask(self, task: dict):
        '''
        example:
            l_dict = {
                "command": "status",
                "data": None,
                "timestamp": l_currntT
            }
        '''
        l_command = task["command"]
        l_chat_id = task["chat_id"]
        l_data = task["data"]
        l_timestamp = int(task["timestamp"])
        l_timezone = task["timezone"]
        l_result = ""
        l_feedback = None
        l_dict = None

        if l_command == "host_status":
            l_result, l_feedback = self.__system()
        elif l_command == "k8s_monitor":
            l_result, l_feedback = self.__monitorK8s()
        elif l_command == "host_restart":
            l_result, l_feedback = self.__restart()
        elif l_command == "update_telegram_robot":
            # this is one way trip ...
            l_result, l_feedback = self.__update_telegram()
        else:
            l_result = "There are plans, but not yet supported."
            l_feedback = {
                "message": "not support",
                "command": "{}".format(l_command)
            }

        l_finishT = round(time.time()*100)*0.01
        l_diffT = round((l_finishT - l_timestamp)*100)*0.01

        manualTimezone = pytz.timezone(l_timezone)
        l_now = datetime.now(manualTimezone)

        l_dict = {
            "result": l_result,
            "clock": "{}".format(l_now),
            "feedback": l_feedback,
            "timecost": "{:.2f} seconds".format(l_diffT),
            "chat_id": l_chat_id
        }
        return l_dict

    def __system(self):
        # Get cpu statistics
        l_current_cpu = str(psutil.cpu_percent()) + '%'
        self.__system_info.update({"cpu": l_current_cpu})

        # Calculate memory information
        memory = psutil.virtual_memory()
        # Convert Bytes to MB (Bytes -> KB -> MB)
        mem_available = round(memory.available/1024.0/1024.0,1)
        mem_total = round(memory.total/1024.0/1024.0,1)
        mem_info = str(mem_available) + 'MB free / ' + str(mem_total) + 'MB total ( ' + str(memory.percent) + '% )'
        self.__system_info.update({"memory": mem_info})

        # Calculate disk information
        disk = psutil.disk_usage('/')
        # Convert Bytes to GB (Bytes -> KB -> MB -> GB)
        disk_free = round(disk.free/1024.0/1024.0/1024.0,1)
        disk_total = round(disk.total/1024.0/1024.0/1024.0,1)
        disk_info = str(disk_free) + 'GB free / ' + str(disk_total) + 'GB total ( ' + str(disk.percent) + '% )'
        self.__system_info.update({"disk": disk_info})

        # command
        command = "bash ./get_ip.sh "
        message = []
        result = "success"
        try:
            returned_value = subprocess.run( 
                command, shell=True, check=True, 
                capture_output=True, text=True,
                ) #stdout=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            message.append(str(e))
            result = "CalledProcessError"
        except subprocess.TimeoutExpired as e:
            message.append(str(e))
            result = "TimeoutExpired"
        except subprocess.SubprocessError as e:
            message.append(str(e))
            result = "SubprocessError"

        message.append("{}:".format(returned_value.returncode))
        message.append("{}".format(returned_value.stderr))

        l_internal_ip = [ False, "None" ]
        l_external_ip = [ False, "None" ]
        l_Lines = return_msg.splitlines()
        for line in l_Lines:
            if l_internal_ip[0] is True and \
                l_external_ip[0] is True:
                continue

            n_internal_ip = line.find('internal_ip=')
            if n_internal_ip > 0 and l_internal_ip[0] is False:
                l_internal_ip[0] = True
                l_internal_ip[1] = "{}".format(line[n_internal_ip:])
                continue

            n_external_ip = line.find('external_ip=')
            if n_external_ip > 0 and l_external_ip[0] is False:
                l_external_ip[0] = True
                l_external_ip[1] = "{}".format(line[n_external_ip:])
                continue

        l_feedback = {
            "system_feedback": message,
            "system_information": self.__system_info,
            "response": {
                "internal_ip": l_internal_ip[1],
                "external_ip": l_external_ip[1]
            }
        }

        return result, l_feedback

    def __restart(self):
        # command
        command = "sudo reboot "
        message = []
        result = "success"
        try:
            returned_value = subprocess.run( 
                command, shell=True, check=True, 
                capture_output=True, text=True,
                ) #stdout=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            message.append(str(e))
            result = "CalledProcessError"
        except subprocess.TimeoutExpired as e:
            message.append(str(e))
            result = "TimeoutExpired"
        except subprocess.SubprocessError as e:
            message.append(str(e))
            result = "SubprocessError"

        message.append("{}:".format(returned_value.returncode))
        message.append("{}".format(returned_value.stderr))

        l_feedback = {
            "system_feedback": message,
            "response": {
                "text": "restart docker container"
            }
        }

        return result, l_feedback

    def __monitorK8s(self):
        # command
        command = "sudo kubectl get pod -A"
        message = []
        result = "success"
        try:
            returned_value = subprocess.run( 
                command, shell=True, check=True, 
                capture_output=True, text=True,
                ) #stdout=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            message.append(str(e))
            result = "CalledProcessError"
        except subprocess.TimeoutExpired as e:
            message.append(str(e))
            result = "TimeoutExpired"
        except subprocess.SubprocessError as e:
            message.append(str(e))
            result = "SubprocessError"

        # print("os return: {}".format(returned_value))
        return_msg = returned_value.stdout
        # print("system call return: {}".format(return_msg))
        message.append("{}:".format(returned_value.returncode))
        message.append("{}".format(returned_value.stderr))

        # last order
        # FIXME

        # print("extend message: {}".format(message))
        l_feedback = {
            "system_feedback": message,
            "response": {
                "response": return_msg
            }
        }

        return result, l_feedback

    def __update_telegram(self, data="newest"):
        self.logger.info("will update telegram robot")
        command = ""
        message = []
        return_msg = []
        result = "success"

        '''
        TODO:
            use supervisor to update and restart system
        '''

        command = "sudo supervisorctl restart backend_robot:backend_robot_00"
        try:
            returned_value = subprocess.run( 
                command, shell=True, check=True, 
                capture_output=True, text=True,
                ) #stdout=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            message.append(str(e))
            result = "CalledProcessError"
        except subprocess.TimeoutExpired as e:
            message.append(str(e))
            result = "TimeoutExpired"
        except subprocess.SubprocessError as e:
            message.append(str(e))
            result = "SubprocessError"

        return_msg.append(returned_value.stdout)

        l_feedback = {
            "system_feedback": message,
            "response": {
                "response": return_msg,
                "version": "{}".format(data)
            }
        }
        return result, l_feedback

