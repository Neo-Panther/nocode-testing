import boto3

"""
  Input Format: ! denotes optional item
  ? denotes info
  event = {
    "queue_name": "<Your Topic Name>"
  }

  Output Format:
    {
      "status": "<FAILED|SUCCESS>",
      !"response": "<Output of process on success>"
      !"message": "<The service error>"
    }
"""

def lambda_handler(event, context):
    queue_name = event['queue_name']
    sqs = boto3.client('sqs')

    try:
        queue_url = sqs.get_queue_url(
            QueueName=queue_name
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
        "response": queue_url['QueueUrl']
    }