import boto3

"""
  Input Format: ! denotes optional item
  event = {
    "table_name": "<Your Table Name>",
    !"mock": <true|false>
  }

  Output Format:
    {
      "status": "<FAILED|SUCCESS>",
      !"response": "<Output of process on success>",
      !"message": "<The service error>"
    }
"""

ddb = boto3.client('dynamodb')

def lambda_handler(event, context):
    if 'mock' in event and event['mock'] == True:
        return {
            'status': 'SUCCESS',
            'response': 'mocked'
        }

    table_name = event['table_name']

    try:
        response = ddb.delete_table(
            TableName = table_name
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