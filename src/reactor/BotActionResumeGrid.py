from reactor.AbstractAction import AbstractAction
from bfxapi.models.order import OrderType
from model.order_grid_strategy import OrderGridStrategy
import math
from decimal import Decimal
from model.trade_order import TradeOrder
from datetime import datetime

class BotActionResumeGrid(AbstractAction):
  def __init__(self):
    super().__init__(commands=['ResumeGrid'])

  async def _execute(self, event_body):
    command = event_body['command']
    data = event_body['data']
    
    if type(data)==dict:
      self.buffer_message("json args NOT supported")
      return
    
    if(len(data) < 1):
      self.buffer_message("Invalid command, please use: ResumeGrid <account_name> <grid_id>")
      return
    
    grid = self.storage.loadObjectById(OrderGridStrategy, int(data[0]))
    
    if not grid:
      self.buffer_message(f"Strategy {data[0]} NOT Exist!")
      return
    
    if grid.account_id != self.account.id:
      self.buffer_message(f"You are NOT authorized!")
      return

    if(grid.status != 'executing'):
      self.buffer_message(f"Strategy {grid.id} is NOT executing!")
      return
    
    await self.resume_grid(grid)
    
  async def resume_grid(self, grid: OrderGridStrategy ):
    if (grid.price_change_type == 'difference'):
      filter_lambda = lambda Attr: Attr('strategy_id').eq(grid.id)
      orders = self.storage.loadObjects(TradeOrder, filter_lambda)
      if orders:
        orderIds = [int(o.id) for o in orders]
        executedBfxOrders = await self.get_bfx_order_history(ids = orderIds)
        executedTradeOrders = [TradeOrder.from_bfx_order(o) for o in executedBfxOrders]
        for executedTradeOrder in  executedTradeOrders:
          if executedTradeOrder.status == 'CANCELED':
            self.storage.deleteObject(executedTradeOrder)
          else:
            grid.latest_base_price = executedTradeOrder.price_avg
            history = TradeOrderHistory.from_TradeOrder(executedTradeOrder)
            self.storage.saveObject(history)
            self.storage.deleteObject(executedTradeOrder)
          orders = [o for o in orders if o.id != executedTradeOrder.id]

      upper_price = grid.latest_base_price + grid.every_rise_by
      lower_price = grid.latest_base_price - grid.every_fall_by
      
      ## todo checkout the position limit
      sell_quantity = grid.order_quantity_per_trade * grid.sell_quantity_perc
      buy_quantity = grid.order_quantity_per_trade * grid.buy_quantity_perc
      
      buy_order = None
      sell_order = None
      for o in orders:
        if o.amount > 0:
          buy_order = o
        else:
          sell_order = o
      
      if(lower_price < grid.lower_price_limit):
        self.buffer_message(f"Grid {grid.id} lower price limit reached: {lower_price}/{grid.lower_price_limit}")
      else:
        if buy_order is None:
          try:
            await self.buy (grid.symbol, buy_quantity,  lower_price, grid.id, grid.oper_count)
          except Exception as e:
            self.buffer_message(f"Place Buy Order fail: {e}")
        else:
          try:
            await self.update_order(buy_order.id, buy_quantity, lower_price, grid.id, grid.oper_count)
          except Exception as e:
            self.buffer_message(f"Update Buy Order fail: {e}")
            
      if(upper_price > grid.upper_price_limit):
        self.buffer_message(f"Grid {grid.id} upper price limit reached: {upper_price}/{grid.upper_price_limit}  lower: {lower_price}/{grid.lower_price_limit}")
      else:
        if sell_order is None:
          try:
            await self.sell(grid.symbol, sell_quantity, upper_price, grid.id, grid.oper_count)
          except Exception as e:
            self.buffer_message(f"Place Sell Order fail: {e}")
        else:
          try:
            await self.update_order(int(sell_order.id), -sell_quantity, upper_price, grid.id, grid.oper_count)
          except Exception as e:
            self.buffer_message(f"Update Sell Order fail: {e}")
      
      if(grid.stop_on_failure and (lower_price < grid.lower_price_limit or upper_price > grid.upper_price_limit)):
        grid.status = 'stop'
      else:
        grid.status ='executing'
      grid.oper_count += 1
      grid.updated_at = datetime.now().isoformat()
      self.storage.saveObject(grid)
      self.buffer_message(f"Rusume Grid Strategy {grid.id}: {grid.symbol} {grid.latest_base_price:5.4f} {grid.price_change_type} {+grid.every_rise_by:4.4f} {-grid.every_fall_by:4.4f} {grid.order_quantity_per_trade:.5f}")

      