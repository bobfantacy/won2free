import sys
import time
import logging
import os
import random

from utils.sqs import SqsUtils
import uuid


logging.basicConfig(
    format='%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO  # Set the desired logging level (INFO, WARNING, ERROR, etc.)
)
logger = logging.getLogger(__name__)

sqs = SqsUtils()

def ReArrangeFundingOffer():
  event = {
    'id': str(uuid.uuid4()),
    'body' : {
      'command' : 'ReArrangeOffer',
      'account_name' : 'funding',
      'data' : ''
    }
  }
  sqs.send_message(event)
  event = {
    'id': str(uuid.uuid4()),
    'body' : {
      'command' : 'ReArrangeOffer',
      'account_name' : 'exchange',
      'data' : ''
    }
  }
  sqs.send_message(event)
def GridStrategyOper():
  event = {
    'id': str(uuid.uuid4()),
    'body' : {
      'command' : 'TradeStatusCheck',
      'account_name' : 'exchange',
      'data' : ''
    }
  }
  sqs.send_message(event)
  
def AutoFundingRate():
  event = {
    'id': str(uuid.uuid4()),
    'body' : {
      'command' : 'AutoFundingRate',
      'account_name' : 'funding',
      'data' : ''
    }
  }
  sqs.send_message(event)
  event = {
    'id': str(uuid.uuid4()),
    'body' : {
      'command' : 'AutoFundingRate',
      'account_name' : 'exchange',
      'data' : ''
    }
  }
  sqs.send_message(event)