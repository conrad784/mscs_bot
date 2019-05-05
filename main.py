#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from threading import Thread
import logging
import pickle
import time
import subprocess
from functools import wraps

from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram import ChatAction

from secret import allowed_ids

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# read the telegram token
with open("token", "r") as fd:
    token = fd.readline().strip()

LIST_OF_ADMINS = list(allowed_ids.values())
logging.info("List of admins: {}".format(LIST_OF_ADMINS))


#------------------------------- Telegram wrapper functions -------------------------------
def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        logger = logging.getLogger()
        user_id = context.effective_user.id
        logger.debug("Getting restricted call by {}".format(user_id))
        if user_id not in LIST_OF_ADMINS:
            logger.info("Unauthorized access denied for {}.".format(user_id))
            return
        return func(update, context, *args, **kwargs)
    return wrapped


def send_action(action):
    """Sends `action` while processing func command."""
    def decorator(func):
        @wraps(func)
        def command_func(*args, **kwargs):
            bot, update = args
            bot.send_chat_action(chat_id=update.effective_message.chat_id, action=action)
            return func(bot, update, **kwargs)
        return command_func
    return decorator

send_typing_action = send_action(ChatAction.TYPING)
send_upload_video_action = send_action(ChatAction.UPLOAD_VIDEO)
send_upload_photo_action = send_action(ChatAction.UPLOAD_PHOTO)

#----------------------------- Helper functions -----------------------------
def get_text_from_message(message):
    logger = logging.getLogger()
    logger.debug("Got message to split: {}".format(message))
    text = message.split(" ", 1)[1:]
    logger.debug("Text output: {}".format(text))
    if text:
        return text[0]
    else:
        return ""
#------------------------------- My functions -------------------------------
class CommandCache(str):
    def __init__(self, string):
        super().__init__()
        self.timestamp = time.time()


def execute_shell(cmd):
    logger = logging.getLogger()
    cmd_list = cmd.strip().split()
    # WARNING, this should be sanitized beforehand as this is user input
    logger.debug(cmd_list)
    try:
        out = subprocess.check_output(cmd_list)
        return out.decode("utf-8")
    except FileNotFoundError:
        logger.error("Binary not found")
    except subprocess.CalledProcessError:
        logger.error("Non-zero exit status")


def restart_servers(servers=""):
    logger = logging.getLogger()
    now = time.time()
    try:
        logger.debug("When was the last time this server was restarted")
        with open("/tmp/mscs_restarted.pickle", "rb") as f:
            last_restarted = pickle.load(f)
        if now-last_restarted < 30:
            logger.info("Restarted in the last 30s, not restarting.")
            ret = "Restarted in the last 30s, not restarting."
        else:
            raise FileNotFoundError
    except (FileNotFoundError, EOFError):
        with open("/tmp/mscs_restarted.pickle", "wb") as f:
            pickle.dump(now, f)
        ret = execute_shell("mscs restart {}".format(servers))
    return ret

def server_status(servers=""):
    logger = logging.getLogger()
    now = time.time()
    try:
        logger.debug("Trying to read cached command")
        with open("/tmp/mscs_status.pickle", "rb") as f:
            status = pickle.load(f)
        if now-status.timestamp < 10:
            logger.info("Cache valid")
            ret = status
        else:
            logger.debug("Cache too old")
            raise FileNotFoundError
    except (FileNotFoundError, EOFError):
        ret = execute_shell("mscs status {}".format(servers))
        with open("/tmp/mscs_status.pickle", "wb") as f:
            pickle.dump(CommandCache(ret), f)
    return ret


# error handling
def error(bot, update, error):
    logger = logging.getLogger()
    logger.warning('Update "%s" caused error "%s"' % (update, error))


#--------------------------- main function with all handlers ----------------------------
def main():
    logger = logging.getLogger()
    updater = Updater(token=token)
    dispatcher = updater.dispatcher

    # Add your other handlers here...
    # MessageHandler will handle messages and
    # CommandHandler will hanle /messages
    # this means telegram.ext.filters are applied beforehand
    # such that e.g. audio and video are not reaching the handler

    def stop_and_restart():
        """Gracefully stop the Updater and replace the current process with a new one"""
        updater.stop()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def restart(bot, update):
        update.message.reply_text('Bot is restarting...')
        Thread(target=stop_and_restart).start()

    dispatcher.add_handler(CommandHandler('r', restart,
                                          filters=Filters.user(username='@conrad784')))

    def start(bot, update):
        bot.send_message(chat_id=update.message.chat_id,
                         text="This Bot is work in progress, expect it not to work!")

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    def echo(bot, update):
        logger.debug("Echoing '{}' to id: {}".format(update.message.text, update.message.chat_id))
        bot.send_message(chat_id=update.message.chat_id, text=update.message.text)

    echo_handler = MessageHandler(Filters.text, echo)
    dispatcher.add_handler(echo_handler)

    @restricted
    @send_typing_action
    def mscs_restart(bot, update):
        msg = update.message
        servers = get_text_from_message(msg.text)
        logger.info("Server restarted by id {}".format(msg.from_user))
        logger.debug("With message {}".format(msg.text))
        ret = restart_servers(servers)
        bot.send_message(chat_id=update.message.chat_id, text="{}".format(ret))

    mscs_restart_handler = CommandHandler("mscs_restart", mscs_restart)
    dispatcher.add_handler(mscs_restart_handler)

    @restricted
    @send_typing_action
    def mscs_status(bot, update):
        msg = update.message
        servers = get_text_from_message(msg.text)
        logger.info("Server status issued by '{}'".format(msg.from_user))
        logger.debug("With message {}".format(msg.text))
        ret = server_status(servers)
        bot.send_message(chat_id=update.message.chat_id, text="{}".format(ret))

    mscs_status_handler = CommandHandler("mscs_status", mscs_status)
    dispatcher.add_handler(mscs_status_handler)

    def unknown(bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")
    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)

    # handle errors
    dispatcher.add_error_handler(error)

    # start Bot
    logger.info("Starting Bot")
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
