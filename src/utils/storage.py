import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
import random
import time

def key_generate():
  timestamp = int(time.time())
  return timestamp*10000+random.randint(1, 9999)

class Storage():
  '''
  Base Storage Util, utilize the dynamoDB to store the data
  '''
  _instance = None
  _inited = False
  
  def __new__(cls, *args, **kwargs):
    if cls._instance is None:
      cls._instance = super(Storage, cls).__new__(cls)
    return cls._instance
  
  def __init__(self):
    if not self._inited:
      self.dynamodb = boto3.resource('dynamodb')
      self._inited = True
  
  def createTableByCls(self, cls):
    if not hasattr(cls, "__tablename__"):
      raise Exception("Object must have __tablename__ attribute")
    return self.createTable(cls.__tablename__, cls.__pkey__, cls.__pkeytype__)
      
  def createTable(self, table_name, pkey, pkey_type = 'N', protected=True, isOnDemand = False):
    try:
      table = self.dynamodb.Table(table_name)
      table.load()
      print(f"Table '{table_name}' already exists.")
      return False
    except ClientError as e:
      if e.response['Error']['Code'] == 'ResourceNotFoundException':
        if isOnDemand:
          account_table = self.dynamodb.create_table(
              TableName=table_name,
              KeySchema=[
                  {
                      'AttributeName': pkey,
                      'KeyType': 'HASH'  
                  }
              ],
              AttributeDefinitions=[
                  {
                      'AttributeName': pkey,
                      'AttributeType': pkey_type
                  }
              ],
              BillingMode='PAY_PER_REQUEST',
              DeletionProtectionEnabled=protected 
          )
        else:
          account_table = self.dynamodb.create_table(
              TableName=table_name,
              KeySchema=[
                  {
                      'AttributeName': pkey,
                      'KeyType': 'HASH'  
                  }
              ],
              AttributeDefinitions=[
                  {
                      'AttributeName': pkey,
                      'AttributeType': pkey_type
                  }
              ],
              ProvisionedThroughput={
                  'ReadCapacityUnits': 1,
                  'WriteCapacityUnits': 1
              },
              DeletionProtectionEnabled=protected 
          )
        account_table.meta.client.get_waiter('table_exists').wait(TableName=table_name)

        return True
      else:
        raise e
  
  def unprotectTable(self, table_name):
      table = self.dynamodb.Table(table_name)
      response = table.update(
          TableName=table_name,
          DeletionProtectionEnabled=False
      )
      return response
  
  def deleteTable(self, table_name):
    try:
      table = self.dynamodb.Table(table_name)
      table.delete()
      print(f"Table '{table_name}' deleted successfully.")
    except ClientError as e:
      if e.response['Error']['Code'] == 'ResourceNotFoundException':
        print(f"Table '{table_name}' does not exist.")
      else:
        print(f"Unexpected error: {e}")
  
  def save(self, table_name, value):
    table = self.dynamodb.Table(table_name)
    if self._is_array(value):
      with table.batch_writer() as batch:
        for item in value:
          batch.put_item(Item=item)
    else:
      table.put_item(Item=value)
      
  def saveObjects(self, objs):
    if self._is_array(objs) and len(objs) > 0:
      if not hasattr(objs[0], "__tablename__"):
        raise Exception("Object must have __tablename__ attribute")
      
      table_name = objs[0].__tablename__
      
      table = self.dynamodb.Table(table_name)
      with table.batch_writer() as batch:
        for item in objs:
          batch.put_item(Item=item.to_dict())
      

  def saveObject(self, obj):
    if not hasattr(obj, "__tablename__"):
      raise Exception("Object must have __tablename__ attribute")
    self.save(obj.__tablename__, obj.to_dict())
  def deleteObjectById(self, cls, id):
    if not hasattr(cls, "__tablename__"):
      raise Exception("Object must have __tablename__ attribute")
    table = self.dynamodb.Table(cls.__tablename__)
    try:
      response = table.delete_item(
          Key={
              cls.__pkey__: id
          }
      )
      return True
    except Exception as e:
      return False
  def deleteObject(self, obj):
    if not hasattr(obj, "__tablename__"):
      raise Exception("Object must have __tablename__ attribute")
    table = self.dynamodb.Table(obj.__tablename__)
    try:
      response = table.delete_item(
          Key={
              obj.__pkey__: getattr(obj, obj.__pkey__)
          }
      )
      return True
    except Exception as e:
      return False

  def loadObjects(self, cls, filter_lambda):
    if not hasattr(cls, "__tablename__"):
      raise Exception("Object must have __tablename__ attribute")
    
    items = self.loadItem(cls.__tablename__, filter_lambda)
    
    result = []
    for item in items:
      result.append(cls.from_dict(item))
    return result
  
  def loadAllObjects(self, cls):
    if not hasattr(cls, "__tablename__"):
      raise Exception("Object must have __tablename__ attribute")
    table = self.dynamodb.Table(cls.__tablename__)
    response = table.scan()
    result = []
    for item in  response.get('Items', []):
      result.append(cls.from_dict(item))
    return result
  
  def loadAllItems(self, table_name):
    table = self.dynamodb.Table(table_name)
    response = table.scan()
    return response.get('Items', [])
  
  def loadItem(self, table_name, filter_lambda):
    table = self.dynamodb.Table(table_name)
    scan_kwargs = {
        'FilterExpression': filter_lambda(Attr)
    }
    response = table.scan(**scan_kwargs)
    return response.get('Items', [])
  def loadItemById(self, table_name, id_key, id_val):
        table = self.dynamodb.Table(table_name)
        response = table.get_item(
            Key={
                id_key: id_val
            }
        )
        return response.get('Item')
  def loadObjectById(self, cls, item_id):
    if not hasattr(cls, "__tablename__"):
      raise Exception("Object must have __tablename__ attribute")
    item = self.loadItemById(cls.__tablename__, cls.__pkey__, item_id)
    return cls.from_dict(item) if item else None
  
  def _is_array(self, variable):
    return isinstance(variable, list)

  def _to_dict(self, obj):
        return {key: getattr(obj, key) for key in obj.__dict__ if not key.startswith('_')}

  def _from_dict(self, cls, data):
      instance = cls()
      for key, value in data.items():
          setattr(instance, key, value)
      return instance