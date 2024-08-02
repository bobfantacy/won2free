import logging
from job.jobEvent import *

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    GridStrategyOper()
    return