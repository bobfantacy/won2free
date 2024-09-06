# trade_order.py
from model.base_model import BaseModel
from datetime import datetime
from decimal import Decimal

class TradeOrderHistory(BaseModel):
    __tablename__ = 'trade_order_history'
    __pkey__ = 'id'
    __pkeytype__ = 'N'
    
    id = None
    account_id : int = 0
    user_id : int = 0  # telegram user id
    gid = None
    cid = None
    symbol : str = ''
    mts_create = None
    mts_update = None
    amount = None
    amount_orig = None
    type = None
    type_prev = None
    flags = None
    status = None
    price : Decimal = Decimal('0')
    price_avg : Decimal = Decimal('0')
    price_trailing : Decimal = Decimal('0')
    price_aux_limit : Decimal = Decimal('0')
    notfiy = None
    place_id = None
    tag = None
    fee : Decimal = Decimal('0')
    meta = None
    strategy_id : int = 0
    oper_count : int = 0
    oper_status = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @classmethod
    def from_TradeOrder(cls, tradeOrder):
        history = TradeOrderHistory()
        for key in tradeOrder.__dict__:
            if not key.startswith('_'):
                setattr(history, key, getattr(tradeOrder, key))
        return history