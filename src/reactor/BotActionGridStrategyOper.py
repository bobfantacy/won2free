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

class BotActionGridStrategyOper(AbstractAction):
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
    if executedTradeOrder.strategy_id == 0: # not belong to any strategy
      self.buffer_message(f"Order {executedTradeOrder.id} {executedTradeOrder.symbol} {executedTradeOrder.amount_orig:.6f} {executedTradeOrder.price_avg:5.0f} executed!")  
      self.storage.deleteObject(executedTradeOrder)
      history = TradeOrderHistory.from_TradeOrder(executedTradeOrder)
      self.storage.saveObject(history)
      return
    self.buffer_message(f"Order {executedTradeOrder.id} {executedTradeOrder.symbol} {executedTradeOrder.amount_orig:.6f} {executedTradeOrder.price_avg:5.0f} executed!")
    self.buffer_message(f"Grid Strategy {executedTradeOrder.strategy_id} TRIGGERED! Oper Count: {executedTradeOrder.oper_count+1} ")
    
    grid = self.get_active_grid_stragegy(executedTradeOrder.strategy_id)
    
    if not grid:
      self.buffer_message(f"Grid Stragegy {executedTradeOrder.strategy_id} is NOT found!")
      return
    
    if(grid.status != 'executing'):
      self.buffer_message(f"Grid Stragegy {grid.id} is NOT executing!")
      return
    
    grid.latest_base_price = executedTradeOrder.price_avg
    
    if grid.price_change_type == 'difference':
      upper_price = grid.latest_base_price + grid.every_rise_by
      lower_price = grid.latest_base_price - grid.every_fall_by
      
      if(upper_price > grid.upper_price_limit or lower_price < grid.lower_price_limit):
        if(grid.stop_on_failure):
          grid.status = 'stop'
        self.buffer_message(f"Price limit reached, upper: {upper_price} lower: {lower_price}")
        return
    
      sell_quantity = grid.order_quantity_per_trade * grid.sell_quantity_perc
      buy_quantity = grid.order_quantity_per_trade * grid.buy_quantity_perc
      
      o2 = self.get_opposite_order(orders, executedTradeOrder)
      
      if(o2 is None):

        try:
          await self.sell(grid.symbol, sell_quantity, upper_price, grid.id, grid.oper_count)
        except Exception as e:
          logger.error(f"Place Sell order error: {grid.symbol} {sell_quantity} {upper_price} {grid.id} {grid.oper_count}")
          self.buffer_message(f"Place Sell Order fail: {e}")
          self.buffer_message(f"Keep Buy Order and wait for next chance")
        try:
          await self.buy (grid.symbol, buy_quantity,  lower_price, grid.id, grid.oper_count)
        except Exception as e:
          logger.error(f"Place Buy order error: {grid.symbol} {buy_quantity} {lower_price} {grid.id} {grid.oper_count}")
          self.buffer_message(f"Place Buy Order fail: {e}")
          self.buffer_message(f"Keep Sell Order and wait for next chance")
      else:
        if o2.amount > 0: #Update Buy Order
          try:
            await self.update_order(int(o2.id), buy_quantity, lower_price, grid.id, grid.oper_count)
          except Exception as e:
            logger.error(f"Update order error: {o2.id} {buy_quantity} {lower_price} {grid.id} {grid.oper_count}")
            self.buffer_message(f"Place Sell Order fail: {e}")
            self.buffer_message(f"Retry to cancel and submit new order")
            await self.cancelOrder([int(o2.id)])
            await self.buy (grid.symbol, buy_quantity,  lower_price, grid.id, grid.oper_count)
          try:
            await self.sell(grid.symbol, sell_quantity, upper_price, grid.id, grid.oper_count)
          except Exception as e:
            logger.error(f"Place Sell order error: {grid.symbol} {sell_quantity} {upper_price} {grid.id} {grid.oper_count}")
            self.buffer_message(f"Place Buy Order fail: {e}")
            self.buffer_message(f"Keep Buy Order and wait for next chance")
        else: #Update Sell Order
          try:
            await self.update_order(int(o2.id), -sell_quantity, upper_price, grid.id, grid.oper_count)
          except Exception as e:
            logger.error(f"Update order error: {o2.id} {-sell_quantity} {upper_price} {grid.id} {grid.oper_count}")
            self.buffer_message(f"Place Sell Order fail: {e}")
            self.buffer_message(f"Retry to cancel and submit new order")
            await self.cancelOrder([int(o2.id)])
            await self.sell (grid.symbol, sell_quantity,  upper_price, grid.id, grid.oper_count)
          try:
            await self.buy (grid.symbol, buy_quantity,  lower_price, grid.id, grid.oper_count)
          except Exception as e:
            logger.error(f"Place Buy order error: {grid.symbol} {buy_quantity} {lower_price} {grid.id} {grid.oper_count}")
            self.buffer_message(f"Place Buy Order fail: {e}")
            self.buffer_message(f"Keep Buy Order and wait for next chance")

      grid.oper_count = grid.oper_count + 1
      grid.status ='executing'
      self.buffer_message(f"Place New Grid Order:\n{grid.symbol} {grid.latest_base_price:5.0f} {grid.price_change_type} +{grid.every_rise_by:3.0f} -{grid.every_fall_by:3.0f} {grid.order_quantity_per_trade:.5f}")
      
      self.storage.saveObject(grid)
      self.storage.deleteObject(executedTradeOrder)
      history = TradeOrderHistory.from_TradeOrder(executedTradeOrder)
      self.storage.saveObject(history)