from reactor.AbstractAction import AbstractAction
from bfxapi.models.order import OrderType
from model.order_grid_strategy import OrderGridStrategy
import math
from decimal import Decimal
from model.trade_order import TradeOrder

class BotActionResumeGrid(AbstractAction):
  def __init__(self):
    super().__init__(commands=['ResumeGrid'])

  async def _execute(self, event_body):
    command = event_body['command']
    data = event_body['data']
    if(len(data) < 2):
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
    
    if grid.price_change_type == 'difference':
      upper_price = grid.latest_base_price + grid.every_rise_by
      lower_price = grid.latest_base_price - grid.every_fall_by
      
      if(upper_price > grid.upper_price_limit or lower_price < grid.lower_price_limit):
        if(grid.stop_on_failure):
          grid.status = 'stop'
        self.buffer_message(f"Price limit reached, upper: {upper_price} lower: {lower_price}")
        return
      
      ## todo checkout the position limit
      sell_quantity = grid.order_quantity_per_trade * grid.sell_quantity_perc
      buy_quantity = grid.order_quantity_per_trade * grid.buy_quantity_perc
      
      buy_order = session.query(TradeOrder).filter(TradeOrder.strategy_id ==grid.id,
                                            TradeOrder.status == 'ACTIVE',
                                            TradeOrder.amount>0).first()
      
      sell_order = session.query(TradeOrder).filter(TradeOrder.strategy_id ==grid.id,
                                            TradeOrder.status == 'ACTIVE',
                                            TradeOrder.amount<0).first()
      
      oper_count = grid.oper_count if buy_order is None and sell_order is None else grid.oper_count-1
      
      if buy_order is None:
        try:
          await self.buy (grid.symbol, buy_quantity,  lower_price, grid.id, oper_count)
        except Exception as e:
          self.buffer_message(f"Place Buy Order fail: {e}")
      else:
        try:
          await self.update_order(buy_order.id, buy_quantity, lower_price, grid.id, oper_count)
        except Exception as e:
          self.buffer_message(f"Update Buy Order fail: {e}")
      
      if sell_order is None:
        try:
          await self.sell(grid.symbol, sell_quantity, upper_price, grid.id, oper_count)
        except Exception as e:
          self.buffer_message(f"Place Sell Order fail: {e}")
      else:
        try:
          await self.update_order(sell_order.id, -sell_quantity, upper_price, grid.id, oper_count)
        except Exception as e:
          self.buffer_message(f"Update Sell Order fail: {e}")
      
      grid.oper_count = oper_count + 1
      grid.status ='executing'
      self.buffer_message(f"Rusume Grid Strategy {grid.id}: {grid.symbol} {grid.latest_base_price:5.0f} {grid.price_change_type} {+grid.every_rise_by:4.0f} {-grid.every_fall_by:4.0f} {grid.order_quantity_per_trade:.5f}")