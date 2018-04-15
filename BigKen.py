from telegram.ext import Updater, CommandHandler
import logging
import requests
import argparse
import yaml
import sys
import os
import json

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


def sendWeatherMessage(bot, update):
    kToC = -273.00
    weather_url = "api.openweathermap.org"
    weather_api_key = "8284bc8e06adb8cf477f720efaf4b874"
    logger.info("Sending weather message")
    req = requests.get("http://{}/data/2.5/weather".format(weather_url), params={'q': 'London', 'APPID': weather_api_key})
    temp = (req.json().get("main").get("temp") + kToC)
    tempMin = ((req.json().get("main").get("temp_min")) + kToC)
    tempMax = ((req.json().get("main").get("temp_max")) + kToC)
    update.message.reply_text("Hi Guys, the temperature is " + str(int(temp)) + " with a minimum of " + str(int(tempMin)) +
                              " and max of "+ str(int(tempMax))) + "."


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
    bot = dp.bot

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("weather", sendWeatherMessage))
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

    logger = logging.getLogger('bigken')


    if os.path.exists(args.config):
        with open(args.config, 'r') as ymlfile:
            config = yaml.load(ymlfile)
    else:
        logger.error("Couldn't find config file at {}".format(args.config))
        sys.exit(1)

    if args.debug:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=level)

    main(config)
