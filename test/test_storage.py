
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

    def test_base_storage(self):
        result = self.storage.createTable(self.table_name, pkey='id', pkey_type='N')
        self.assertTrue(result)  
        
        value = {
          'id': 1,
          'name' : 'alice',
          'age' : 10,
          'sex' : 'male'
        }
        self.storage.save(self.table_name, value)
        
        values = [
          {
            'id': 2,
            'name' : 'bob',
            'age' : 12,
            'sex' : 'female'
          },
          {
            'id': 3,
            'name' : 'calvin',
            'age' : 14,
            'sex' : 'male'
          },
        ]
        
        self.storage.save(self.table_name, values)
        
        items = self.storage.loadAllItems(self.table_name)
        print(items)
        self.assertEqual(len(items), 3)
        
        filter_lambda = lambda Attr: Attr('name').eq('calvin')

        items = self.storage.loadItem(self.table_name, filter_lambda)
        self.assertEqual(len(items), 1)
        
        filter_lambda = lambda Attr: Attr('age').gte(12)

        items = self.storage.loadItem(self.table_name, filter_lambda)
        self.assertEqual(len(items), 2)
        
        filter_lambda = lambda Attr: Attr('age').gte(12) & Attr('sex').eq('male')
        items = self.storage.loadItem(self.table_name, filter_lambda)
        self.assertEqual(len(items), 1)
        
        self.storage.unprotectTable(self.table_name)
        self.storage.deleteTable(self.table_name)

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