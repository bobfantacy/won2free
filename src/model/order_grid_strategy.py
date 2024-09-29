# account.py
from model.base_model import BaseModel
from decimal import Decimal, ROUND_FLOOR
import math

class OrderGridStrategy(BaseModel):
  __tablename__ = 'order_grid_strategy'
  __pkey__ = 'id'
  __pkeytype__ = 'N'
  
  id : None
  account_id : int = 0
  user_id : int = 0  # telegram user id
  symbol : str = ''
  initial_base_price : Decimal = Decimal(0)
  latest_base_price : Decimal = Decimal(0)
  price_change_type : None
  every_rise_by : None
  every_fall_by : None
  fall_after_rise_by : Decimal = Decimal(0)
  rise_after_fall_by : Decimal = Decimal(0)
  lower_price_limit : Decimal = Decimal(0)
  upper_price_limit : Decimal = Decimal(0)
  expiry_date : None
  order_quantity_per_trade : Decimal = Decimal(0)
  buy_quantity_perc : Decimal = Decimal(0)
  sell_quantity_perc : Decimal = Decimal(0)
  min_position : Decimal = Decimal(0)
  max_position : Decimal = Decimal(0)
  stop_on_failure : None
  status : None
  oper_count : Decimal = Decimal(0)
  created_at : None
  updated_at : None
  comments : None
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
  
  def calcReserve(self):
    buy_quantity  = self.order_quantity_per_trade * self.buy_quantity_perc
    sell_quantity = self.order_quantity_per_trade * self.sell_quantity_perc
    sell_times = ((self.upper_price_limit - self.latest_base_price) / self.every_rise_by).quantize(Decimal('1'), rounding=ROUND_FLOOR)
    reservedA = sell_quantity * sell_times
    buy_times = ((self.latest_base_price - self.lower_price_limit) / self.every_fall_by).quantize(Decimal('1'), rounding=ROUND_FLOOR)
    lowest_price = self.latest_base_price - self.every_fall_by * buy_times
    reservedB = (self.latest_base_price + lowest_price) * buy_quantity* buy_times / 2
    return (reservedA, reservedB)
  
  def calcReserveWithLimitTimes(self, limitTimes: Decimal= Decimal(10)):
    buy_quantity  = self.order_quantity_per_trade * self.buy_quantity_perc
    sell_quantity = self.order_quantity_per_trade * self.sell_quantity_perc
    sell_times = ((self.upper_price_limit - self.latest_base_price) / self.every_rise_by).quantize(Decimal('1'), rounding=ROUND_FLOOR)
    sell_times = min(sell_times, limitTimes)
    reservedA = sell_quantity * sell_times
    buy_times = ((self.latest_base_price - self.lower_price_limit) / self.every_fall_by).quantize(Decimal('1'), rounding=ROUND_FLOOR)
    buy_times = min(buy_times, limitTimes)
    lowest_price = self.latest_base_price - self.every_fall_by * buy_times
    reservedB = (self.latest_base_price -self.every_fall_by + lowest_price) * buy_quantity* buy_times / 2
    return {self.symbol[1:4]:reservedA, self.symbol[4:]:reservedB}
    