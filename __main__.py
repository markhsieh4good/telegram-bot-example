#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
# author: mark.hsieh
import sys
import logging
import os, signal

from threading import Thread
from threading import Event

from common.myqueue import *
from common.sendmessage import *
from TelegramRobot import *

logging.basicConfig(
                    level=logging.INFO,
                    format='%(name)s - %(levelname)s - %(message)s',
                            # datefmt="%m/%d/%Y %I:%M:%S %p %Z",
                    # Send to file and ttyS0...
                    handlers=[
                        # logging.FileHandler("{0}/{1}.log".format(logPath, fileName)),
                        logging.StreamHandler(sys.stdout)
                    ]
        )
logger = logging.getLogger(__name__)

# def stop_self():
#     os.kill(os.getpid(), signal.SIGINT)

def signal_handler(signum, frame):
    logger.warning('signal_handler: caught signal ' + str(signum))
    global StopSys
    if signum == signal.SIGINT.value:
        print('... SIGINT')
        StopSys = True
    elif signum == signal.SIGTERM.value:
        print('... SIGTERM')
        StopSys = True
    elif signum == signal.SIGABRT.value:
        print('... SIGABRT')
        StopSys = True
    else:
        print('???')
    
if __name__ == "__main__":
    logger.info('Wellcome into the remote control service.')
    # global var.
    global MonitorRobot
    global WorkerRobot
    global StopSys

    # Running server
    # app.run(debug=True)
    req_q = MyQueue(logger, size=30, high_permission_has=0.25)
    res_q = MyQueue(logger, size=30, high_permission_has=0) # result order is base on request.
    
    # Monitor and create event
    
    # Listen and act

    # queue link with ...
    # monitor bot [push]--(request queue)-->[pop] action robot
    # action bot [push]--(result queue)-->[pop] monitor bot
    MonitorRobotStopEvent = Event()
    MonitorRobot = MonitorSrv(stop_system=MonitorRobotStopEvent, target_name="binance-bot", queue_req=req_q, queue_res=res_q)
    
    WorkerRobotStopEvent = Event()
    WorkerRobot = WorkerSrv(stop_system=MonitorRobotStopEvent, target_name="binance-bot", queue_req=req_q, queue_res=res_q)

    # MonitorRobot listeners
    MonitorRobotThread = Thread(
        target=MonitorRobot.run, 
        args=(), 
        name="MonitorRobotCommunicateThread")
    MonitorRobotThread.start()
    
    WorkerRobotThread = Thread(
        target=WorkerRobot.run, 
        args=(), 
        name="WorkerRobotCommunicateThread")
    WorkerRobotThread.start()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGABRT, signal_handler)
    # signal.signal(signal.SIGSTOP, signal_handler)
    b_run = True
    StopSys = False
    while b_run is True:
        if StopSys is True:
            b_run = False
        else:
            time.sleep(1)
    
    MonitorRobotStopEvent.set()
    MonitorRobotThread.join()

    WorkerRobotStopEvent.set()
    WorkerRobotThread.join()
    
    req_q.clean()
    res_q.clean()
    logger.info('Thanks for using, bye.')
