from reactor.AbstractAction import AbstractAction
from datetime import datetime
from utils.global_context import *
from model.trade_order import TradeOrder
from model.trade_order_history import TradeOrderHistory
from model.order_grid_strategy import OrderGridStrategy
from decimal import Decimal
import time
import logging

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
          break
      await self.processOrderExecuted(orders, executedTradeOrder)

  def get_active_grid_stragegy(self, strategy_id):
    filter_lambda = lambda Attr: Attr('id').eq(strategy_id)
    items = self.storage.loadObjects(OrderGridStrategy, filter_lambda)
    itemsLen = len(items)
    if itemsLen != 1:
      return None
    else:
      return items[0]
  def get_opposite_order(self, orders, order):
    for o in orders:
      if(o.strategy_id == order.strategy_id and o.id != order.id):
        return o
    return None
    
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
        # if(grid.stop_on_failure):
        #   grid.status = 'stop'
        self.buffer_message(f"Price limit reached, upper: {upper_price} lower: {lower_price}")
    
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
      
      grid.oper_count = grid.oper_count + 1
      grid.status ='executing'
      self.buffer_message(f"Place New Grid Order:\n{grid.symbol} {grid.latest_base_price:5.2f} {grid.price_change_type} +{grid.every_rise_by:3.2f} -{grid.every_fall_by:3.2f} {grid.order_quantity_per_trade:.5f}")
      
      self.storage.saveObject(grid)
      history = TradeOrderHistory.from_TradeOrder(executedTradeOrder)
      self.storage.saveObject(history)
      self.storage.deleteObject(executedTradeOrder)
