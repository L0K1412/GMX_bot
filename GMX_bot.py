#import os

import telebot

from GMX_api_dune import *

#BOT_TOKEN = os.environ.get('BOT_TOKEN')

#GMX bot: -724598287
#Test bot: -859345214

BOT_TOKEN = '6001644146:AAHcfm3XxlAxQQzBJeaElYk3ktyjk0urzlI'

bot = telebot.TeleBot(BOT_TOKEN)

#bot.send_message(-724598287, 'start test')

# @bot.message_handler(commands=['start', 'hello'])
# def send_welcome(message):
#     bot.reply_to(message, "Chat id:")
#     bot.send_message(message.chat.id, message.chat.id)

# bot.send_message(-859345214, 'start test')

def run_bot():    
    all_query = ['2621909','2462605','2649390','2655347','2747633']
    
    for query in all_query:
        text = run_query(query)
        for item in text:
            bot.send_message(-724598287, item, parse_mode="HTML")
            #bot.send_message(-859345214, item, parse_mode="HTML")
            time.sleep(5)
    
run_bot()

#bot.infinity_polling()