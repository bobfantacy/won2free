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
context = GlobalContext()
bot = context.teleBot._teleBot
sqs = context.sqs

MINIAPP_URL = os.getenv('MINIAPP_URL')

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    chat_id = message.chat.id
    chat_type = message.chat.type
    if chat_type == 'private':
        try:
            keyboard = InlineKeyboardMarkup()
            web_app_info = WebAppInfo(url=MINIAPP_URL)
            keyboard.add(InlineKeyboardButton("Fun my Fund!", web_app=web_app_info))
            bot.send_message(chat_id, 'Welcome to Won2Free!\n A free, simple, easy bot for Bitfinex!', reply_markup=keyboard)
        except Exception as error:
            print('Error sending message:', error)
    else:
        bot.send_message(chat_id, 'This bot only works in private chat!')

@bot.message_handler(commands=['cmd'])
def send_command_help(message):
    welcome_text = '''
    Welcome to Trade AI!
    /help *
    /fund *
    /exchange *
    '''
    bot.reply_to(message, welcome_text)
    
@bot.message_handler(commands=['fund'])
def send_fund(message):
    fund_message = '''
    Funding Action:
    /ReArrangeOffer
    /AutoFundingRate
    /FundingSummary
    /FundingNotification
    '''
    bot.reply_to(message, fund_message)
    
@bot.message_handler(commands=['exchange'])
def send_exchange(message):
    exchange_message = '''
    Exchange Action:
    /buy *
    /sell *
    /ResumeGrid *
    /TradeStatusCheck *
    /TradeReport *
    '''
    bot.reply_to(message, exchange_message)
    
@bot.message_handler(commands=['echo'])
def echo_message(message):
    bot.reply_to(message, f"thread_id: {message.message_thread_id} chat_id: {message.chat.id} text: {message.text} user_id: {message.from_user.id}")
    
@bot.message_handler(commands=['buy',
                               'sell', 
                               'ResumeGrid',
                               'AutoFundingRate',
                               'ReArrangeOffer',
                               'TradeStatusCheck',
                               'NewLendingPlan',
                               'TestDict',
                               'TradeReport',
                               'FundingSummary',
                               'FundingNotification'])
def bot_action(message):
    logger.info(f"Received a message from telegram: {message.text}")
    
    if not checkUserId(message):
        bot.reply_to(message, 'You are NOT authorized!')
        return 
    try:
        command, account_name, *args = message.text.split()

        account = context.accounts.get(account_name)
        if not account: 
            bot.reply_to(message, f'NOT Found account name: {account_name}')
            return
        if account.user_id != message.from_user.id:
            bot.reply_to(message, f'NOT Authrized to oper {account_name}')
            return
        
        try:
            try_json = ' '.join(args)
            if(try_json[0:1]=='{'):
                args_dict = json.loads(try_json)
                args = args_dict
        except:
            bot.reply_to(message, f'Something wrong with the json args:\n {try_json}')
            return
            
        command = command[1:]
        
        event = {
            'id': str(uuid.uuid4()),
            'body' : {
                'command' : command,
                'user_id': message.from_user.id, 
                'account_name' : account_name,
                'data' : args
            }
        }
        sqs.send_message(event)
    except Exception as e:
        bot.reply_to(message, f'Something went wrong! {e}')
    
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

def checkUserId(message):
    user_id = message.from_user.id
    for account in context.accounts.values():
        if account.user_id == user_id:
            return True
    return False

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