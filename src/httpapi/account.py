from model.account import Account
from utils.storage import Storage, key_generate
from utils.api_gateway import *
from datetime import datetime
import logging
import time
import random


logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

storage = Storage()

def get_accounts(event, context):
    # logger.info('Event: {}'.format(event))
    user_id = get_user_id(event)
    
    filter_lambda = lambda Attr: Attr('user_id').eq(user_id)

    accounts = storage.loadObjects(Account, filter_lambda)
    sanitized_accounts = [sanitize_account(account).to_dict() for account in accounts]
    logger.info(f"accounts: {sanitized_accounts}")
    return create_200_response(sanitized_accounts)

def save_account(event, context):
    logger.info('Event: {}'.format(event))
    user_id : int= get_user_id(event)
    
    post_data = json.loads(event['body'])
    logger.info('Post Data: {}'.format(post_data))
    
    account_data = post_data.get('account')
    try: 
        if account_data:
            account = Account(**account_data)
            if account.account_name is None:
                return create_400_response({'message': 'Invalid account name'})
            if account.bfx_key is None or account.bfx_secret is None:
                return create_400_response({'message': 'Invalid bfx_key or bfx_secret'})
            
            account_id = account_data.get('id')
            if account_id is None or account_id.strip() == "":
                
                filter_lambda = lambda Attr: Attr('account_name').eq(account.account_name)
                accounts = storage.loadObjects(Account, filter_lambda)
                if accounts:
                    return create_400_response({'message': 'account name already existed!'})
                
                account.id = key_generate()    
                account.user_id = user_id
                account.create_time = datetime.now().isoformat()
                account.update_time = datetime.now().isoformat()
                account.affiliate_code = 'mBkll4Et-'
                storage.saveObject(account)
                return create_200_response({'message': 'Account saved successfully', 'id': account.id})
            else:
                oldAccount = storage.loadObjectById(Account, int(account_data['id']))
                if oldAccount.user_id != user_id:
                    return create_400_response({'message': 'Invalid account data'})
                if('***' in account.bfx_key):
                    account.bfx_key =  oldAccount.bfx_key
                    account.bfx_secret = oldAccount.bfx_secret
                account.account_name = oldAccount.account_name
                account.id = int(account.id)
                account.update_time = datetime.now().isoformat()
                account.user_id = user_id
                storage.saveObject(account)
                return create_200_response({'message': 'Account saved successfully', 'id': account.id})
        else:
            return create_400_response({'message': 'Invalid account data'})
    except Exception as e:
        return create_400_response({'message': f'Exception: {e}'})

def del_account(event, context):
    logger.info('Event: {}'.format(event))
    user_id : int= get_user_id(event)
    
    post_data = json.loads(event['body'])
    logger.info('Post Data: {}'.format(post_data))
    account_data = post_data.get('account')
    try:
        if account_data:
            account = Account(**account_data)
            if account_data.get('id') is None:
                return create_400_response({'message': 'Invalid account data'})
            oldAccount = storage.loadObjectById(Account, int(account_data['id']))
            if oldAccount.user_id != user_id:
                return create_400_response({'message': 'Invalid account data'})
            
            storage.deleteObjectById(Account, int(account_data['id']))
            
            return create_200_response({'message': 'Account deleted successfully', 'id': account.id})
            
        else:
            return create_400_response({'message': 'Invalid account data'})
    except Exception as e:
        return create_400_response({'message': f'Exception: {e}'})
    
def sanitize_account(account): 
    account.bfx_key = account.bfx_key[:6] + '***' + account.bfx_key[-4:]
    account.bfx_secret = account.bfx_secret[:6] + '***' + account.bfx_secret[-4:]
    account.affiliate_code = None

    return account