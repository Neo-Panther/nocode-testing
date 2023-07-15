import boto3
import re

"""
    Input Format: ! denotes optional item
    event = {
        "bucket_name": "<Your Bucket Name>",
        "file_name": "<Your File Name (to be used in the s3 bucket)>",
        !"contents": "<Your file contents Regex>"
    }

    Output Format:
        {
        "status": "<FAILED|SUCCESS>",
        !"response": "<Output of process on success>",
        !"message": "<The service error>"
        }
"""

s3 = boto3.client('s3')

def lambda_handler(event, context):
    bucket_name = event['bucket_name']
    file_name = event['file_name']

    try:
        response = s3.get_object(
            Bucket = bucket_name,
            Key = file_name
        )

        response = response['Body'].read().decode('utf-8')
        contents = "*"
        if 'contents' in event:
            contents = event['contents']

        if re.search(contents, response):
            return {
                'status': 'SUCCESS',
                'response': 'File exists and contains the given contents'
            }
            
        else:
            return {
                'status': 'SUCCESS',
                'response': 'File does not exist'
            }
    
    except Exception as e:
        print("The Following error occurred while deleting the entity:")
        print(e)
        return {
            'status': 'FAILED',
            'message': "Error: " + str(type(e).__name__) + " - "+ str(e)
        }