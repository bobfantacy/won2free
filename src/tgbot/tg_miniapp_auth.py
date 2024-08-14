import hmac
import os
import jwt
import time
import json
import logging
from urllib.parse import parse_qs

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'OPTIONS,POST'
    }

BOT_TOKEN : str = os.getenv('TG_TOKEN','')
JWT_ALGORITHM = 'HS256'
JWT_SECRET = os.getenv('JWT_SECRET','SHOULD_USE_YOUR_SECRET')

def validate_web_app(initdata: str) -> tuple[bool, dict | None]:
    url_params = parse_qs(initdata)
    
    auth_date = int(url_params.get('auth_date', [0])[0])
    
    if int(time.time()) - auth_date > 86400:
        return (False, {})
    
    hash_value : str = url_params.pop('hash', [''])[0]
    sorted_params = sorted(url_params.items())

    data_check_string = '\n'.join(f'{key}={value[0]}' for key, value in sorted_params)
    secret = hmac.new('WebAppData'.encode(), BOT_TOKEN.encode(), 'sha256').digest()
    calculated_hash = hmac.new(secret, data_check_string.encode(), 'sha256').hexdigest()
    if hmac.compare_digest(hash_value, calculated_hash):
        user = url_params.get('user', [None])[0]
        user_obj = json.loads(user) if user else None
        return (True, user_obj)
    else:
        return (False, {})

def auth(event, context):
    logger.info('Event: {}'.format(event))

    if event.get('httpMethod') == 'POST' and event.get('body'): 
        data = event.get('body')
        try:
            initData = json.loads(data)['initData']
            (res , user) = validate_web_app(initData)
            if res and user is not None:
                token = jwt.encode({
                    'id': user['id'],
                    'first_name': user['first_name'],
                    'username': user['username'],
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
        except Exception as e:
            logger.error('Exception: {}'.format(e))
            response = {
                    'statusCode': 401,
                    'headers': headers,
                    'body': json.dumps({'status': 'error', 'message': 'Invalid login attempt.'})
                }
            return response  