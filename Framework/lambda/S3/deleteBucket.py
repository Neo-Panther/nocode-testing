import boto3
import json

"""
    Input Format: ! denotes optional item
    event = {
        "bucket_name": "<Your Bucket Name>",
        !"mock": <true|false>
    }

    Output Format:
        {
        "status": "<FAILED|SUCCESS>",
        !response": "<Output of process on success>",
        !"message": "<The service error>"
        }
"""

s3 = boto3.client('s3')

def lambda_handler(event, context):
    if 'mock' in event and event['mock'] == True:
        return {
            'status': 'SUCCESS',
            'response': 'mocked'
        }

    bucket_name = event['bucket_name']

    try:
        s3.delete_bucket(
            Bucket = bucket_name
        )

        return {
            'status': 'SUCCESS',
            'response': 'Bucket Deleted'
        }
    
    except Exception as e:
        print("The Following error occurred while deleting the entity:")
        print(e)
        return {
            'status': 'FAILED',
            'message': "Error: " + str(type(e).__name__) + " - "+ str(e)
        }