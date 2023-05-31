#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
# author: mark.hsieh
import sys
import logging
import os, signal
import datetime
import yaml

from threading import Thread
from threading import Event

from common.myqueue import *

from mod.SendMessage import *
from mod.TelegramRobot import *
from mod.HostMonitor import *

logging.basicConfig(
                    level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    # Send to file and ttyS0...
                    handlers=[
                        # logging.FileHandler("{0}/{1}.log".format(logPath, fileName)),
                        logging.StreamHandler(sys.stdout)
                    ]
        )
logger = logging.getLogger(__name__)

def cb(msg:dict):
    chat_id = msg["chat_id"]
    del msg["chat_id"]
    TelegramRobot.sendMessageByURL(chat_id, msg)

def stop_self():
    os.kill(os.getpid(), signal.SIGINT)

def isStopSys():
    return StopSys

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
    elif signum == signal.SIGALRM.value:
        print('... SIGALRM')
        StopSys = False
    else:
        print('???')

    if StopSys:
        logging.info("Signal : '{}' Received. Handler Executed @ {}".format(signal.strsignal(signum), datetime.now()))
        TelegramRobot.stop_listen_telegram()
    else:
        print('just alarm for test')
    
if __name__ == "__main__":
    logger.info('Wellcome into the remote control service.')

    current_working_directory = os.getcwd()
    print('working folder is:' + current_working_directory)

    # Initial all option from configuration file (*.yaml)
    with open("config.yaml", "r", encoding="utf-8") as f:
        yaml_data = yaml.safe_load(f)

    # global var.
    global TelegramRobot
    
    # Telegram Robot setting
    TelegramRobot = MyTelegramSrv(logger, isStopSys, yaml_data)
    K8sHost = MyBtcSrv(logger)
    SendMessager = MySendTools(logger)

    # Running server
    # app.run(debug=True)
    req_q = MyQueue(logger, size=30, high_permission_has=0.25)
    res_q = MyQueue(logger, size=30, high_permission_has=0) # result order is base on request.

    # system signal reader
    signal.signal(signal.SIGALRM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGABRT, signal_handler)
    signal.alarm(signal.SIGALRM)
    time.sleep(2)

    # queue link with ...
    # telegram bot [push]--(request queue)-->[pop] btc robot
    # btc robot [push]--(result queue)-->[pop] telegram bot

    # K8s Host listener
    K8sHostStopEvent = Event()
    K8sHostThread = Thread(
        target=K8sHost.run, 
        args=(K8sHostStopEvent, req_q, res_q), 
        name="K8sHostCommunicateThread")
    K8sHostThread.start()

    # Send Message listener
    SendMessageStopEvent = Event()
    SendMessageThread = Thread(
        target=SendMessager.run, 
        args=(SendMessageStopEvent, req_q, res_q, cb), 
        name="SendMessageCommunicateThread")
    SendMessageThread.start()

    # TelegramRobot.freeAllUpdates()
    TelegramRobot.start(req_q, res_q) # until receive system signal.
    TelegramRobot.stop_listen_telegram() # 再次檢查

    SendMessageStopEvent.set()
    SendMessageThread.join()

    K8sHostStopEvent.set()
    K8sHostThread.join()

    req_q.clean()
    res_q.clean()
    logger.info('Thanks for using, bye.')
