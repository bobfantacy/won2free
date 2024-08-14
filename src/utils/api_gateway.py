import json
from decimal import Decimal

DEFAULT_HEADERS = {
    'Content-Type': 'application/json',
    # Required for CORS support to work
    'Access-Control-Allow-Origin': '*',
    # Required for cookies, authorization headers with HTTPS
    'Access-Control-Allow-Credentials': True,
}

def create_200_response(message):
    return create_aws_lambda_response(200, {'data': message}, DEFAULT_HEADERS)

def create_400_response(message):
    return create_aws_lambda_response(400, {'data': message}, DEFAULT_HEADERS)

def create_aws_lambda_response(status_code, message, headers=None):
    if headers is None:
        headers = DEFAULT_HEADERS
    return {
        'statusCode': status_code,
        'headers': headers,
        'body': json.dumps(message, cls=CustomJSONEncoder)
    }
    
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

def get_user_id(event):
  return int(event['requestContext']['authorizer']['principalId'])