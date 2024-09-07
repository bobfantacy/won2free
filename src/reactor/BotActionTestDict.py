from reactor.AbstractAction import AbstractAction

class BotActionTestDict(AbstractAction):
  def __init__(self):
    super().__init__(commands=['TestDict'])

  async def _execute(self, event_body):
    data = event_body['data']
    if type(data)==dict:
      self.buffer_message(f"dict data: {data}")
    else:
      self.buffer_message(f"list data: {data}")