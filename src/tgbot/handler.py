import json
import telebot
from utils.global_context import GlobalContext
from utils.sqs import SqsUtils
from telebot.types import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from datetime import datetime
import uuid
import os
import logging


# Logging is cool!
logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

OK_RESPONSE = {
    'statusCode': 200,
    'headers': {'Content-Type': 'application/json'},
    'body': json.dumps('ok')
}

ERROR_RESPONSE = {
    'statusCode': 400,
    'body': json.dumps('Oops, something went wrong!')
}

bot = telebot.TeleBot(os.getenv('TG_TOKEN'),threaded=False)
MINIAPP_URL = os.getenv('MINIAPP_URL')
sqs = SqsUtils()

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    chat_id = message.chat.id
    chat_type = message.chat.type
    if chat_type == 'private':
        try:
            keyboard = InlineKeyboardMarkup()
            web_app_info = WebAppInfo(url=MINIAPP_URL)
            keyboard.add(InlineKeyboardButton("Open web App", web_app=web_app_info))
            keyboard.add(InlineKeyboardButton("Open Url", url=MINIAPP_URL))
            bot.send_message(chat_id, 'Welcome to my Mini App!', reply_markup=keyboard)
        except Exception as error:
            print('Error sending message:', error)
    else:
        bot.send_message(chat_id, 'This bot only works in private chat!')

@bot.message_handler(commands=['cmd'])
def send_command_help(message):
    welcome_text = '''
    Welcome to Trade AI!
    /help *
    /balance
    /fund *
    /exchange *
    /on
    '''
    bot.reply_to(message, welcome_text)
    
@bot.message_handler(commands=['fund'])
def send_fund(message):
    fund_message = '''
    Funding Action:
    /config
    /lending_plan
    /funding_offer
    /funding_history
    /funding_credit
    /funding_loan
    /earning
    /candle
    /ReArrangeFundingOffer
    /AutoFundingRate
    /FundingSummary
    /syncFunding
    '''
    bot.reply_to(message, fund_message)
    
@bot.message_handler(commands=['exchange'])
def send_exchange(message):
    exchange_message = '''
    Exchange Action:
    /buy *
    /sell *
    /orders *
    /cancelOrder 
    /updateOrder
    /createGrid
    /initGrid
    /ResumeGrid
    /showGrid
    /tradeHistory
    /syncTradeHistory
    '''
    bot.reply_to(message, exchange_message)
    
@bot.message_handler(commands=['echo'])
def echo_message(message):
    
    bot.reply_to(message, f"thread_id: {message.message_thread_id} chat_id: {message.chat.id} text: {message.text} user_id: {message.from_user.id}")
    
@bot.message_handler(commands=[
                              'balance',
                              'lending_plan',
                              'on',
                              'funding_offer','funding_history','funding_credit','funding_loan',
                              'earning','candle','ReArrangeFundingOffer','AutoFundingRate','FundingSummary',
                              'buy','sell','orders','cancelOrder','updateOrder','createGrid',
                              'initGrid','ResumeGrid','showGrid','tradeHistory','syncTradeHistory','syncFunding'])
def bot_action(self, message):
    logger.info(f"Received a message from telegram: {message.text}")
    command, account_name, *args = message.text.split()
    command = command[1:]
    # toUpperCase 
    # self.bot.reply_to(message, f"你输入的命令是:{command}")
    event = {
        'id': str(uuid.uuid4()),
        'body' : {
            'chat_id' : message.chat.id,
            'message_thread_id':message.message_thread_id,
            'account_name' : account_name,
            'data' : args
        }
    }
    sqs.send_message(event)
    
def webhook(event, context):
    """
    Runs the Telegram webhook.
    """
    logger.info('Event: {}'.format(event))

    if event.get('httpMethod') == 'POST' and event.get('body'): 
        update = Update.de_json(event.get('body'))
        message = update.message
        if hasattr(message, 'chat'):
            bot.process_new_messages([message])
        return OK_RESPONSE
    return ERROR_RESPONSE

def set_webhook(event, context):
    """
    Sets the Telegram bot webhook.
    """
    logger.info('Event: {}'.format(event))
    
    url = 'https://{}/{}/'.format(
        event.get('headers').get('Host'),
        event.get('requestContext').get('stage'),
    )
    print(f"url: {url}")
    webhook = bot.set_webhook(url)
    print(f"result: {webhook}")

    if webhook:
        return OK_RESPONSE

    return ERROR_RESPONSE