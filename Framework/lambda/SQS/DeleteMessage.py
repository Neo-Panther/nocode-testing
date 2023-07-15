import boto3

"""
  Input Format: ! denotes optional item
  ? denotes info
  event = {
    "queue_name": "<Your Topic Name>",
    "receipt_handle": "<The receipt handle of the message to delete from read message>"
    !"mock": <true|false>
  }

  Output Format:
    {
      "status": "<FAILED|SUCCESS>",
      !"response": "<Output of process on success>"
      !"message": "<The service error>"
    }
"""

def lambda_handler(event, context):
    if 'mock' in event and event['mock'] == True:
        return {
            "status": "SUCCESS",
            "response": "mocked"
        }
    
    queue_name = event['queue_name']
    sqs = boto3.client('sqs')
    receipt_handle = event['receipt_handle']

    try:
        queue_url = sqs.get_queue_url(
            QueueName=queue_name
        )

        sqs.delete_message(
            QueueUrl=queue_url['QueueUrl'],
            ReceiptHandle=receipt_handle
        )

    except Exception as e:
        print("The Following error occurred during the process:")
        print(e)
        return {
            "status": "FAILED",
            "message": "Error: " + str(type(e).__name__) + " - "+ str(e)
        }
    
    return {
        "status": "SUCCESS",
        'response': 'Deleted message from queue'
    }
