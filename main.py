#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from threading import Thread
import logging
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

#------------------------------- My functions -------------------------------
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
    return execute_shell("mscs restart {}".format(servers))

def server_status(servers=""):
    return execute_shell("mscs status {}".format(servers))


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
        servers = msg.text.split(" ", 1)[1]
        ret = restart_servers(servers)
        logger.info("Server restarted by id {}".format(update.message.chat_id))
        bot.send_message(chat_id=update.message.chat_id, text="{}".format(ret))

    mscs_restart_handler = CommandHandler("mscs_restart", mscs_restart)
    dispatcher.add_handler(mscs_restart_handler)

    @restricted
    @send_typing_action
    def mscs_status(bot, update):
        msg = update.message
        logger.info("Server status issued by '{}'".format(msg.from_user))
        logger.debug("With message {}".format(msg.text))
        server = msg.text.split(" ", 1)[1]
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
