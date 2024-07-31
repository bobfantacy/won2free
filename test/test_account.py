import unittest
import sys
import os
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))

from utils.storage import Storage
from utils.storage import *
from model.account import Account

class TestAccount(unittest.TestCase):
  
  def setUp(self):
    self.storage = Storage()
    self.table_name = 'account_test'
    self.storage.createTable(self.table_name, pkey='id', pkey_type='N')
  
  def test_sava_account(self):
    account1 = Account(
        id=1,
        account_name='example_account',
        bfx_key='example_key',
        bfx_secret='example_secret',
        affiliate_code='example_code',
        create_time='2023-01-01T00:00:00Z',
        update_time='2023-01-01T00:00:00Z',
        extra={'key': 'value'}
    )
    account2 = Account(
        id=2,
        account_name='example_account2',
        bfx_key='example_key2',
        bfx_secret='example_secret2',
        affiliate_code='example_code2',
        create_time='2023-01-01T00:00:00Z',
        update_time='2023-01-01T00:00:00Z',
        extra={'key': 'value'}
    )
    
    self.storage.save(self.table_name, account1.to_dict())
    self.storage.save(self.table_name, account2.to_dict())
    
    items = self.storage.loadAllItems(self.table_name)
    self.assertEqual(len(items), 2)
    
    filter_lambda = lambda Attr: Attr('account_name').eq('example_account')

    items = self.storage.loadItem(self.table_name, filter_lambda)
    self.assertEqual(len(items), 1)
    
    account = Account.from_dict(items[0])
    self.assertEqual(account.bfx_key, 'example_key')
    
  def test_sava_account_object(self):
    Account.__tablename__ = 'account_test'
    account1 = Account(
        id=1,
        account_name='example_account',
        bfx_key='example_key',
        bfx_secret='example_secret',
        affiliate_code='example_code',
        create_time='2023-01-01T00:00:00Z',
        update_time='2023-01-01T00:00:00Z',
        extra={'key': 'value'}
    )
    account2 = Account(
        id=2,
        account_name='example_account2',
        bfx_key='example_key2',
        bfx_secret='example_secret2',
        affiliate_code='example_code2',
        create_time='2023-01-01T00:00:00Z',
        update_time='2023-01-01T00:00:00Z',
        extra={'key': 'value'}
    )
    
    self.storage.saveObject(account1)
    self.storage.saveObject(account2)
    
    items = self.storage.loadAllObjects(Account)
    self.assertEqual(len(items), 2)
          
    filter_lambda = lambda Attr: Attr('account_name').eq('example_account')

    items = self.storage.loadObjects(Account, filter_lambda)
    self.assertEqual(len(items), 1)
    
    account = items[0]
    self.assertEqual(account.bfx_key, 'example_key')
  
  def tearDown(self):
    self.storage.unprotectTable(self.table_name)
    self.storage.deleteTable(self.table_name)
if __name__ == '__main__':
    unittest.main()