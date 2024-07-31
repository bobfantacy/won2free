import unittest
import sys

import json
import random
import sys
import os
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(parent_dir, 'src'))

from utils.telebot import TelebotUtils

class TestTelebotUtils(unittest.TestCase):
    def setUp(self):
        pass
      
    def test_telebotutils_singleton(self):
        bot1 = TelebotUtils({})
        bot2 = TelebotUtils({})
        self.assertEqual(bot1, bot2)

if __name__ == '__main__':
    unittest.main()
