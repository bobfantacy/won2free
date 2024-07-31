import unittest
import sys
import os
import json
import random
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(parent_dir, 'src'))

from utils.sqs import SqsUtils

class TestSqs(unittest.TestCase):
    def setUp(self):
        queue_name = 'test-queue.fifo'
        os.environ['QUEUE_NAME'] = queue_name
        SqsUtils.create_queue(queue_name=queue_name)
        
    def test_create_fifo_queue(self):
        sqs = SqsUtils()
        queue_name=f'test-queue{random.randint(1,100)}.fifo'
        queue_url = sqs.create_queue(queue_name=queue_name)
        self.assertIsNotNone(queue_url)
        queue = sqs.get_queue(queue_name=queue_name)
        queue.delete()
        
    def test_send_receive_delete_message(self):
        sqs = SqsUtils()
        # Send message
        event = {
            'id': random.randint(1, 1000),
            'data': "hello world"
        }
        send_response = sqs.send_message(event)
        self.assertEqual(send_response['ResponseMetadata']['HTTPStatusCode'], 200)

        # Receive message
        messages = sqs.receive_messages(1)
        self.assertEqual(len(messages), 1)
        print(f"len(messages): {len(messages)}")
        for message in messages:
            self.assertEqual(json.loads(message.body)['data'], "hello world")
            message.delete()
    def test_sqs_singleton(self):
        sqs1 = SqsUtils()
        sqs2 = SqsUtils()
        self.assertEqual(sqs1, sqs2)

if __name__ == '__main__':
    unittest.main()
