# account.py
from model.base_model import BaseModel

class OrderGridStrategy(BaseModel):
  __tablename__ = 'order_grid_strategy'
  __pkey__ = 'id'
  __pkeytype__ = 'N'
  
  id : None
  account_id : None
  symbol : None
  initial_base_price : None
  latest_base_price : None
  price_change_type : None
  every_rise_by : None
  every_fall_by : None
  fall_after_rise_by : None
  rise_after_fall_by : None
  lower_price_limit : None
  upper_price_limit : None
  expiry_date : None
  order_quantity_per_trade : None
  buy_quantity_perc : None
  sell_quantity_perc : None
  min_position : None
  max_position : None
  stop_on_failure : None
  status : None
  oper_count : None
  created_at : None
  updated_at : None
  comments : None
  
  def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
    
    
    