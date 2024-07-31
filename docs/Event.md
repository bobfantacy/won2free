All messages are send to the same AWS SQS FIFO queue. The struct of event like this
```
event = {
  'type' : 'bot_action',
  'body' : {
    'command' : 'ReArrangeOffer',
    'account_name' : 'funding',
    'data' : object
  }
}
```