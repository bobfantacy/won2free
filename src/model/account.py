# account.py
from model.base_model import BaseModel
import json

class Account(BaseModel):
    __tablename__ = 'account'
    __pkey__ = 'id'
    __pkeytype__ = 'N'
    
    id = None
    account_name = None
    bfx_key = None
    bfx_secret = None
    affiliate_code = None
    create_time = None
    update_time = None
    extra : str = '{"group":[]}'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setOnChannel(self, chat_id, channelName, thread_Id):
        extra = json.loads(self.extra)
        for i in range(len(extra.get('group'))):
            if( extra['group'][i]['chat_id'] == chat_id):
                extra['group'][i]['onChannel'][channelName] = thread_Id
                self.extra = json.dumps(extra)
                return
            
    def checkChatId(self, chat_id):
        groups = json.loads(self.extra)
        for group in groups:
            if( group.get('chat_id') == chat_id):
                return True
        return False
            