# account.py
from model.base_model import BaseModel
from decimal import Decimal

class LendingPlan(BaseModel):
    __tablename__ = 'lending_plan'
    __pkey__ = 'id'
    __pkeytype__ = 'N'

    id = None
    account_id : int = 0
    user_id : int = 0  # telegram user id
    symbol = None
    start_rate = None
    end_rate : Decimal = Decimal(0)
    rate_gap : Decimal = Decimal(0)
    offer_limit : Decimal = Decimal(0)
    total_amount : Decimal = Decimal(0)
    priority = None
    period = None
    min_amount : Decimal = Decimal(0)
    refresh_period : Decimal = Decimal(0)
    status = None
    last_refresh_timestamp = None
    auto_update = None
    days = None
    low_rate : Decimal = Decimal(0)
    high_rate : Decimal = Decimal(0)
    create_time = None
    update_time = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)