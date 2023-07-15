import boto3

"""
  Input Format: ! denotes optional item
  event = {
    "table_name": "<Your Table Name>",
    "item": {
      "<attribute name>": <Data>,
      ! Number of such pairs is variable, dynamoDB conventions to be followed
    }
  }

  Output Format:
    {
      "status": "<FAILED|SUCCESS>",
      !"response": "<Output of process on success>"
      !"message": "<The service error>"
    }
"""

ddb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    table_name = event['table_name']
    item = event['item']

    try:
        table = ddb.Table(table_name)

        response = table.get_item(
            Key = item
        )

        if 'Item' in response:
            return {
                'status': 'SUCCESS',
                'response': response['Item']
            }
        else:
            return {
                'status': 'SUCCESS',
                'response': 'Entry does not exist'
            }
    
    except Exception as e:
        print("The Following error occurred while creating the entity:")
        print(e)
        return {
            'status': 'Failed',
            'message': "Error: " + str(type(e).__name__) + " - "+ str(e)
        }