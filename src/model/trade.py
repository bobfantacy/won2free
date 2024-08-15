# trade.py
from model.base_model import BaseModel
from datetime import datetime
from decimal import Decimal

class Trade(BaseModel):
    __tablename__ = 'trade'
    __pkey__ = 'id'
    __pkeytype__ = 'N'
    
    id = None
    account_id : int = 0
    user_id : int = 0  # telegram user id
    pair : str = ''
    mts_create = None
    order_id : int = 0
    amount : Decimal = Decimal('0')
    price : Decimal = Decimal('0')
    order_type : str = ''
    order_price : Decimal = Decimal('0')
    maker : int = 0
    fee : Decimal = Decimal('0')
    fee_currency : str = ''
    date = None
    direction : str = ''
    cid : int = 0
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.date = self.mts_create
        if self.amount > 0 :
          self.direction = 'LONG'
        else:
          self.direction = 'SHORT'
    
    @classmethod
    def from_bfx_trade(cls, t):
        return Trade(
        id = t.id,
        pair = t.pair,
        mts_create = datetime.fromtimestamp(t.mts_create / 1000).isoformat(),
        order_id = t.order_id,
        amount = Decimal(str(t.amount)),
        price = Decimal(str(t.price)),
        order_type = t.order_type,
        order_price = Decimal(str(t.order_price)),
        maker = t.maker,
        fee = Decimal(str(t.fee)),
        fee_currency = t.fee_currency,
        date = t.date,
        direction= t.direction
      )