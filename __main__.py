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
    global TelegramRobot
    
    # Telegram Robot setting
    TelegramRobot = MyTelegramSrv(logger, stop_self)
    BtcRobot = MyBtcSrv(logger)
    SendMessager = MySendTools(logger)

    # Running server
    # app.run(debug=True)
    req_q = MyQueue(logger, size=30, high_permission_has=0.25)
    res_q = MyQueue(logger, size=30, high_permission_has=0) # result order is base on request.

    # queue link with ...
    # telegram bot [push]--(request queue)-->[pop] btc robot
    # btc robot [push]--(result queue)-->[pop] telegram bot

    # Btc-Robot listener
    BtcRobotStopEvent = Event()
    BtcRobotThread = Thread(
        target=BtcRobot.run, 
        args=(BtcRobotStopEvent, req_q, res_q), 
        name="BtcRobotCommunicateThread")
    BtcRobotThread.start()

    # Send Message listener
    SendMessageStopEvent = Event()
    SendMessageThread = Thread(
        target=SendMessager.run, 
        args=(SendMessageStopEvent, req_q, res_q, cb), 
        name="BtcRobotCommunicateThread")
    SendMessageThread.start()

    TelegramRobot.freeAllUpdates()
    TelegramRobot.start(req_q, res_q) # until receive system signal.
    TelegramRobot.release()

    SendMessageStopEvent.set()
    SendMessageThread.join()

    BtcRobotStopEvent.set()
    BtcRobotThread.join()

    req_q.clean()
    res_q.clean()
    logger.info('Thanks for using, bye.')
