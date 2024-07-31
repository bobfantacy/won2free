from model.base_model import BaseModel
from datetime import datetime
from decimal import Decimal

class SyncTick(BaseModel):
    '''
    This model records the timestamp of bfx sync orders. Like trade, funding offer, funding loan, funding credit and so on 
    '''
    __tablename__ = 'sync_tick'
    __pkey__ = 'account_id'
    __pkeytype__ = 'N'
    
    account_id : int = 0
    trade_last_sync : int = 0 # the last sync timestamp
    order_history_last_sync : int = 0
    loan_last_sync: int = 0
    credit_last_sync: int = 0
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    