import os
import logging
import asyncio

loop = asyncio.get_event_loop()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

from reactor.reactor import Reactor
from utils.sqs import SqsUtils


reactor = Reactor()
sqs = SqsUtils()

def lambda_handler(event, context):
    logger.info('Event: {}'.format(event))
    messages = []
    if(event.get('Records') is not None):
        for msg in event.get('Records'):
            message = sqs.transform_to_message(msg)
            messages.append(message)
    results = loop.run_until_complete(*[reactor.processQueue(messages)])
    return 0
