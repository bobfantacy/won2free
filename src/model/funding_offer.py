# funding_offer.py
from model.base_model import BaseModel
from datetime import datetime
from decimal import Decimal

class FundingOffer(BaseModel):
    __tablename__ = 'funding_offer'
    __pkey__ = 'id'
    __pkeytype__ = 'N'
    
    id = None
    account_id = None
    lp_id = None
    symbol = None
    mts_created = None
    mts_updated = None
    amount : Decimal = Decimal(0)
    amount_orig : Decimal = Decimal(0)
    type = None
    flags = None
    status = None
    rate : Decimal = Decimal(0)
    period : Decimal = Decimal(0)
    notify = None
    hidden = None
    renew = None
    
    def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
    
    @classmethod
    def from_bfx_offer(cls, o):
      return FundingOffer(
        id = o.id,
        symbol = o.symbol,
        mts_created = datetime.fromtimestamp(o.mts_created / 1000).isoformat(),
        mts_updated = datetime.fromtimestamp(o.mts_updated / 1000).isoformat(),
        amount = Decimal(o.amount),
        amount_orig = Decimal(str(o.amount_orig)),
        type = 'LIMIT',
        flags = 0,
        status = o.status,
        rate = Decimal(str(o.rate)),
        period = o.period,
        notify = o.notify,
        hidden = o.hidden,
        renew = 0
      )