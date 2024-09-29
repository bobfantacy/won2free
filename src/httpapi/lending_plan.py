from model.account import Account
from model.lending_plan import LendingPlan
from utils.storage import Storage, key_generate
from utils.api_gateway import *
from utils.global_context import GlobalContext
from datetime import datetime
import logging
import time
import random
from decimal import Decimal

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

globalContext = GlobalContext()
storage = Storage()

def get_lending_plans(event, context):
    # {"account_id": 123456 } 
    # logger.info('Event: {}'.format(event))
    
    try:
        user_id = get_user_id(event)
        post_data = json.loads(event['body'])
        logger.info('Post Data: {}'.format(post_data))
        account_id = int(post_data.get('account_id'))
      
        filter_lambda = lambda Attr: Attr('user_id').eq(user_id) and Attr('account_id').eq(int(account_id))

        lendingPlans = storage.loadObjects(LendingPlan, filter_lambda)
        lendingPlans = [lendingPlan.to_dict() for lendingPlan in lendingPlans]
        return create_200_response(lendingPlans)
    except:
        return create_400_response({'message': 'Invalid account_id'})

def save_lending_plan(event, context):
    logger.info('Event: {}'.format(event))
    user_id : int = get_user_id(event)
    
    lendingPlan_data = json.loads(event['body'])
    logger.info('Post Data: {}'.format(lendingPlan_data))
    
    timestamp = datetime.now().isoformat()
    try: 
      if lendingPlan_data:
        lendingPlan = LendingPlan(**lendingPlan_data)
        validateLendingPlan(lendingPlan)
        
        lendingPlan_id = lendingPlan_data.get('id')
        if lendingPlan_id is None or lendingPlan_id.strip() == "":
          
          if globalContext.checkUserIdVsAccountId(user_id, lendingPlan.account_id):
              return create_400_response({'message': 'Not Authorized!'})
          
          lendingPlan.id = key_generate()
          lendingPlan.account_id = int(lendingPlan.account_id)
          lendingPlan.user_id = user_id
          lendingPlan.last_refresh_timestamp = timestamp
          lendingPlan.create_time = timestamp
          lendingPlan.update_time = timestamp
          storage.saveObject(lendingPlan)
          return create_200_response({'message': 'LendingPlan saved successfully', 'id': lendingPlan.id})
        else:
          oldLendingPlan = storage.loadObjectById(LendingPlan, int(lendingPlan_data['id']))
          if not oldLendingPlan:
              return create_400_response({'message': 'LendingPlan NOT existed!'})
          if oldLendingPlan.user_id != user_id:
              return create_400_response({'message': 'Invalid LendingPlan data'})
          
          lendingPlan.account_id = oldLendingPlan.account_id
          lendingPlan.id = int(lendingPlan.id)
          lendingPlan.update_time = timestamp
          lendingPlan.user_id = user_id
          storage.saveObject(lendingPlan)
          return create_200_response({'message': 'LendingPlan saved successfully', 'id': lendingPlan.id})
      else:
          return create_400_response({'message': 'Invalid LendingPlan data'})
    except Exception as e:
        return create_400_response({'message': f'Exception: {e}'})
      
def del_lending_plan(event, context):
    logger.info('Event: {}'.format(event))
    user_id : int= get_user_id(event)
    
    post_data = json.loads(event['body'])
    logger.info('Post Data: {}'.format(post_data))
    
    try:
        account_id = int(post_data.get('account_id'))
        lendingPlan_id = int(post_data.get('id'))

        oldLendingPlan = storage.loadObjectById(LendingPlan, lendingPlan_id)
        
        if not (oldLendingPlan.user_id == user_id and int(oldLendingPlan.account_id) == account_id):
            return create_400_response({'message': 'Invalid LendingPlan data'})
        
        storage.deleteObjectById(LendingPlan, lendingPlan_id)
        
        return create_200_response({'message': 'LendingPlan deleted successfully', 'id': lendingPlan_id})
    except Exception as e:
        return create_400_response({'message': f'Exception: {e}'})
      
def validateLendingPlan(lendingPlan):
  if lendingPlan.account_id is None:
    raise Exception("Invalid account_id")
  if lendingPlan.symbol is None or len(lendingPlan.symbol.strip())==0 or lendingPlan.symbol[0:1] !='f':
    raise Exception("Invalid symbol")
  lendingPlan.symbol = lendingPlan.symbol.strip()
  
  if lendingPlan.status not in ['ACTIVE', 'INACTIVE']:
    raise Exception("Invalid status")
  
  try:
    lendingPlan.period = int(lendingPlan.period)
    if lendingPlan.period < 2 or lendingPlan.period > 120:
      raise Exception("Invalid period")
  except:
    raise Exception("Invalid period")

  try:
    lendingPlan.min_amount = Decimal(lendingPlan.min_amount)
    if lendingPlan.min_amount < 0:
      raise Exception("Invalid min_amount")
  except:
    raise Exception("Invalid min_amount")
  
  try:
    lendingPlan.offer_limit = int(lendingPlan.offer_limit)
    if lendingPlan.offer_limit < 0 or lendingPlan.offer_limit > 100:
      raise Exception("Invalid offer_limit")
  except:
    raise Exception("Invalid offer_limit")
  
  try:
    lendingPlan.total_amount = Decimal(lendingPlan.total_amount)
    if lendingPlan.total_amount < 0:
      raise Exception("Invalid total_amount")
  except:
    raise Exception("Invalid total_amount")
  
  try:
    lendingPlan.priority = int(lendingPlan.priority)
  except:
    raise Exception("Invalid priority")
  try:
    lendingPlan.auto_update = int(lendingPlan.auto_update)
    if lendingPlan.auto_update not in (0,1):
      raise Exception("Invalid auto_update")
  except:
    raise Exception("Invalid auto_update")
  
  if lendingPlan.auto_update == True:
    try:
      lendingPlan.days = int(lendingPlan.days)
    except:
      raise Exception("Invalid days")
    
    try:
      lendingPlan.low_rate = Decimal(lendingPlan.low_rate) 
      if lendingPlan.low_rate < 0:
        raise Exception("Invalid low_rate")
    except:
      raise Exception("Invalid low_rate")
    
    try:
      lendingPlan.high_rate = Decimal(lendingPlan.high_rate)
      if lendingPlan.high_rate < 0:
        raise Exception("Invalid high_rate")
    except:
      raise Exception("Invalid high_rate")
  else:
    try:
      lendingPlan.start_rate = Decimal(lendingPlan.start_rate)
      if lendingPlan.start_rate < 0:
        raise Exception("Invalid start_rate")
    except:
      raise Exception("Invalid start_rate")
    
    try:
      lendingPlan.rate_gap = Decimal(lendingPlan.rate_gap)
      if lendingPlan.rate_gap < 0:
        raise Exception("Invalid rate_gap")
    except:
      raise Exception("Invalid rate_gap")
    
    try:
      lendingPlan.end_rate = Decimal(lendingPlan.end_rate)
      if lendingPlan.end_rate < 0:
        raise Exception("Invalid end_rate")
    except:
      raise Exception("Invalid end_rate")