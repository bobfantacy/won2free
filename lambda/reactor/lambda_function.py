import os
import logging
import asyncio

loop = asyncio.get_event_loop()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

from reactor.reactor import Reactor

def lambda_handler(event, context):
    reactor = Reactor()
    results = loop.run_until_complete(*[reactor.processQueue()])
    return 0
