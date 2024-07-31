import unittest
import sys
import os
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(parent_dir, 'src'))

import boto3

class TestSqs(unittest.TestCase):        
        
    def test_sqs_native(self):
        sqs = boto3.resource('sqs')
        queue = sqs.get_queue_by_name(QueueName='test-queue.fifo')
        print('\n'+queue.url)
        print(queue.attributes.get('DelaySeconds'))
        response = queue.send_message(MessageBody='world', MessageGroupId='default')

        # The response is NOT a resource, but gives you a message ID and MD5
        print(response.get('MessageId'))
        print(response.get('MD5OfMessageBody'))
        
        messages = queue.receive_messages(MaxNumberOfMessages=1)
        for message in messages:
            print(message.body)
            message.delete()
        

if __name__ == '__main__':
    unittest.main()
