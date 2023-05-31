
#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-
# author: mark.hsieh
import os
import logging
import asyncio
import random
import re
from datetime import datetime
import pytz
import signal

# import telegram
## api
from telegram import Update, Bot
from telegram.ext import Updater, MessageHandler
from telegram.ext import CallbackContext, CommandHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext import ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Load data from config.ini file
# import configparser
# config = configparser.ConfigParser()
# config.read('config.ini')

import json

import requests
import time

# for conversation handler, linking number
BINANCE, TELEGRAM, AREA, MARKET = range(4)

class MyTelegramSrv(object):
    def __init__(self, logger, is_stop_system, working_folder, configuration) -> None:
        super().__init__()

        # parse to local value
        self.__bot_token = configuration['bot_token']
        self.__refresh_seconds = configuration['refresh_seconds']
        self.__char_id = configuration['group_chat_id']
        self.__whisp_id = configuration['whisp_chat_id']
        self.__version = configuration['version']
        self.__timezone = configuration['timezone']

        header = {"Authorization": "Telegram Bot Hock: {}".format(self.__bot_token)}
        self.__queue_request = None
        self.__queue_result = None
        self.__chatpool = []

        if self.__char_id == "" or self.__char_id is None:
            pass
        else:
            self.__chatpool.append(self.__char_id)
        if self.__whisp_id == "" or self.__whisp_id is None:
            pass
        else:
            self.__chatpool.append(self.__whisp_id)

        self.__updater = Updater(self.__bot_token, use_context=True)
        self.__bot = self.__updater.bot
        self.__updater.dispatcher.add_handler(handler=CommandHandler('hello', self.__hello, pass_update_queue=True, pass_job_queue=True, pass_user_data=True), group=0)
        self.__updater.dispatcher.add_handler(handler=CommandHandler('help', self.__help, pass_update_queue=True, pass_job_queue=True, pass_user_data=True), group=0)

        self.__updater.dispatcher.add_handler(handler=CommandHandler('status', self.__status), group=0)
        self.__updater.dispatcher.add_handler(handler=CommandHandler('k8s', self.__k8s), group=0)

        self.__updater.dispatcher.add_handler(handler=CommandHandler('restart', self.__restart), group=0)

        # self.__updater.dispatcher.add_handler(handler=CommandHandler('update', self.__upgrade), group=0)
        self.__updater.dispatcher.add_handler(handler=CommandHandler('offecho', self.__offecho), group=0)
        self.__updater.dispatcher.add_handler(handler=CommandHandler('broadcast', self.__echo), group=0)

        self.__updater.dispatcher.add_handler(handler=CallbackQueryHandler(self.__press_button_callback))

        # self.__updater.dispatcher.add_handler(handler=CommandHandler('more', self.__more), group=0)

        self.logger = logger
        self.is_stop_system = is_stop_system

        # 把Hello語錄檔案載入
        self.__sentences = []
        # l_directory = os.getcwd().replace('\\', '/')
        l_directory = working_folder
        self.logger.info("loaded sentences from: {} to {}".format(l_directory, '/resrc/sentence/hello.txt'))
        if os.path.exists(l_directory + '/resrc/sentence/hello.txt'):
            _FILE = open(l_directory + '/resrc/sentence/hello.txt')
            _LINE = _FILE.readlines()
            for line in _LINE:
                self.__sentences.append(line)
        else:
            self.__sentences.extend(
                ["I don't have time to play games, but I keep showing up in games!",
                "If you say hello again, I will chop off your palm! But I can't, TAT",
                "You don't know how hard it is to keep an eye on the market, but fortunately my mood mod has never been made.",
                "Get off! I don't want to sing to you! I'm a heartless investment robot, not a music box.",
                "Has anyone heard the buzzing of the flies? Kind reminder, can you look in the mirror?"])
        self.logger.info("{} already loaded finish.".format(__name__))

    def __information(self):
        manualTimezone = pytz.timezone(self.__timezone)
        l_date = datetime.now(manualTimezone) 

        self.__sendMessageToAllChat("Hello, this is telegram bot. \n"
            + "\t version: {}\n ".format(self.__version)
            + "\t clock: {}".format(l_date))

    def start(self, queue_req, queue_res):
        # stop_signals=[SIGINT, SIGTERM, SIGABRT]

        self.__queue_request = queue_req
        self.__queue_result = queue_res

        self.__information()
        self.__freeAllUpdates() # clean all message from telegram cloud queue

        self.__updater.start_polling(
            poll_interval=float(self.__refresh_seconds), 
            timeout=10)
        self.__updater.idle()

    def __stop(self, delay=0):
        l_start = int(round(time.time()))
        l_end = round(l_start + delay)
        l_run = True
        while l_run is True:
            l_current = int(round(time.time()))
            if l_current > l_end:
                l_run = False
            else:
                time.sleep(0.5)
        if self.is_stop_system is False:
            signal.alarm(signal.SIGINT)

    def stop_listen_telegram(self):
        self.__release()

    def __release(self):
        self.logger.info("{} stoping...".format(__name__))
        try:
            self.__updater.stop()
        except RuntimeError:
            self.logger.warning("already close object from {}".format(__name__))
        except Exception as msg:
            self.logger.warning("some thing wrong when stop close object from {}. \n".format(__name__)
                               + "\t\t {}".format(msg))

    # async def cencel(self, update: Update, context: CallbackContext):
    #     user = update.message.from_user
    #     logger.info("User %s canceled the conversation.", user.first_name)
    #     await update.message.reply_text(
    #         "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    #     )
    #     return ConversationHandler.END

    def __freeAllUpdates(self):
        self.__getAllUpdates2Release()

    def __isRunning(self):
        return self.__updater.running

    def sendMessageByURL(self, chat_id, message):
        self.__sendMessageToTypicalChat(chat_id, message)

    def __sendMessageToTypicalChat(self, chat_id, message):
        # TODO: add a function to set Typical Chat ID
        # use group char id
        if self.__isRunning is False:
            pass
        else:
            headers = {
                'Content-Type': 'application/json',

            }
            # url = f"https://api.telegram.org/bot{self.__bot_token}/sendMessage?chat_id={chat_id}&text={message}"
            # lres = requests.get(url).json()
            url = f"https://api.telegram.org/bot{self.__bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message
            }
            data = json.dumps(payload, ensure_ascii=False).encode('utf8')
            lres = requests.post(url, data=data, headers=headers)

            # if lres["ok"] is True or lres["ok"] == 'True' or lres["ok"] == 'true':
            #     pass
            if lres.status_code == 200 or lres.ok is True:
                pass
            else:
                self.logger.error("sendMessage fail. {}:{} {}".format(lres.status_code, lres.reason, lres.text))

    def __sendPictureToTypicalChat(self, chat_id, path, message):
        if self.__isRunning is False:
            pass
        else:
            headers = {
                'Content-Type': 'application/json',
            }
            url = f'https://api.telegram.org/bot{self.__bot_token}/sendPhoto'
            payload = {
                'chat_id': chat_id,
                'photo': path,
                'caption': message
            }
        
            data = json.dumps(payload, ensure_ascii=False).encode('utf8')
            lres = requests.post(url, data=data, headers=headers)
            if lres.status_code == 200 or lres.ok is True:
                pass
            else:
                self.logger.error("sendMessage fail. {}:{} {}".format(lres.status_code, lres.reason, lres.text))

    def __sendAudioToTypicalChat(self, chat_id, path):
        if self.__isRunning is False:
            pass
        else:
            headers = {
                'Content-Type': 'application/json',
            }
            url = f'https://api.telegram.org/bot{self.__bot_token}/sendAudio'
            payload = {
                'chat_id': chat_id,
                'audio': path
            }

            data = json.dumps(payload, ensure_ascii=False).encode('utf8')
            lres = requests.post(url, data=data, headers=headers)
            if lres.status_code == 200 or lres.ok is True:
                pass
            else:
                self.logger.error("sendMessage fail. {}:{} {}".format(lres.status_code, lres.reason, lres.text))

    def __sendVideoToTypicalChat(self, chat_id, path):
        if self.__isRunning is False:
            pass
        else:
            headers = {
                'Content-Type': 'application/json',
            }
            url = f'https://api.telegram.org/bot{self.__bot_token}/sendVideo'
            payload = {
                'chat_id': chat_id,
                'video': path
            }
        
            data = json.dumps(payload, ensure_ascii=False).encode('utf8')
            lres = requests.post(url, data=data, headers=headers)
            if lres.status_code == 200 or lres.ok is True:
                pass
            else:
                self.logger.error("sendMessage fail. {}:{} {}".format(lres.status_code, lres.reason, lres.text))

    def __getAllUpdates2Release(self):
        # TODO: add a function to set Typical Chat ID
        # use group char id
        if self.__isRunning is False:
            pass
        else:
            headers = {
                'Content-Type': 'application/json',

            }
            url = f"https://api.telegram.org/bot{self.__bot_token}/getUpdates"
            lres = requests.get(url).json()
            # url = f"https://api.telegram.org/bot{self.__bot_token}/sendMessage"
            # payload = {
            #     "chat_id": chat_id,
            #     "text": message
            # }
            # data = json.dumps(payload, ensure_ascii=False).encode('utf8')
            # lres = requests.post(url, data=data, headers=headers)

            if lres["ok"] is True or lres["ok"] == 'True' or lres["ok"] == 'true':
                # just use this function to clean old requestion.
                pass
            elif lres.status_code == 200 or lres.ok is True:
                pass
            else:
                self.logger.error("sendMessage fail. {}:{} {}".format(lres.status_code, lres.reason, lres.text))

    # async def __sendMsgByApplicationBuilder(self, chat_id, message):
    #     # ref.: https://stackoverflow.com/a/74195448
    #     application = ApplicationBuilder().token(self.__bot_token).build()
    #     await application.bot.sendMessage(chat_id=chat_id, text=message)

    # def __sendMessageByAppBuilder(self, chat_id, message):
    #     asyncio.run(self.__sendMsgByApplicationBuilder(chat_id, message))

    def __sendMessageToAllChat(self, message):
        for chat_id in self.__chatpool:
            # self.__sendMessageByAppBuilder(chat_id, message)
            self.__sendMessageToTypicalChat(chat_id, message)

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
        if l_res is False:
            self.logger.warning("add request into queue fail. {}".format(l_msg))

    # def __popFromQueueRes(self):
    #     '''
    #     __popFromQueueRes ()
    #     PARAMETER:
    #         NONE
    #     OUTPUT:
    #         dict data
    #     '''
    #     # 這個功能需要一個thread達到非同步處理
    #     # 放在外部比較好操作
    #     l_msg = None
    #     l_msg = self.__queue_result.pop()
    #     return json.load(l_msg)

    def __hello(self, update: Update, context: CallbackContext):
        # l_vistor = context.user_data context.update_queue
        # print("{}".format(l_vistor))
        chat_id = str(update.message.chat_id)
        count = self.__chatpool.count(chat_id)
        if count <= 0:
            update.message.reply_text("hello new friend ... {}".format(chat_id))
            self.__chatpool.append(chat_id)

        # random.seed(1)
        l_sentence = "{} \n[ /help ] how to use this bot".format((random.choice(self.__sentences)))
        update.message.reply_text(l_sentence)

    def __help(self, update: Update, context: CallbackContext):
        chat_id = str(update.message.chat_id)
        count = self.__chatpool.count(chat_id)
        if count <= 0:
            update.message.reply_text("I don't known you, please say hello at first. (/hello)")
        else:
            # TODO: virtual button select INF.
            message_reply_text = 'I can help you as below, choice one.'
            buttons = [
                [InlineKeyboardButton("platform Status", callback_data='callback_status')],
                [InlineKeyboardButton("k8s pods infomation", callback_data='callback_k8s_monitor')],
                [InlineKeyboardButton("Restart host", callback_data='callback_restart')],
                # [InlineKeyboardButton("Update Btc Robot", callback_data='callback_update_btc_robot')],
                # [InlineKeyboardButton("Update Telegram Robot", callback_data='callback_update_telegram_robot')],
                # [InlineKeyboardButton("Set Area", callback_data='callback_set_area')],
                # [InlineKeyboardButton("Set Market", callback_data='callback_set_market')],
                [InlineKeyboardButton("Show More", callback_data='callback_more')]
            ]
            keyboard = InlineKeyboardMarkup(buttons)
            update.message.reply_text(message_reply_text, reply_markup=keyboard)

    def __offecho(self, update: Update, context: CallbackContext):
        chat_id = str(update.message.chat_id)
        # txt = update.message.text

        count = self.__chatpool.count(chat_id)
        if count > 0:
            self.__chatpool.remove(chat_id)
            update.message.reply_text("I already close your Broadcast Receive flag. You can revert this function, just say hello again. (/hello)")
        else:
            update.message.reply_text("Who are you? I don't service unknown.")

    def __echo(self, update: Update, context: CallbackContext):
        chat_id = str(update.message.chat_id)
        txt = update.message.text

        count = self.__chatpool.count(chat_id)
        if count > 0:
            self.__sendMessageToAllChat(txt)
        else:
            update.message.reply_text("Who are you? I don't service unknown.")

    def __status(self, update: Update, context: CallbackContext):
        l_currntT = round(time.time()*100)*0.01

        chat_id = str(update.message.chat_id)
        count = self.__chatpool.count(chat_id)
        if count > 0:
            l_dict = {
                "command": "host_status",
                "chat_id": chat_id,
                "data": None,
                "timestamp": l_currntT,
                "timezone": self.__timezone
            }
            # response message after we figure out the requestion
            self.__pushToQueueReq(l_dict, important=False)
        else:
            update.message.reply_text("Who are you? I don't service unknown.")

    def __k8s(self, update: Update, context: CallbackContext):
        l_currntT = round(time.time()*100)*0.01

        chat_id = str(update.message.chat_id)
        count = self.__chatpool.count(chat_id)
        if count > 0:
            l_dict = {
                "command": "k8s_monitor",
                "chat_id": chat_id,
                "data": None,
                "timestamp": l_currntT,
                "timezone": self.__timezone
            }
            # response message after we figure out the requestion
            self.__pushToQueueReq(l_dict, important=True)
        else:
            update.message.reply_text("Who are you? I don't service unknown.")

    def __restart(self, update: Update, context: CallbackContext):
        l_currntT = round(time.time()*100)*0.01

        chat_id = str(update.message.chat_id)
        count = self.__chatpool.count(chat_id)
        if count > 0:
            l_dict = {
                "command": "host_restart",
                "chat_id": chat_id,
                "data": None,
                "timestamp": l_currntT,
                "timezone": self.__timezone
            }
            # response message after we figure out the requestion
            self.__pushToQueueReq(l_dict, important=True)
        else:
            update.message.reply_text("Who are you? I don't service unknown.")

    # def __upgrade(self, update: Update, context: CallbackContext):
    #     l_currntT = round(time.time()*100)*0.01

    #     chat_id = str(update.message.chat_id)
    #     count = self.__chatpool.count(chat_id)
    #     if count > 0:
    #         message_reply_text = 'I can help you as below, choice one.'
    #         buttons = [
    #             [InlineKeyboardButton("update BTC Robot", callback_data='update_btc_robot')],
    #             [InlineKeyboardButton("update Telegram Robot", callback_data='update_telegram_robot')]
    #         ]
    #         keyboard = InlineKeyboardMarkup(buttons)
    #         update.message.reply_text(message_reply_text, reply_markup=keyboard)
    #     else:
    #         update.message.reply_text("Who are you? I don't service unknown.")

    # def __more(self, update: Update, context: CallbackContext):
    #     update.message.reply_text("[ /new_binance VERSION ] update the binance rebot to VERSION \n"
    #                             + "[ /new_this] update the telegram rebot to the newest \n"
    #                             + "[ /set_nodes VALUE ] re-define area range \n"
    #                             + "[ /set_contract_limit VALUE ] re-define market per contract"
    #                             + "[ /set_trade_u2b_onoff VALUE ] start/stop use USDT to buy BTC \n"
    #                             + "[ /set_trade_b2u_onoff VALUE ] start/stop sell BTC to be USDT \n"
    #                             + "[ /set_eat_kfc_point VALUE ] In the node, compare the purchase price of BTC, how much it can be sold if it rises \n"
    #                             + "[ /set_force_sell_point VALUE ] In the node, compare the purchase price of BTC, how much it falls to force selling \n")


    def __press_button_callback(self, update: Update, context: CallbackContext):
        try:
            query = update.callback_query
            answer = query.data
            who = query.from_user 
            chat_id = str(query.message.chat_id)
        except Exception as e:
            print(e)

        l_ugly_help_list = ['callback_status', 'callback_k8s_monitor', 'callback_stop', 'callback_start', 'callback_restart', 'callback_more'] 
        # , "callback_update_btc_robot", "callback_update_telegram_robot","callback_set_area","callback_set_market"]

        command = ""

        if answer in l_ugly_help_list:
            if answer == 'callback_status':
                command = "host_status"
            elif answer == 'callback_k8s_monitor':
                command = "k8s_monitor"
            elif answer == 'callback_restart':
                command = "host_restart"
            elif answer == 'callback_more':
                command = "more"
            # elif answer == "callback_update_btc_robot":
            #     command = "update_btc_robot"
            # elif answer == "callback_update_telegram_robot":
            #     command = "update_telegram_robot"
            # elif answer == "callback_set_area":
            #     command = "set_area"
            # elif answer == "callback_set_market":
            #     command = "set_market"
            else:
                command = "unknown" ## ???
        else:
            command = "unknown"

        if command == "unknown" or command == "" or command is None:
            # self.logger.error("we not support callback tag={} ".format(answer))
            update.callback_query.edit_message_text("we not support callback tag={} ".format(answer))
        elif command == "more":
            update.callback_query.edit_message_text("[ /more ] to check the detail")
        #     self.__sendMessageToTypicalChat(chat_id, 
        #         + "[ /offecho ] do not accept broadcast message at this chat\n "
        #         + "[ /broadcast ] send message to all chat auth to this bot (need add the message)\n")
        # elif re.search("update", command):
        #     self.__sendMessageToTypicalChat(chat_id, "[ /{} ] use this command to start update \n".format(command))
        # elif re.search("set", command):
        #     self.__sendMessageToTypicalChat(chat_id, "[ /{} ] use this command to start set \n".format(command))
        elif re.search("callback", answer):
            l_currntT = round(time.time()*100)*0.01
            count = self.__chatpool.count(chat_id)
            if count > 0:
                l_dict = {
                    "command": command,
                    "chat_id": chat_id,
                    "data": None,
                    "timestamp": l_currntT,
                    "timezone": self.__timezone
                }
                # response message after we figure out the requestion
                self.__pushToQueueReq(l_dict, important=False)
                update.callback_query.edit_message_text('ok i got it. please wait for {}.'.format(answer))
            else:
                update.callback_query.edit_message_text("Who are you? I don't service unknown.")

    def __update_binance(self, update: Update, context: CallbackContext):
        if context.args:
            args_word = str(context.args[0]).split()
            self.logger.info("you type {}".format(args_word))

            l_currntT = round(time.time()*100)*0.01
            chat_id = str(update.message.chat_id)
            count = self.__chatpool.count(chat_id)
            if count > 0:
                l_dict = {
                    "command": "update_btc_robot",
                    "chat_id": chat_id,
                    "data": args_word,
                    "timestamp": l_currntT,
                    "timezone": self.__timezone
                }
                # response message after we figure out the requestion
                self.__pushToQueueReq(l_dict, important=False)
                update.callback_query.edit_message_text('ok i got it. please wait for updating ... Binance bot')
            else:
                update.callback_query.edit_message_text("Who are you? I don't service unknown.")
        else:
            self.logger.info("I don't recv. any data.")
            update.callback_query.edit_message_text("[ /new_binance VERSION ] you need to give me the VERSION")

    def __update_telegram(self, update: Update, context: CallbackContext):
        # l_currntT = round(time.time()*100)*0.01
        chat_id = str(update.message.chat_id)
        count = self.__chatpool.count(chat_id)
        manualTimezone = pytz.timezone(self.__timezone)
        l_now = datetime.now(manualTimezone)

        if count > 0:
            l_dict = {
                "result": "success",
                "clock": "{}".format(l_now),
                "feedback": "please wait update finish",
                "timecost": "0.001 seconds"
            }
            # response message after we figure out the requestion
            self.sendMessageByURL(chat_id, l_dict)
            update.callback_query.edit_message_text('ok i got it. please wait for updating ... TG bot')

            self.__stop(3) # stop system after 3 sec.
        else:
            update.callback_query.edit_message_text("Who are you? I don't service unknown.")

    def __renew_mix_node_setting(self, update: Update, context: CallbackContext):
        if context.args:
            args_word = str(context.args[0]).split()
            self.logger.info("you type {}".format(args_word))


            l_currntT = round(time.time()*100)*0.01
            chat_id = str(update.message.chat_id)
            count = self.__chatpool.count(chat_id)
            if count > 0:
                l_dict = {
                    "command": "set_nodes",
                    "chat_id": chat_id,
                    "data": args_word,
                    "timestamp": l_currntT,
                    "timezone": self.__timezone
                }
                # response message after we figure out the requestion
                self.__pushToQueueReq(l_dict, important=False)
                update.callback_query.edit_message_text("ok i got it. please wait for nodes setting to {} ".format(args_word))
            else:
                update.callback_query.edit_message_text("Who are you? I don't service unknown.")
        else:
            self.logger.info("I don't recv. any data.")
            update.callback_query.edit_message_text("[ /set_nodes VALUE ] you need to give me the VALUE")

    def __renew_contract_limit_setting(self, update: Update, context: CallbackContext):
        if context.args:
            args_word = str(context.args[0]).split()
            self.logger.info("you type {}".format(args_word))


            l_currntT = round(time.time()*100)*0.01
            chat_id = str(update.message.chat_id)
            count = self.__chatpool.count(chat_id)
            if count > 0:
                l_dict = {
                    "command": "set_contract_limit",
                    "chat_id": chat_id,
                    "data": args_word,
                    "timestamp": l_currntT,
                    "timezone": self.__timezone
                }
                # response message after we figure out the requestion
                self.__pushToQueueReq(l_dict, important=False)
                update.callback_query.edit_message_text("ok i got it. please wait for contract limit {} ".format(args_word))
            else:
                update.callback_query.edit_message_text("Who are you? I don't service unknown.")
        else:
            self.logger.info("I don't recv. any data.")
            update.callback_query.edit_message_text("[ /set_contract_limit VALUE  ] you need to give me the VALUE")

    def __renew_u2b_onoff_setting(self, update: Update, context: CallbackContext):
        if context.args:
            args_word = str(context.args[0]).split()
            self.logger.info("you type {}".format(args_word))


            l_currntT = round(time.time()*100)*0.01
            chat_id = str(update.message.chat_id)
            count = self.__chatpool.count(chat_id)
            if count > 0:
                l_dict = {
                    "command": "set_trade_u2b_onoff",
                    "chat_id": chat_id,
                    "data": args_word,
                    "timestamp": l_currntT,
                    "timezone": self.__timezone
                }
                # response message after we figure out the requestion
                self.__pushToQueueReq(l_dict, important=False)
                update.callback_query.edit_message_text("ok i got it. please wait for u2b {} ".format(args_word))
            else:
                update.callback_query.edit_message_text("Who are you? I don't service unknown.")
        else:
            self.logger.info("I don't recv. any data.")
            update.callback_query.edit_message_text("[ /set_trade_u2b_onoff VALUE  ] you need to give me the VALUE")

    def __renew_b2u_onoff_setting(self, update: Update, context: CallbackContext):
        if context.args:
            args_word = str(context.args[0]).split()
            self.logger.info("you type {}".format(args_word))


            l_currntT = round(time.time()*100)*0.01
            chat_id = str(update.message.chat_id)
            count = self.__chatpool.count(chat_id)
            if count > 0:
                l_dict = {
                    "command": "set_trade_b2u_onoff",
                    "chat_id": chat_id,
                    "data": args_word,
                    "timestamp": l_currntT,
                    "timezone": self.__timezone
                }
                # response message after we figure out the requestion
                self.__pushToQueueReq(l_dict, important=False)
                update.callback_query.edit_message_text("ok i got it. please wait for b2u {} ".format(args_word))
            else:
                update.callback_query.edit_message_text("Who are you? I don't service unknown.")
        else:
            self.logger.info("I don't recv. any data.")
            update.callback_query.edit_message_text("[ /set_trade_b2u_onoff VALUE  ] you need to give me the VALUE")

    def __renew_sell_point_setting(self, update: Update, context: CallbackContext):
        if context.args:
            args_word = str(context.args[0]).split()
            self.logger.info("you type {}".format(args_word))


            l_currntT = round(time.time()*100)*0.01
            chat_id = str(update.message.chat_id)
            count = self.__chatpool.count(chat_id)
            if count > 0:
                l_dict = {
                    "command": "set_eat_kfc_point",
                    "chat_id": chat_id,
                    "data": args_word,
                    "timestamp": l_currntT,
                    "timezone": self.__timezone
                }
                # response message after we figure out the requestion
                self.__pushToQueueReq(l_dict, important=False)
                update.callback_query.edit_message_text("ok i got it. please wait for sell when {} ".format(args_word))
            else:
                update.callback_query.edit_message_text("Who are you? I don't service unknown.")
        else:
            self.logger.info("I don't recv. any data.")
            update.callback_query.edit_message_text("[ /set_eat_kfc_point VALUE  ] you need to give me the VALUE")

    def __renew_force_sell_point_setting(self, update: Update, context: CallbackContext):
        if context.args:
            args_word = str(context.args[0]).split()
            self.logger.info("you type {}".format(args_word))


            l_currntT = round(time.time()*100)*0.01
            chat_id = str(update.message.chat_id)
            count = self.__chatpool.count(chat_id)
            if count > 0:
                l_dict = {
                    "command": "set_force_sell_point",
                    "chat_id": chat_id,
                    "data": args_word,
                    "timestamp": l_currntT,
                    "timezone": self.__timezone
                }
                # response message after we figure out the requestion
                self.__pushToQueueReq(l_dict, important=False)
                update.callback_query.edit_message_text("ok i got it. please wait for force sell when {} ".format(args_word))
            else:
                update.callback_query.edit_message_text("Who are you? I don't service unknown.")
        else:
            self.logger.info("I don't recv. any data.")
            update.callback_query.edit_message_text("[ /set_force_sell_point VALUE  ] you need to give me the VALUE")

