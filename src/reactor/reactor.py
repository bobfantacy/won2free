import logging
import json
from utils.sqs import SqsUtils
from utils.global_context import GlobalContext
from reactor.BotActionReArrangeOffer import BotActionReArrangeOffer
from reactor.BotActionTradeStatusCheck import BotActionTradeStatusCheck
from reactor.BotActionSyncTrade import BotActionSyncTrade
from reactor.BotActionAutoFundingRate import BotActionAutoFundingRate
from reactor.BotActionBuy import BotActionBuy
from reactor.BotActionSell import BotActionSell
from reactor.BotActionResumeGrid import BotActionResumeGrid
from reactor.BotActionTestDict import BotActionTestDict

from decimal import Decimal, getcontext, Inexact, Rounded
context = GlobalContext()

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO  # Set the desired logging level (INFO, WARNING, ERROR, etc.)
)

logger = logging.getLogger(__name__)

class Reactor():
  
  def __init__(self):
    logger.info(f"Init Reactor...")
    self.botEventActions = [
       BotActionReArrangeOffer(),
       BotActionTradeStatusCheck(),
       BotActionSyncTrade(),
       BotActionAutoFundingRate(),
       BotActionBuy(),
       BotActionSell(),
       BotActionResumeGrid(),
       BotActionTestDict()
    ]

  async def processQueue(self, messages):
    sqs = SqsUtils()
    # Receive message
    if len(messages)==0:
      messages = sqs.receive_messages(10)
    logger.info(f"Starting Reactor...")
    #if the queue is full, just keep run
    while len(messages)!=0:
      logger.info(f"Received message size: {len(messages)}")
      for message in messages:
        try:
          event_msg = json.loads(message.body)
          body = event_msg['body']
          command = body['command']
          account_name = body['account_name']
          if context.accounts.get(account_name) is None:
            logger.error(f"Account not found: {account_name}")
            message.delete()
            continue
          missMatched = True
          for action in self.botEventActions:
            if(action.match(command)):
              logger.info(f"{account_name} Matched action: {type} {command} {account_name}")
              await action.execute(body)
              missMatched = False
              break
          if missMatched:
            logger.warning(f"Missed match event:  {type} {command} {account_name}")
            pass
          message.delete()
        except Exception as e:
          logger.error(e)
      messages = sqs.receive_messages(10)
    logger.info("finish")