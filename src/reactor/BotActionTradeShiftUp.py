from reactor.AbstractAction import AbstractAction
from utils.global_context import *
from model.order_grid_strategy import OrderGridStrategy
import logging
import time

logger = logging.getLogger(__name__)

class BotActionTradeShiftUp(AbstractAction):
  def __init__(self):
    super().__init__(commands=['ShiftUp'])
    
  async def _execute(self, event_body):
    command = event_body['command']
    data = event_body['data']
    if type(data)==dict:
      self.buffer_message("json args NOT supported")
      return
    
    if(len(data) < 2):
      self.buffer_message("Invalid command, please use: ShiftUp <account_name> <grid_id> <True/False>")
      return
    
    grid = self.storage.loadObjectById(OrderGridStrategy, int(data[0]))
    if data[1].lower() == 'true':
      grid.shift_up_enabled= True
      grid.shift_up_checked= True
      self.storage.saveObject(grid)
      self.buffer_message(f"Grid Strategy {grid.id} Enable Shift Up")
    elif data[1].lower() == 'false':
      grid.shift_up_enabled= False
      grid.shift_up_checked= False
      self.storage.saveObject(grid)
      self.buffer_message(f"Grid Strategy {grid.id} Disable Shift Up")
    
    