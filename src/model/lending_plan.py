# account.py
from model.base_model import BaseModel
from decimal import Decimal

class LendingPlan(BaseModel):
    __tablename__ = 'lending_plan'
    __pkey__ = 'id'
    __pkeytype__ = 'N'

    def __init__(self, *args, **kwargs):
        self.version = 1
        self.id = None
        self.account_id : int = 0
        self.user_id : int = 0  # telegram user id
        self.symbol = None
        self.start_rate : Decimal = Decimal(0)
        self.end_rate : Decimal = Decimal(0)
        self.rate_gap : Decimal = Decimal(0)
        self.rate_limit_low : Decimal = Decimal('0.027')
        self.rate_limit_high : Decimal = Decimal('0.07')
        self.rate_limit_enabled: bool = True
        self.offer_limit : Decimal = Decimal(0)
        self.total_amount : Decimal = Decimal(0)
        self.priority = None
        self.period = None
        self.min_amount : Decimal = Decimal(0)
        self.refresh_period : Decimal = Decimal(0)
        self.status = None
        self.last_refresh_timestamp = None
        self.auto_update = None
        self.days = None
        self.low_rate : Decimal = Decimal(0)
        self.high_rate : Decimal = Decimal(0)
        self.create_time = None
        self.update_time = None
        super().__init__(*args, **kwargs)
        self.rate_limit_high = Decimal(str(self.rate_limit_high))
        self.rate_limit_low = Decimal(str(self.rate_limit_low))

    def modelVersionChange(self):
        attrs = []
        fromVersion = self.version
        if fromVersion == 0:
            attrs.append(('add', 'rate_limit_low',  Decimal('0.027')))
            attrs.append(('add', 'rate_limit_high', Decimal('0.07')))
            attrs.append(('add', 'rate_limit_enabled', True))
            attrs.append(('add', 'version', 0))
        return attrs