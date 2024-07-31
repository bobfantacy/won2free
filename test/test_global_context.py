import unittest
import sys
import os
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))

from utils.global_context import GlobalContext

class TestAccount(unittest.TestCase):
  
  def setUp(self):
    pass
  
  def testEnv(self):
    aws = os.getenv('AWS_PROFILE')
    print(aws)
  
  def tearDown(self):
    pass
if __name__ == '__main__':
    unittest.main()