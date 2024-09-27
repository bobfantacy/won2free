# account.py
from model.base_model import BaseModel
import json

class Account(BaseModel):
    __tablename__ = 'account'
    __pkey__ = 'id'
    __pkeytype__ = 'N'
    
    id: int = 0
    user_id : int = 0  # telegram user id
    account_name = None
    bfx_key = None
    bfx_secret = None
    affiliate_code = None
    create_time = None
    update_time = None
    funding_back_exchange = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


            