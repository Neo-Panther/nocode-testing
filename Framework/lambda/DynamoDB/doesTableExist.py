import boto3

"""
  Input Format: ! denotes optional item
  event = {
    "table_name": "<Your Table Name>"
  }

  Output Format:
    {
      "status": "<FAILED|SUCCESS>",
      !response": "<Output of process on success>",
      !"message": "<The service error>"
    }
"""

ddb = boto3.client('dynamodb')

def lambda_handler(event, context):
    table_name = event['table_name']
    
    try:
        response = ddb.describe_table(
            TableName = table_name
        )

        response.pop('ResponseMetadata')

        return {
            'status': 'SUCCESS',
            'response': response
        }
    
    except Exception as e:
        print("The Following error occurred:")
        print(e)

        if (type(e).__name__ == 'ResourceNotFoundException'):
            return {
                'status': 'SUCCESS',
                'response': 'Table does not exist'
            }
        else:
            return {
                'status': 'FAILED',
                'message': "Error: " + str(type(e).__name__) + " - "+ str(e)
            }