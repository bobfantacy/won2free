import json
import os
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import logging

logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

JWT_ALGORITHM = 'HS256'
JWT_SECRET = os.getenv('JWT_SECRET','SHOULD_USE_YOUR_SECRET')

def auth(event, context):
    logger.info(f"Event: {event}")
    whole_auth_token = event.get('authorizationToken')
    if not whole_auth_token:
        raise Exception('Unauthorized')

    token_parts = whole_auth_token.split(' ')
    auth_token = token_parts[1]
    token_method = token_parts[0]

    if not (token_method.lower() == 'bearer' and auth_token):
        logger.warn("Failing due to invalid token_method or missing auth_token")
        raise Exception('Unauthorized')
    try:
        principal = verify_token(auth_token, JWT_SECRET, JWT_ALGORITHM)
        logger.info(f"principal: {principal}")
        policy = generate_policy(principal['id'], 'Allow', event['methodArn'])
        logger.info("Allow to access")
        return policy
    except Exception as e:
        logger.warn(f"Failing due to {e}")
        raise Exception('Unauthorized')


def public_endpoint(event, context):
    logger.info("Event: {}".format(event))
    logger.info(f"userid: {event['requestContext']['authorizer']['principalId']}")
    return create_200_response('Hi ⊂◉‿◉つ from Public API')


def private_endpoint(event, context):
    logger.info(f"userid: {event['requestContext']['authorizer']['principalId']}")
    return create_200_response('Hi ⊂◉‿◉つ from Private API. Only logged in users can see this')

def verify_token(token, secret, algorithms):
    decoded_token = jwt.decode(token, secret, algorithms=[algorithms])
    return decoded_token


def generate_policy(principal_id, effect, resource):
    return {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    # "Resource": resource
                    "Resource": '*'

                }
            ]
        }
    }

def create_200_response(message):
    headers = {
        # Required for CORS support to work
        'Access-Control-Allow-Origin': '*',
        # Required for cookies, authorization headers with HTTPS
        'Access-Control-Allow-Credentials': True,
    }
    return create_aws_lambda_response(200, {'message': message}, headers)


def create_aws_lambda_response(status_code, message, headers):
    return {
        'statusCode': status_code,
        'headers': headers,
        'body': json.dumps(message)
    }