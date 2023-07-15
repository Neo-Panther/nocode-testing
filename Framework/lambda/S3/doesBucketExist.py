import boto3
import json

"""
    Input Format: ! denotes optional item
    event = {
        "bucket_name": "<Your Bucket Name>"
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
    bucket_name = event['bucket_name']

    try:
        response = s3.get_bucket_location(
            Bucket = bucket_name
        )
        
        response.pop('ResponseMetadata')

        return {
            'status': 'SUCCESS',
            'response': response
        }
    
    except Exception as e:
        print("The Following error occurred while deleting the entity:")
        print(e)

        if type(e).__name__ == 'NoSuchBucket':
            return {
                'status': 'SUCCESS',
                'response': 'Bucket does not exist'
            }
        else:
            return {
                'status': 'FAILED',
                'message': "Error: " + str(type(e).__name__) + " - "+ str(e)
            }