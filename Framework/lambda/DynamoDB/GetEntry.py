import boto3

"""
  Input Format: ! denotes optional item
  ? denotes info
  event = {
    "table_name": "<Your Table Name>",
    "key": {
      "<hash key name>": <hash key value>,
      !"<sort|range key name>": <sort|range key value>
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
  ddb = boto3.resource('dynamodb')
  # Get the table
  table = ddb.Table(event["table_name"])

  try:
    # Get Item from table
    response = table.get_item(Key = event["Key"])

    # Delete irrelevant info
    response.pop("ResponseMetadata")
  except Exception as e:
    return {
      "status": "FAILED",
      "message": "Error: " + str(type(e).__name__) + " - "+ str(e)
    }
  return {
      "status": "SUCCESS",
      "response": response
    }