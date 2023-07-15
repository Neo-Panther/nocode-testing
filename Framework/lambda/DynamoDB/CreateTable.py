import boto3

"""
  Input Format: ! denotes optional item
  ? denotes info
  event = {
    "table_name": "<Your Table Name>",
    "key": {
      "hash_key": {
        "name": "<Name of your hash key>",
        "type": "<DynamoDB type of your hash key, eg. S for string>"
      },
      !"sort_key": {
        "name": "<Name of your sort|range key>",
        "type": "<DynamoDB type of your sort|range key, eg. S for string>"
      }
    },
    !"provisioned_throughput": {
      "read_capacity": "<initial provisioned read capacity units>",
      "write_capacity": "<initial provisioned write capacity units>"
    },
    !"mock": <true|false>
  }

  Output Format:
    {
      "status": "<FAILED|SUCCESS>",
      !"response": "<Output of process on success>"
      !"message": "<The service error>"
    }
"""
def handler(event, context):
  # Mock if needed
  if 'mock' in event and event['mock'] == True:
    return {
      "status": "SUCCESS",
      "response": "mocked"
    }
  
  # Get the service resource.
  ddb = boto3.client('dynamodb')

  # Extract the primary key(s)
  keySchema = [{
    "AttributeName": event["key"]["hash_key"]["name"],
    "KeyType": "HASH"
  }]
  attributeDefinitions = [{
    "AttributeName": event["key"]["hash_key"]["name"],
    "AttributeType": event["key"]["hash_key"]["type"]
  }]
  if "sort_key" in event["key"]:
      keySchema += [{
      "AttributeName": event["key"]["sort_key"]["name"],
      "KeyType": "RANGE"
      }]
      attributeDefinitions += [{
        "AttributeName": event["key"]["sort_key"]["name"],
        "AttributeType": event["key"]["sort_key"]["type"]
      }]
  # Extract Throughput capacity
  readCap = writeCap = 5
  if "provisioned_throughput" in event:
    readCap = event["provisioned_throughput"]["read_capacity"]
    writeCap = event["provisioned_throughput"]["write_capacity"]

  try:
    # Get the service resource.
    dynamodb = boto3.resource("dynamodb")

    # Create the DynamoDB table.
    response = dynamodb.create_table(
      TableName=event["table_name"],
      KeySchema=keySchema,
      AttributeDefinitions=attributeDefinitions,
      ProvisionedThroughput={
        "ReadCapacityUnits": readCap,
        "WriteCapacityUnits": writeCap
      }
    )
    
    # Delete irrelevant info
    response.pop("ResponseMetadata")
  except Exception as e:
    return {
      "status": "FAILED",
      "message": "Error: " + str(type(e).__name__) + str(e)
    }
  return {
      "status": "SUCCESS"
    }



