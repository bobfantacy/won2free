from abc import ABC, abstractmethod
from utils.global_context import *
from datetime import datetime
from cachetools import cached, TTLCache
from model.trade_order import TradeOrder
from model.funding_offer import FundingOffer
from model.lending_plan import LendingPlan
from bfxapi.models.funding_offer import FundingOffer as BfxFundingOffer
from model.sync_tick import SyncTick
from bfxapi.models.order import Order
from bfxapi.models.notification import Notification
from bfxapi.utils.auth import calculate_order_flags
import logging
import time
import io

logger = logging.getLogger(__name__)
cache = TTLCache(maxsize=10, ttl=2)

class AbstractAction(ABC):
  def __init__(self, commands):
    #make all command in commands to lower
    for i in range(len(commands)):
      commands[i] = commands[i].lower()
    self.commands = commands
    self.context = GlobalContext()
    self.teleBot = self.context.teleBot
    self.storage = self.context.storage
  
  def match(self, _command):
    for command in self.commands:
      if  _command.lower() == command:
        return True
    return False
  
  async def execute(self, event_body):
    try:
      if 'data' not in event_body:
        event_body['data'] = []
      self._before_execute(event_body)
      await self._execute(event_body)
      self._after_execute(event_body)
    except Exception as e:
      logger.error(e)
      pass
      
  def _before_execute(self, event_body):
    self.command = event_body.get('command')
    self.account_name = event_body['account_name']
    self.bfx = self.context.bfxs[self.account_name]
    self.account = self.context.accounts[self.account_name]
  
  def _after_execute(self, event_body):
    self.flush_message()
  
  @abstractmethod
  async def _execute(self, event_body):
    pass
  
  async def cancel_all_funding_offers(self, account_name):
    endpoint = f"auth/w/funding/offer/cancel/all"
    raw_info = await self.bfx.rest.post(endpoint)
    
  async def cancel_funding_offers(self, offer_ids):
    for offer_id in offer_ids:
      try:
        await self.bfx.rest.submit_cancel_funding_offer(offer_id)
        self.storage.deleteObjectById(FundingOffer, offer_id)
      except Exception as e:
        pass
  async def get_wallet_balance_available(self, type, currency):
    wallets = await self.bfx.rest.get_wallets()
    for wallet in wallets:
      if(wallet.currency == currency and wallet.type == type):
        return wallet.balance_available
    return 0
  async def cancelOrder(self,orderIds):
    try:
      await self.bfx.rest.submit_cancel_order_multi(ids = orderIds)
      for orderId in orderIds:
        self.storage.deleteObjectById(TradeOrder, orderId)
    except Exception as e:
      self.teleBot.buffer_message(self.account_name, f"Error: {e}")
      return
  async def submit_update_order(self, orderId, price=None, amount=None, delta=None, price_aux_limit=None,
                                  price_trailing=None, hidden=False, close=False, reduce_only=False,
                                  post_only=False, time_in_force=None, leverage=None, aff_code=None):
        """
        Refer to the bfx rest api, add aff_code argument
        """
        payload = {"id": orderId,
                   "meta": {}}
        if price != None:
            payload['price'] = str(price)
        if amount != None:
            payload['amount'] = str(amount)
        if delta != None:
            payload['delta'] = str(delta)
        if price_aux_limit != None:
            payload['price_aux_limit'] = str(price_aux_limit)
        if price_trailing != None:
            payload['price_trailing'] = str(price_trailing)
        if time_in_force != None:
            payload['tif'] = str(time_in_force)
        if leverage != None:
            payload["lev"] = str(leverage)
        flags = calculate_order_flags(
            hidden, close, reduce_only, post_only, False)
        payload['flags'] = flags
        if aff_code != None:
            payload['meta']['aff_code'] = str(aff_code)
        endpoint = "auth/w/order/update"
        raw_notification = await self.bfx.rest.post(endpoint, payload)
        return Notification.from_raw_notification(raw_notification)
  async def update_order(self, order_id, amount, price, strategy_id = 0, oper_count = 0):
    try:
      response = await self.submit_update_order(int(order_id), price=price, amount=amount)
      if(response.status == 'SUCCESS'):
        o = response.notify_info
        # each item is in the form of an Order object
        order = TradeOrder.from_bfx_order(o)
        order.user_id = self.account.user_id
        order.account_id = self.account.id
        order.strategy_id = strategy_id
        order.oper_count = oper_count
        self.storage.saveObject(order)
        self.buffer_message(f"Update Order: {order.symbol}, {amount:.6f}, {price:6.3f}")
      else:
        raise Exception('Error in Update Order!')
    except Exception as e:
      logger.error(e)
      self.buffer_message(f"Update Order Error: {order_id}, {amount:.6f}, {price:6.3f} {e}")
      raise Exception(e)
    
  def flush_message(self):
    self.teleBot.send_message(self.account_name, message = '')
      
  def buffer_message(self, message):
    self.teleBot.buffer_message(self.account_name, message)
    
  async def get_bfx_trades(self, start, end):
    trades = await self.bfx.rest.get_trades(start=start, end=end,limit=2000)
    return trades
  async def get_bfx_active_order(self, ids = None):
    endpoint = "auth/r/orders"
    payload = {}
    if ids:
        payload['id'] = ids
    raw_orders = await self.bfx.rest.post(endpoint, payload)
    return [Order.from_raw_order(ro) for ro in raw_orders]
  
  async def get_bfx_order_history(self, start=None, end = None, limit=25, sort=-1, ids=None):
    endpoint = "auth/r/orders/hist"
    payload = {}
    if start:
        payload['start'] = start
    if end:
        payload['end'] = end
    if limit:
        payload['limit'] = limit
    if sort:
        payload['sort'] = sort
    if ids:
        payload['id'] = ids
    raw_orders = await self.bfx.rest.post(endpoint, payload)
    return [Order.from_raw_order(ro) for ro in raw_orders]
  
  async def submit_order(self, symbol, amount, price, strategy_id = 0, oper_count = 0):
    try: 
      response = await self.bfx.rest.submit_order(symbol=symbol, 
                                                  amount=amount, 
                                                  price=price, 
                                                  market_type=OrderType.EXCHANGE_LIMIT, 
                                                  aff_code=self.account.affiliate_code)
      for o in response.notify_info:
        # each item is in the form of an Order object
        order = TradeOrder.from_bfx_order(o)
        order.user_id = self.account.user_id
        order.account_id = self.account.id
        order.strategy_id = strategy_id
        order.oper_count = oper_count
        self.storage.saveObject(order)
        self.buffer_message(f"Submit Order: {symbol}, {amount:.6f}, {price:6.3f}")
    except Exception as e:
      logger.error(e)
      self.buffer_message(f"Submit Order Fail: {symbol}, {amount:.6f}, {price:6.3} \n {e}")
      raise Exception(e)
  async def buy(self, symbol, amount, price, strategy_id = 0, oper_count = 0):
    if(amount < 0):
      raise Exception("amount should be larger then zero")
    logger.info(f"Buy {symbol=}, {amount=}, {price=}")
    await self.submit_order(symbol, amount, price, strategy_id, oper_count)
    
  async def sell(self, symbol, amount, price, strategy_id = 0, oper_count = 0):
    if(amount < 0):
      raise Exception("amount should be larger then zero")
    logger.info(f"Sell {symbol=}, {amount=}, {price=}")
    await self.submit_order(symbol, -amount, price, strategy_id, oper_count)
    
  async def getAllActiveFundingOffers(self):
    endpoint = "auth/r/funding/offers"
    offers = await self.bfx.rest.post(endpoint)
    return [BfxFundingOffer.from_raw_offer(o) for o in offers]
  @cached(cache)
  def getSyncTick(self):
    filter_lambda = lambda Attr: Attr('account_id').eq(self.account.id)
    items = self.storage.loadObjects(Account, filter_lambda)
    if len(items) == 0:
      now = int(round(time.time() * 1000))
      then = now - (1000 * 60 * 60 * 24 * 60)
      syncTick = SyncTick(
        account_id = self.account.id, 
        trade_last_sync = then,
        loan_last_sync = then,
        credit_last_sync = then
      )
      return syncTick
    else:
      return items[0]
  
  @cached(cache)
  async def query_funding_orders(self, symbol = 'fUSD'):
    offers = await self.bfx.rest.get_funding_offers(symbol)
    offerVos = []
    totalAmount = 0
    for offer in offers:
      offerVos.append({"id": offer.id, "symbol": offer.symbol, "amount": offer.amount, "rate": offer.rate*100, "period": offer.period})
      totalAmount = totalAmount + offer.amount
    return (totalAmount, offerVos)