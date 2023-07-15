import boto3

"""
  Input Format: ! denotes optional item
  ? denotes info
  event = {
    "table_name": "<Your Table Name>",
    "item": {
      "<attribute name>": <Data>,
      ? Number of such pairs is variable, dynamoDB conventions to be followed, primary key value must be provided
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
    # Perform operation
    response = table.put_item(Item=event["item"])

    # Delete irrelevant info
    response.pop("ResponseMetadata")
  except Exception as e:
    print("The Following error occurred while creating the entity:")
    print(e)
    return {
      "status": "FAILED",
      "message": "Error: " + str(type(e).__name__) + " - "+ str(e)
    }
  return {
      "status": "SUCCESS",
      "response": response
    }