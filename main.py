#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from threading import Thread
import logging
import subprocess

from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

with open("token", "r") as fd:
    token = fd.readline().strip()

allowed_ids = {"conrad784": "12467755"}


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


# error handling
def error(bot, update, error):
    logger = logging.getLogger()
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def main():
    logger = logging.getLogger()
    updater = Updater(token=token)
    dispatcher = updater.dispatcher

    # Add your other handlers here...

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
        bot.send_message(chat_id=update.message.chat_id, text=update.message.text)

    echo_handler = MessageHandler(Filters.text, echo)
    dispatcher.add_handler(echo_handler)

    def mscs_restart(bot, update):
        ret = restart_servers()
        bot.send_message(chat_id=update.message.chat_id, text="{}".format(ret))

    mscs_restart_handler = CommandHandler("mscs_restart", mscs_restart)
    dispatcher.add_handler(mscs_restart_handler)

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
