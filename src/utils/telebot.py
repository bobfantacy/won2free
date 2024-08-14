import io
import os
import json
import telebot
from telebot import types
from queue import Queue


class TelebotUtils:
  
  _instance = None
  _inited = False
  # singleton pattern
  def __new__(cls, *args, **kwargs):
    if cls._instance is None:
      cls._instance = super(TelebotUtils, cls).__new__(cls)
    return cls._instance
  
  def __init__(self, accounts):
    if not self._inited:
      self._account_map = {}
      self._msgBufs = {}
      for account in accounts:
        self._msgBufs[account.account_name] =  Queue()
        self._account_map[account.account_name] = account
      self.teleBot = telebot.TeleBot(os.getenv('TG_TOKEN'))
      self._inited = True
      
  def set_webhook(self, url):
    return self.teleBot.set_webhook(url)
    
  def buffer_message(self, account_name, message):
    if(message!=''):
      self._msgBufs[account_name].put(message)
      
  def send_message(self, account_name, message = ''):
    if(message!=''):
      self._msgBufs[account_name].put(message)
    
    if(not self._msgBufs[account_name].empty()):
      buffer = io.StringIO()
      while not self._msgBufs[account_name].empty():
        buffer.write(self._msgBufs[account_name].get())
        buffer.write("\n")
      message = buffer.getvalue()
      size = 4096
      msgs = [message[i:i+size] for i in range(0, len(message), size)]
      account = self._account_map[account_name]
      for msg in msgs:
        self.teleBot.send_message(account.user_id, text = msg)