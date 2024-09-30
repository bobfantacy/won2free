
import unittest
import sys
import os
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))

from utils.storage import Storage
from utils.storage import *

class TestStorage(unittest.TestCase):

    def setUp(self):
        self.storage = Storage()
        self.table_name = 'table_test3'

    def testCreateTableByCls(self):
      class TestClass():
        __tablename__ = 'table_by_cls5'
        __pkey__ = 'id'
        __pkeytype__ = 'N'
        id = None
        data = None
        def __init__(self, id, data):
          self.id = id
          self.data = data
      result = self.storage.createTableByCls(TestClass)
      self.assertEquals(result, True)
      
      self.storage.unprotectTable(TestClass.__tablename__)
      self.storage.deleteTable(TestClass.__tablename__)
      
    def tearDown(self):
        
        pass

if __name__ == '__main__':
    unittest.main()