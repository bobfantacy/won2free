from reactor.AbstractAction import AbstractAction
from bfxapi.models.order import OrderType
from model.lending_plan import LendingPlan
from utils.global_context import *
from datetime import datetime, timedelta
import math
import time

class BotActionFundingNotification(AbstractAction):
  
  def __init__(self):
    super().__init__(commands=['FundingNotification'])

  async def _execute(self, context):
    for currency in ['fUSD', 'fUST']:
      await self._notify_executed_offers(currency)
        
  async def _notify_executed_offers(self, symbol: str = 'fUSD', minutes = 61):
    now = datetime.now()
    start_time = now - timedelta(minutes=minutes)
    end_time = now
    
    start = int(start_time.timestamp()*1000)
    end =   int(end_time.timestamp()*1000)
    offers = await self.bfx.rest.get_funding_offer_history(symbol=symbol, start=start, end=end, limit=500)
    for o in offers:
      if 'EXECUTED' in o.status:
        self.buffer_message(f"{o.id} {o.symbol} {o.status} {o.rate*100*365:.4f}% {o.period} {datetime.fromtimestamp(o.mts_updated/1000)}")
