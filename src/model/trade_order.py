# trade_order.py
from model.base_model import BaseModel
from datetime import datetime
from decimal import Decimal

class TradeOrder(BaseModel):
    __tablename__ = 'trade_order'
    __pkey__ = 'id'
    __pkeytype__ = 'N'
    
    id : int = 0
    account_id : int = 0
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
    def from_bfx_order(cls, o):
        return TradeOrder(
            id = o.id,
            gid=o.gid,
            cid=o.cid,
            symbol=o.symbol,
            mts_create=datetime.fromtimestamp(o.mts_create / 1000).isoformat(),
            mts_update=datetime.fromtimestamp(o.mts_update / 1000).isoformat(),
            amount=Decimal(str(o.amount)),
            amount_orig=Decimal(str(o.amount_orig)),
            type=o.type,
            type_prev=o.type_prev,
            flags=o.flags,
            status=o.status,
            price=Decimal(str(o.price)),
            price_avg=Decimal(str(o.price_avg)),
            price_trailing=Decimal(str(o.price_trailing)),
            price_aux_limit=Decimal(str(o.price_aux_limit)),
            notfiy=o.notfiy,
            place_id=o.place_id,
            tag=o.tag,
            fee=Decimal(str(o.fee)),
            meta=o.meta,
            strategy_id=None,
            oper_count=None,
            oper_status='active' if o.status == 'ACTIVE' else 'executed'
        )