from reactor.AbstractAction import AbstractAction
from bfxapi.models.order import OrderType
from model.lending_plan import LendingPlan
from model.funding_offer import FundingOffer
from datetime import datetime
from decimal import Decimal
import logging
import math

logger = logging.getLogger(__name__)

class BotActionReArrangeOffer(AbstractAction):
  def __init__(self):
    super().__init__(commands=['ReArrangeOffer'])

  async def _execute(self, context):
      logger.info('execute BotActionReArrangeOffer')
      await self.removeInactiveFundingOffer()
      lps = self.getActiveLendingPlans()
      for lp in lps:
        offer_count , message = await self.distribute_funding_offers(lp)
        if(offer_count > 0):
          self.buffer_message(f"{message}\n{lp.symbol} ReArrangeFundingOffer completed!")
  async def removeInactiveFundingOffer(self):
    activeOffers = await self.getAllActiveFundingOffers()
    filter_lambda = lambda Attr: Attr('account_id').eq(self.account.id)
    offers = self.storage.loadObjects(FundingOffer, filter_lambda)
    activeIds = [o.id for o in activeOffers]
    inactiveIds = [o.id for o in offers if o.id not in activeIds]
    for offer_id in inactiveIds:
      self.storage.deleteObjectById(FundingOffer, offer_id)
    
  async def distribute_funding_offers(self, lp):
    # Get All active offers
    filter_lambda = lambda Attr: Attr('lp_id').eq(lp.id)
    offers = self.storage.loadObjects(FundingOffer, filter_lambda)
    # Cancel All out of range offers
    delta = Decimal('0.000002')
    outRangeIds = [int(o.id) for o in offers if o.rate*100 + delta < lp.start_rate or o.rate*100 - delta > lp.end_rate]
    if len(outRangeIds)!=0:
      await self.cancel_funding_offers(outRangeIds)
      self.buffer_message(f"Canceled funding offer out of range of Plan {lp.id}!")
    inRangeOffers = [o for o in offers if o.rate*100 + delta >= lp.start_rate and o.rate*100 - delta <= lp.end_rate]
    
    amount_offering = Decimal(0)
    for o in inRangeOffers:
      amount_offering += o.amount
      
    if amount_offering > lp.total_amount:
      message = f"Plan {lp.d} offering {amount_offering} exceed total_amount {lp.total_amount}"
      return (0, message)
    
    min_amount = lp.min_amount
    start_rate = Decimal(lp.start_rate)
    end_rate = Decimal(lp.end_rate)

    period = lp.period
    offer_limit = lp.offer_limit
    symbol = lp.symbol
        
    balance_available = Decimal(await self.get_wallet_balance_available('funding', symbol[1:]))
    
    amount_need_lend = balance_available if balance_available <= lp.total_amount - amount_offering else lp.total_amount - amount_offering
    
    
    
    amount = amount_need_lend / offer_limit
    rate_gap = (end_rate - start_rate) if offer_limit == 1 else (end_rate - start_rate)/(offer_limit-1) 
    
    if amount < min_amount:
      amount = min_amount
    rate = start_rate 
    offer_message = []
    total_amount = amount_need_lend
    
    message = f"Distributing funding offers from {start_rate:.4f} to {end_rate:.4f} with rate gap of {rate_gap:.4f}\n"
    while amount_need_lend >=min_amount:
      if(amount_need_lend < amount + min_amount):
        amount = amount_need_lend
        
      response = await self.bfx.rest.submit_funding_offer(symbol, amount, rate/100, int(period))
      self.saveFundingOffer(response, lp.id)
      
      offer_message.append("Offer: {} {} {:f} {:<f} {}".format(response.notify_info.id, response.notify_info.symbol, response.notify_info.amount, response.notify_info.rate*100, response.notify_info.period))
      amount_need_lend -= amount
      rate += rate_gap
      
    # Only need the first, second and the last offer message
    offer_count = len(offer_message)
    offer_message = offer_message[0:2] + (offer_message[-1:] if len(offer_message) >= 3 else [])
    message = message + '\n'.join(offer_message)
    message = message + f"\nOffer Count: {offer_count:d}\nTotal Amount: {total_amount:.4f}"
    message = message + "\nDistributing funding offers completed!"
    return (offer_count, message)
  
  def saveFundingOffer(self, response, lp_id):
    funding_offer = FundingOffer(id=response.notify_info.id, 
                                   account_id = self.account.id,
                                   symbol = response.notify_info.symbol,
                                   mts_created = datetime.fromtimestamp(response.notify_info.mts_create/1000).isoformat(),
                                   mts_updated = datetime.fromtimestamp(response.notify_info.mts_updated/1000).isoformat(),
                                   amount = Decimal(str(response.notify_info.amount)),
                                   amount_orig = Decimal(str(response.notify_info.amount_orig)),
                                   type = response.notify_info.f_type,
                                   flags = response.notify_info.flags,
                                   status = response.notify_info.status,
                                   rate = Decimal(str(response.notify_info.rate)),
                                   period = response.notify_info.period,
                                   notify = response.notify_info.notify,
                                   hidden = response.notify_info.hidden,
                                   renew = response.notify_info.renew,
                                   lp_id = lp_id)
    self.storage.saveObject(funding_offer)
    
  def getActiveLendingPlans(self):
    filter_lambda = lambda Attr: Attr('status').eq('ACTIVE') & Attr('account_id').eq(self.account.id)
    lps = self.storage.loadObjects(LendingPlan, filter_lambda) 
    return lps
    
    