import os
import json
from bfxapi import Client
from bfxapi.client import WS_HOST, REST_HOST
from bfxapi.models.order import OrderType

from model.account import Account
from utils.sqs import SqsUtils
from utils.storage import Storage
from utils.telebot import TelebotUtils
from decimal import Decimal, getcontext, Inexact, Rounded

class GlobalContext:
  '''
    Global Context object, holding all the object during the runtime
    and some convient functions
  '''
  # singleton pattern, keep only one instance of GlobalConfig
  _instance = None
  _inited = False
  
  def __new__(cls, *args, **kwargs):
    if cls._instance is None:
      cls._instance = super(GlobalContext, cls).__new__(cls, *args, **kwargs)
    return cls._instance
  
  accounts = {}
  telebotUtils : TelebotUtils
  sqs: SqsUtils
  storage : Storage
  
  def __init__(self):
    if self._inited:
      return
    
    self.accounts = {}
    self.bfxs = {}
    
    self.storage = Storage()
    all_accounts = self.storage.loadAllObjects(Account)
    
    for account in all_accounts:
      self.accounts[account.account_name] = account
      self.bfxs[account.account_name] = Client(API_KEY=account.bfx_key, API_SECRET=account.bfx_secret)
    
    self.teleBot = TelebotUtils(all_accounts)
    
    self.sqs = SqsUtils()

    self._inited = True
  
  def getBfx(self, account_name):
    return self.bfxs[account_name]
      

  def checkUserIdVsAccountId(self, user_id, account_id):
    for account in self.accounts.values():
      if account.user_id == user_id and account.id == account_id:
        return True
    return False