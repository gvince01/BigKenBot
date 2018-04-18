#!/usr/bin/env python3

import logging
import requests
import argparse
import yaml
import sys
import os

from telegram.ext import Updater, CommandHandler
from handler import ArgumentHandler


def start(bot, update):
    logger.info("Called start")
    update.message.reply_text("YES YES YES BOYS")

def help(bot, update):
    logger.info("Called help")
    update.message.reply_text("The commands I currently support are the following:"
                                "\n /set <mintues> creates an alarm. "
                                "\n /unset - deletes the alarm"
                                "\n /weather - lets you know what the weather will be like tomorrow + % chance of rain"
                                "\n /weather temp - tells you the current temperature"
                                "\n /tube status of all underground tube lines"
                                "\n /strudel to set a strudel timer")


def alarm(bot, job, message = "THE TIME IS UP!!!"):
    logger.info("Called alarm")
    bot.send_message(job.context, text = message)


def tempReply(bot, update, temperature):
    logger.info("Called tempReply")
    if temperature < 0:
        message = "Fuck it's cold boys"
    elif temperature < 5:
        message = "It's might chilly boys"
    elif temperature < 10:
        message = "A wee bit nippy"
    elif temperature < 15:
        message = "Not too bad"
    else:
        message = "Taps-aff"
    message += ' ({})'.format(temperature)
    update.message.reply_text(message)


def weatherDarkSky(bot, update, args, arguments):
    logger.info("Sending weather message")
    req = requests.get("https://api.darksky.net/forecast/{}/{},{}".format(config['darksky']['api_key'], config['lat'], config['lon']))
    temp = int((req.json()['currently']['temperature'] - 32) * 5/9) #maybe put this in a function
    hourlySummary = req.json()['hourly']['summary']
    hourlySummary += " {}% chance of rain.".format(req.json()['hourly']['data'][0]['precipProbability'] * 100)
    try:
        if not args:
            update.message.reply_text(hourlySummary)
        elif args[0] == "temp":
            tempReply(bot, update, temp)
        else:
            update.message.reply_text("Go outside and take a look")
    except Exception as e:
        logger.error("Something went wrong while getting the weather")
        print(e)


def set_timer(bot, update, args, job_queue, chat_data):
    logger.info("Called set_timer")
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        due = int(args[0]) * 60 #minutes into seconds
        if due < 0:
            update.message.reply_text('Sorry we can not go back to future!')
            return
        # Add job to queue
        job = job_queue.run_once(alarm, due, context=chat_id)
        chat_data['job'] = job

        update.message.reply_text('Timer successfully set!')

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /set <minutes>')


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


def strudel(bot, update, job_queue, chat_data): #custom message needs to be set
    strudel_time = ["45"]
    set_timer(bot, update, strudel_time, job_queue, chat_data)


def tflLineStatus(bot, update, args, arguments):
    logger.info("Called TFL Line Status")
    req = requests.get("https://api.tfl.gov.uk/Line/Mode/tube/Status?app_id={}&app_key={}".format(config['tfl']['app_id'],config['tfl']['api_key']))
    stringPrinter = ""
    for i in range(0, 10):
        tempString = ("{} - {}".format(req.json()[i]['name'], req.json()[i]['lineStatuses'][0]['statusSeverityDescription']))
        stringPrinter += tempString + "\n"

    update.message.reply_text(stringPrinter)

def main(config):
    """Run bot."""
    updater = Updater(config['telegram']['api_key'])

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(ArgumentHandler("weather", weatherDarkSky, pass_args=True, arguments=config))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(ArgumentHandler("tube", tflLineStatus, pass_args=True, arguments=config))
    dp.add_handler(CommandHandler("set", set_timer,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True
                                  ))
    dp.add_handler(CommandHandler("strudel", strudel,
                                  pass_job_queue=True,
                                  pass_chat_data=True
                                  ))
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
