#!/usr/bin/env python3

import logging
import requests
import argparse
import yaml
import sys
import os
import json

from telegram.ext import Updater, CommandHandler
from handler import ArgumentHandler


def start(bot, update):
    logger.info("Called start")
    update.message.reply_text("YES YES YES BOYS")

def help(bot, update):
    logger.info("Called help")
    update.message.reply_text("/set + time in seconds to create an alarm. " +
                              "\n /weather - lets you know what the weather will be like tomorrow")


def alarm(bot, job, message = "Someone please water me!"):
    logger.info("Called alarm")
    bot.send_message(job.context, text = message)

def tempReply(bot, update, temp, tempMin, tempMax):
    if temp < 0:
        message = "Fuck it's cold boys"
    elif temp < 5:
        message = "It's might chilly boys"
    elif temp < 10:
        message = "A wee bit nippy"
    elif temp < 15:
        message = "Not too bad"
    else:
        message = "Taps-aff"
    message += ' ({})'.format(temp)
    update.message.reply_text(message)


def sendWeatherMessage(bot, update, args, arguments):
    kToC = -273
    logger.info("Sending weather message")
    req = requests.get("http://{}/data/2.5/weather".format(config['openweather']['weather_url']), params={'lat': config['lat'], 'lon': config['lon'], 'APPID': config['openweather']['api_key']})
    temp = int(req.json().get("main").get("temp") + kToC)
    tempMin, tempMax = int((req.json().get("main").get("temp_min")) + kToC), int((req.json().get("main").get("temp_max")) + kToC)
    try:
        type = args[0]
        if type == "temp":
            tempReply(bot, update, temp, tempMin, tempMax)
        elif type == "cond":
            update.message.reply_text("Outside is {}".format(req.json()['weather'][0]['description']))
        else:
            update.message.reply_text("Go outside and take a look")

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /weather temp -- current temp with min and max' +
                                  "\n /weather cond -- raining etc")
    except Exception as e:
        logger.error("Something went wrong while getting the weather")
        print(e)

def set_timer(bot, update, args, job_queue, chat_data):
    logger.info("Called set_timer")
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        due = int(args[0])
        if due < 0:
            update.message.reply_text('Sorry we can not go back to future!')
            return


        # Add job to queue
        job = job_queue.run_once(alarm, due, context=chat_id)
        chat_data['job'] = job

        update.message.reply_text('Timer successfully set!')

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /set <seconds>')


def unset(bot, update, chat_data):
    logger.info("Called unset")
    """Remove the job if the user changed their mind."""
    if 'job' not in chat_data:
        update.message.reply_text('You have no active timer')
        return

    job = chat_data['job']
    job.schedule_removal()
    del chat_data['job']

    update.message.reply_text('Timer successfully unset!')


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main(config):

    """Run bot."""
    updater = Updater(config['telegram']['api_key'])

    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    dp.chat_data = config

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(ArgumentHandler("weather", sendWeatherMessage, pass_args=True, arguments=config))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("set", set_timer,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("unset", unset, pass_chat_data=True))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("--debug", action='store_true', help='Debug')
    parser.add_argument("--config", help="Config file to read", default='config.yaml')

    args = parser.parse_args()

    if args.debug:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logger = logging.getLogger('bigken')
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=level)

    if os.path.exists(args.config):
        with open(args.config, 'r') as ymlfile:
            config = yaml.load(ymlfile)
    else:
        logger.error("Couldn't find config file at {}".format(args.config))
        sys.exit(1)

    main(config)
