import boto3

"""
  Input Format: ! denotes optional item
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
      !"message": "<The service error>",
      !"response": "<Output of process on success>"
    }
"""

ddb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    if 'mock' in event and event['mock'] == True:
        return {
            'status': 'SUCCESS',
            'response': 'mocked'
        }

    table_name = event['table_name']
    key = event['key']

    try:
        table = ddb.Table(table_name)

        response = table.delete_item(
            Key = key
        )

        response.pop('ResponseMetadata')

        return {
            'status': 'SUCCESS',
            'response': response
        }
    
    except Exception as e:
        print("The Following error occurred while deleting the entity:")
        print(e)
        return {
            'status': 'FAILED',
            'message': "Error: " + str(type(e).__name__) + " - "+ str(e)
        }