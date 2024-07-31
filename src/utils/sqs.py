import boto3
import os
import json
import logging

class SqsUtils:
  
  _instance = None
  _inited = False
  # singleton pattern, keep only one instance of GlobalConfig
  def __new__(cls, *args, **kwargs):
    if cls._instance is None:
      cls._instance = super(SqsUtils, cls).__new__(cls)
    return cls._instance
  
  def __init__(self):
    if not self._inited:
      self.sqs = boto3.resource('sqs')
      queue_name = os.getenv('QUEUE_NAME')
      self.queue = self.sqs.get_queue_by_name(QueueName=queue_name)
      self.logger = logging.getLogger(__name__)
      self._inited = True
    
  def send_message(self,event_data):
    try:
      msgBody = json.dumps(event_data)
      self.logger.info('Sending message to SQS, msg body: {}'.format(msgBody))
      response = self.queue.send_message(MessageBody=msgBody,
                            MessageGroupId= 'default'
                            )
      return response
    except Exception as e:
      print(e)
      self.logger.error(e)
  
  def receive_messages(self, maxNumberOfMessages=1):
    response = self.queue.receive_messages(
        MaxNumberOfMessages=maxNumberOfMessages,
        WaitTimeSeconds=1
    )
    return response
  
  def get_queue(self, queue_name):
    return self.sqs.get_queue_by_name(QueueName=queue_name)
  
  @classmethod
  def create_queue(cls, queue_name, fifo_queue=True, content_based_deduplication=True):
    sqs = boto3.resource('sqs')
    try:
        attributes = {
            'FifoQueue': 'true' if fifo_queue else 'false',
            'ContentBasedDeduplication': 'true' if content_based_deduplication else 'false'
        }
        if fifo_queue and not queue_name.endswith('.fifo'):
            queue_name += '.fifo'
        response = sqs.create_queue(
            QueueName=queue_name,
            Attributes=attributes
        )
        print('Queue created successfully, queue URL: {}'.format(response.url))
        return response.url
    except Exception as e:
        print('Failed to create queue: {}'.format(e))
        return None
if __name__ == '__main__':
  sqs = SqsUtils()
  