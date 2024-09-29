import boto3
import os
import json
import logging
from botocore.exceptions import ClientError

class MockMessage:
    def __init__(self, receipt_handle, body, message_id):
        self.receipt_handle = receipt_handle
        self.body = body
        self.message_id = message_id

    def delete(self):
        sqs = SqsUtils()
        sqs.delete_message(self.receipt_handle)
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
      self.logger.error(e)
      raise e
  
  def receive_messages(self, maxNumberOfMessages=1):
    response = self.queue.receive_messages(
        MaxNumberOfMessages=maxNumberOfMessages,
        WaitTimeSeconds=1
    )
    return response
  
  def delete_message(self, receipt_handle):
    try:
      response = self.queue.delete_messages(
          Entries=[
              {
                  'Id': '1',
                  'ReceiptHandle': receipt_handle
              }
          ]
      )
      
      if 'Successful' in response and len(response['Successful']) > 0:
        # print("Successfully deleted message.")
        pass
      else:
        print("Failed to delete message.")
          
    except Exception as e:
      print(f"Error deleting message: {e}")
      
  def get_queue(self, queue_name):
    return self.sqs.get_queue_by_name(QueueName=queue_name)
  
  def transform_to_message(self, message_dict):
    message = MockMessage(
        receipt_handle=message_dict['receiptHandle'],
        body=message_dict['body'],
        message_id=message_dict['messageId']
    )
    return message
  
  @classmethod
  def create_queue(cls, queue_name, fifo_queue=True, content_based_deduplication=True):
    sqs = boto3.resource('sqs')
    if fifo_queue and not queue_name.endswith('.fifo'):
            queue_name += '.fifo'
            
    try:
        response = sqs.get_queue_by_name(QueueName=queue_name)
        print(f"Queue '{queue_name}' already exists. URL: {response.url}")
        return response.url
    except ClientError as e:
      if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
        attributes = {
            'FifoQueue': 'true' if fifo_queue else 'false',
            'ContentBasedDeduplication': 'true' if content_based_deduplication else 'false'
        }
        response = sqs.create_queue(
            QueueName=queue_name,
            Attributes=attributes
        )
        print('Queue created successfully, queue URL: {}'.format(response.url))
        return response.url
      else:
        raise Exception(f"Error in creating queue {queue_name}")
      