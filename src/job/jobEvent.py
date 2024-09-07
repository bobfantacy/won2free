import sys
import time
import logging
import os
import random

from utils.sqs import SqsUtils
from utils.storage import Storage
from model.account import Account
import uuid


logging.basicConfig(
    format='%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO  # Set the desired logging level (INFO, WARNING, ERROR, etc.)
)
logger = logging.getLogger(__name__)

sqs = SqsUtils()
storage = Storage()

def ReArrangeOffer(event, context):
  command = 'ReArrangeOffer'
  commandEvent(command)
  
def TradeStatusCheck(event, context):
  command = 'TradeStatusCheck'
  commandEvent(command)
  
def AutoFundingRate(event, context):
  command = 'AutoFundingRate'
  commandEvent(command)

def TradeReport(event, context):
  command = 'TradeReport'
  commandEvent(command)

def commandEvent(command):
  accounts = storage.loadAllObjects(Account)
  for account in accounts:
    event = {
      'id': str(uuid.uuid4()),
      'body' : {
        'command' : command,
        'account_name' : account.account_name,
        'data' : ''
      }
    }
    sqs.send_message(event)