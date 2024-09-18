from reactor.AbstractAction import AbstractAction
from bfxapi.models.order import OrderType
from model.lending_plan import LendingPlan
from utils.global_context import *
from datetime import datetime, timedelta
import math
import time

class BotActionFundingSummary(AbstractAction):
  
  def __init__(self):
    super().__init__(commands=['FundingSummary'])

  async def _execute(self, context):
      funding_info = await self._getFundingMonthSummary()
      self.buffer_message(f"\nEarning Month Summary: {funding_info['earning']:.2f} USD")
      self.buffer_message(f"USD yield: {funding_info['funding_usd']['yield_lend']:.5f} (APR: {funding_info['funding_usd']['yield_lend']*365:.2f}% ), duration: {funding_info['funding_usd']['duration_lend']:.0f}")
      self.buffer_message(f"UST yield: {funding_info['funding_ust']['yield_lend']:.5f} (APR: {funding_info['funding_ust']['yield_lend']*365:.2f}% ), duration: {funding_info['funding_ust']['duration_lend']:.0f}")
      days = 3
      self.buffer_message(f"\nEarning in {days} days")
      for currency in ['USD', 'UST']:
        ledgers = await self._fetch_daily_ledgers(currency, days)
        if ledgers:
          for l in ledgers:
            self.buffer_message(f"{l['currency']} {l['amount']:.2f} {l['balance']:5.2f} {l['apr']*100:.2f}% {l['mts']}")
          self.buffer_message("\r")
  
  async def _fetch_daily_ledgers(self, currency: str = 'USD', days = 1):
    now = datetime.now()
    start_time = now - timedelta(days=days)
    
    start = int(start_time.timestamp()*1000)
    end = int(now.timestamp()*1000)
    
    # 使用 await 调用异步方法
    ledgers = await self.bfx.rest.get_ledgers(symbol=currency, start=start, end=end, limit=25, category=None)
    return [{'currency': l.currency, 'amount': l.amount, 'balance': l.balance, 'apr': (l.amount/l.balance*365), 'mts': datetime.fromtimestamp(l.mts/1000)} 
            for l in ledgers if l.description == 'Margin Funding Payment on wallet funding']
  async def _getFundingMonthSummary(self):
    endpoint = "auth/r/summary"
    raw_summary = await self.bfx.rest.post(endpoint)
    key='fUSD'
    endpoint = f"auth/r/info/funding/{key}"
    raw_fusd_funding_info = await self.bfx.rest.post(endpoint)
    key='fUST'
    endpoint = f"auth/r/info/funding/{key}"
    raw_fust_funding_info = await self.bfx.rest.post(endpoint)

    funding_info ={
      'earning': raw_summary[6][2],
      'earning_curr': raw_summary[6][1],
      'funding_usd' : 
        {
          'symbol': raw_fusd_funding_info[1],
          'yield_loan': raw_fusd_funding_info[2][0]*100,
          'yield_lend':raw_fusd_funding_info[2][1]*100,
          'duration_loan':raw_fusd_funding_info[2][2],
          'duration_lend': raw_fusd_funding_info[2][3],
        },
      'funding_ust' : 
        {
          'symbol': raw_fust_funding_info[1],
          'yield_loan': raw_fust_funding_info[2][0]*100,
          'yield_lend':raw_fust_funding_info[2][1]*100,
          'duration_loan':raw_fust_funding_info[2][2],
          'duration_lend': raw_fust_funding_info[2][3],
        },
    }
    return funding_info