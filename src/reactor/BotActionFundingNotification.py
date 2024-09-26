from reactor.AbstractAction import AbstractAction
from bfxapi.models.order import OrderType
from model.lending_plan import LendingPlan
from utils.global_context import *
from datetime import datetime, timedelta
import math
import time
import re

class BotActionFundingNotification(AbstractAction):
  
  def __init__(self):
    super().__init__(commands=['FundingNotification'])

  async def _execute(self, context):
    for currency in ['fUSD', 'fUST']:
      await self._notify_executed_offers(currency)
      
  def extract_percentage(self, text):
        match = re.search(r'(\d+\.\d+)%', text)
        if match:
            return float(match.group(1))
        return 0
  async def _notify_executed_offers(self, symbol: str = 'fUSD', minutes = 180):
    now = datetime.now()
    start_time = now - timedelta(minutes=minutes)
    end_time = now
    
    start = int(start_time.timestamp()*1000)
    end =   int(end_time.timestamp()*1000)
    offers = await self.bfx.rest.get_funding_offer_history(symbol=symbol, start=start, end=end, limit=500)
    for o in offers:
      if 'EXECUTED' in o.status:
        actual_rate = self.extract_percentage(o.status)
        self.buffer_message(f"{o.id} {o.symbol} {o.status} {actual_rate*365:.4f}% {o.period} {datetime.fromtimestamp(o.mts_updated/1000)}")
