from reactor.AbstractAction import AbstractAction
from datetime import datetime, timedelta
from utils.global_context import *
from model.trade_order import TradeOrder
from model.trade_order_history import TradeOrderHistory
from model.order_grid_strategy import OrderGridStrategy
from model.trade_order_stat import TradeOrderStat
from decimal import Decimal
import time
import logging
import time

logger = logging.getLogger(__name__)

class BotActionTradeStatusCheck(AbstractAction):
  def __init__(self):
    super().__init__(commands=['TradeStatusCheck'])
    
  async def _execute(self, event_body):

    filter_lambda = lambda Attr: Attr('account_id').eq(self.account.id)
    orders = self.storage.loadObjects(TradeOrder, filter_lambda)
    
    if not orders:
      return
    
    orderIds = [int(o.id) for o in orders ]
    
    executedBfxOrders = await self.get_bfx_order_history(ids = orderIds)
    executedTradeOrders = [TradeOrder.from_bfx_order(o) for o in executedBfxOrders]
    for executedTradeOrder in executedTradeOrders:
      for order in orders:
        if executedTradeOrder.id == order.id:
          executedTradeOrder.strategy_id = order.strategy_id
          executedTradeOrder.oper_count = order.oper_count
          executedTradeOrder.account_id = order.account_id
          executedTradeOrder.user_id = order.user_id
          break
      await self.processOrderExecuted(orders, executedTradeOrder)
    if self.account.funding_back_exchange:
      wallet_available = await self.balanceExchangeAndFundingAmount()
      for currency in ['USD','UST']:
        await self.makeShortPeriodFunding(wallet_available, currency)

  async def makeShortPeriodFunding(self, wallet_available, currency = 'USD'):
    funding_balance_available = wallet_available[currency]
    symbol = f'f{currency}'
    if funding_balance_available > 150:
      now = datetime.now()
      start_time = now - timedelta(minutes=300)
      start_timestamp = int(start_time.timestamp())*1000
      end_timestamp = int(now.timestamp())*1000
      funding_history = await self.bfx.rest.get_funding_offer_history(symbol=symbol, start=start_timestamp, end=end_timestamp)
      if not funding_history:
        books = await self.bfx.rest.get_public_books(symbol, precision="P0", length=100)
        highest_rate = 0
        highest_period = 2
        for b in books:
            if b[1] in range(2,6) and b[3] <0 and b[0]>highest_rate:
                highest_rate = b[0]
                highest_period = b[1]
        if highest_rate > 0:
          await self.bfx.rest.submit_funding_offer(symbol, 150, highest_rate, highest_period)
  def get_active_grid_stragegy(self, strategy_id):
    filter_lambda = lambda Attr: Attr('id').eq(strategy_id)
    items = self.storage.loadObjects(OrderGridStrategy, filter_lambda)
    itemsLen = len(items)
    if itemsLen != 1:
      return None
    else:
      return items[0]
  async def balanceExchangeAndFundingAmount(self):
    tokenReserves = self.get_token_reserves(5)
    wallet_balances = await self.bfx.rest.get_wallets()
    wallet_available = {}
    for currency in ['USD','UST','BTC','ETH','SOL','EOS']:
      

      exchange_wallet = next((w for w in wallet_balances if w.type == 'exchange' and w.currency==currency), None)
      funding_wallet = next((w for w in wallet_balances if w.type == 'funding' and w.currency==currency), None)
      wallet_available[currency] = Decimal(str(funding_wallet.balance_available)) if funding_wallet else Decimal(0)
      if tokenReserves.get(currency):
        tokenReserveAmount = tokenReserves[currency]
        diff = Decimal(str(exchange_wallet.balance)) - tokenReserveAmount
        if diff > 0.001 and wallet_available[currency] < 150:
          
          await self.bfx.rest.submit_wallet_transfer('exchange','funding', currency,currency,diff)
          wallet_available[currency] = wallet_available[currency] + diff
          time.sleep(2)
        elif diff < -0.001 and wallet_available[currency] > 0:
          amount_transfer = min(abs(diff), wallet_available[currency])
          await self.bfx.rest.submit_wallet_transfer('funding' ,'exchange',currency,currency,amount_transfer)
          wallet_available[currency] = wallet_available[currency] - amount_transfer
          time.sleep(2)
    return wallet_available
  def get_token_reserves(self,limitTimes=5):
    strategies = self.storage.loadAllObjects(OrderGridStrategy)
    tokenAmount = {}
    for strategy in strategies:
      if strategy.status =='executing':
        print(f"id {strategy.id} {strategy.symbol}")
        reserve = strategy.calcReserveWithLimitTimes(limitTimes)
        for k,v in reserve.items():
          if k in tokenAmount:
            tokenAmount[k] += v
          else:
            tokenAmount[k] = v
            
    return tokenAmount
  def get_opposite_order(self, orders, order):
    for o in orders:
      if(o.strategy_id == order.strategy_id and o.id != order.id):
        return o
    return None
  def stat(self, executedTradeOrder):
    stat : TradeOrderStat = self.storage.loadObjectById(TradeOrderStat, executedTradeOrder.strategy_id)
    if not stat:
      stat = TradeOrderStat()
      stat.id = executedTradeOrder.strategy_id
      stat.symbol = executedTradeOrder.symbol
      stat.account_id = executedTradeOrder.account_id
      stat.user_id = executedTradeOrder.user_id
    stat.stat([executedTradeOrder.to_dict()])
    self.buffer_message(f"Net Grid Profit: {stat.net_profit:.2f} / {stat.apr*100:.2f}% Impermanent Loss: {stat.impermanent_loss:.2f} Net Profit: {stat.net_profit + stat.impermanent_loss:.2f} / {(stat.net_profit + stat.impermanent_loss)/stat.total_deposit*100:.2f}% ")
    self.storage.saveObject(stat)
    
  async def processOrderExecuted(self, orders, executedTradeOrder):
    if executedTradeOrder.status == 'CANCELED':
      self.storage.deleteObject(executedTradeOrder)
      return
    
    self.buffer_message(f"\nOrder {executedTradeOrder.id} {executedTradeOrder.symbol} {executedTradeOrder.amount_orig:.6f} {executedTradeOrder.price_avg:5.3f} executed!")
    if executedTradeOrder.strategy_id == 0: # not belong to any strategy
      self.storage.deleteObject(executedTradeOrder)
      history = TradeOrderHistory.from_TradeOrder(executedTradeOrder)
      self.storage.saveObject(history)
      return
        
    grid = self.get_active_grid_stragegy(executedTradeOrder.strategy_id)
    
    if not grid:
      self.buffer_message(f"Grid Stragegy {executedTradeOrder.strategy_id} is NOT found!")
      return
    
    if(grid.status != 'executing'):
      self.buffer_message(f"Grid Stragegy {grid.id} is NOT executing!")
      return
    
    self.buffer_message(f"Grid Strategy {executedTradeOrder.strategy_id} TRIGGERED! Oper Count: {executedTradeOrder.oper_count+1} ")
    
    grid.latest_base_price = executedTradeOrder.price_avg
    
    if grid.price_change_type == 'difference':
      upper_price = grid.latest_base_price + grid.every_rise_by
      lower_price = grid.latest_base_price - grid.every_fall_by
      
      if(upper_price > grid.upper_price_limit or lower_price < grid.lower_price_limit):
        self.buffer_message(f"Price limit reached, upper: {upper_price} lower: {lower_price}")
        if(grid.stop_on_failure):
          grid.status = 'stop'
          grid.oper_count = grid.oper_count + 1
          o2: TradeOrder = self.get_opposite_order(orders, executedTradeOrder) # type: ignore
          await self.cancelOrder([int(o2.id)])
          self.storage.saveObject(grid)
          history = TradeOrderHistory.from_TradeOrder(executedTradeOrder)
          self.storage.saveObject(history)
          self.storage.deleteObject(executedTradeOrder)
          self.stat(executedTradeOrder)
          self.buffer_message(f"Grid Strategy {executedTradeOrder.strategy_id} STOP!")
          return
    
      sell_quantity = grid.order_quantity_per_trade * grid.sell_quantity_perc
      buy_quantity = grid.order_quantity_per_trade * grid.buy_quantity_perc
      
      o2: TradeOrder = self.get_opposite_order(orders, executedTradeOrder) # type: ignore
      
      buy_order = None
      sell_order = None
      
      if o2 is not None and o2.amount > 0:
        buy_order = o2
      else:
        sell_order = o2
        
      if lower_price >= grid.lower_price_limit:
        if buy_order is None:
          try:
            await self.buy (grid.symbol, buy_quantity,  lower_price, grid.id, grid.oper_count)
          except Exception as e:
            self.buffer_message(f"Place Buy Order fail: {e}")
        else:
          try:
            await self.update_order(buy_order.id, buy_quantity, lower_price, grid.id, grid.oper_count)
          except Exception as e:
            logger.error(f"Update order error: {buy_order.id} {buy_quantity} {lower_price} {grid.id} {grid.oper_count}")
            self.buffer_message(f"Update Buy Order fail: {e}")
            self.buffer_message(f"Retry to cancel and submit new order")
            try:
              await self.cancelOrder([int(buy_order.id)])
              await self.buy (grid.symbol, buy_quantity,  lower_price, grid.id, grid.oper_count)
            except Exception as e:
              self.buffer_message(f"Cancel or Submit buy Order fail: {e}")
      else:
        self.buffer_message(f"lower price limit reached: {lower_price}/{grid.lower_price_limit}")
        
      if upper_price <= grid.upper_price_limit:
        if sell_order is None:
          try:
            await self.sell(grid.symbol, sell_quantity, upper_price, grid.id, grid.oper_count)
          except Exception as e:
            self.buffer_message(f"Place Sell Order fail: {e}")
        else:
          try:
            await self.update_order(int(sell_order.id), -sell_quantity, upper_price, grid.id, grid.oper_count)
          except Exception as e:
            logger.error(f"Update order error: {o2.id} {-sell_quantity} {upper_price} {grid.id} {grid.oper_count}")
            self.buffer_message(f"Update Sell Order fail: {e}")
            self.buffer_message(f"Retry to cancel and submit new order")
            try:
              await self.cancelOrder([int(sell_order.id)])
              await self.sell (grid.symbol, sell_quantity,  upper_price, grid.id, grid.oper_count)
            except Exception as e:
              self.buffer_message(f"Cancel or Submit sell Order fail: {e}")
      else:
        self.buffer_message(f"upper price limit reached: {upper_price}/{grid.upper_price_limit}")
      
      grid.oper_count = grid.oper_count + 1
      grid.status ='executing'
      self.buffer_message(f"Place New Grid Order:\n{grid.symbol} {grid.latest_base_price:5.4f} {grid.price_change_type} +{grid.every_rise_by:3.4f} -{grid.every_fall_by:3.4f} {grid.order_quantity_per_trade:.5f}")
      
      self.storage.saveObject(grid)
      history = TradeOrderHistory.from_TradeOrder(executedTradeOrder)
      self.storage.saveObject(history)
      self.storage.deleteObject(executedTradeOrder)
      self.stat(executedTradeOrder)
