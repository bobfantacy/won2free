import hashlib
import hmac
import jwt
import time
import os
import json
import logging


# Logging is cool!
logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

BOT_TOKEN : str = os.getenv("TG_TOKEN")
SECRET_KEY = hashlib.sha256(BOT_TOKEN.encode()).digest()

JWT_ALGORITHM = 'HS256'
JWT_SECRET = os.getenv('JWT_SECRET','SHOULD_USE_YOUR_SECRET')

headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'OPTIONS,POST'
    }

def verify_telegram_auth(data):
    auth_date = int(data['auth_date'])
    
    if int(time.time()) - auth_date > 864000:
        return False

    check_string = '\n'.join(
        f"{key}={data[key]}"
        for key in sorted(data.keys())
        if key != 'hash'
    )

    hmac_obj = hmac.new(SECRET_KEY, check_string.encode(), hashlib.sha256)
    generated_hash = hmac_obj.hexdigest()

    return generated_hash == data['hash']

def auth(event, context):
    logger.info('Event: {}'.format(event))

    if event.get('httpMethod') == 'POST' and event.get('body'): 
      data = json.loads(event.get('body'))
      if verify_telegram_auth(data):
        token = jwt.encode({
            'id': data['id'],
            'first_name': data['first_name'],
            'username': data['username'],
            'exp': time.time() + 3600*24*14  # expired in 2 weeks
        }, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        response = {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'status': 'success', 'message': 'User verified successfully.', 'token': token})
            }
        return response
      else:
        response = {
                'statusCode': 401,
                'headers': headers,
                'body': json.dumps({'status': 'error', 'message': 'Invalid login attempt.'})
            }
        return response