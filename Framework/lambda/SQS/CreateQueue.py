import boto3

"""
  Input Format: ! denotes optional item
  ? denotes info
  event = {
    "queue_name": "<Your Topic Name>",
    !"fifo": <true|false>, Currently only supported in us-west-2 and us-east-2
    !"attributes": "<Dict of SQS specific attributes>"
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
    sqs = boto3.client('sqs')

    if 'mock' in event and event['mock'] == True:
        return {
            "status": "SUCCESS",
            "response": "mocked"
        }

    queue_name = event['queue_name']

    if 'fifo' in event and event['fifo'] == True:
        queue_name += ".fifo"
    
    attributes = {}
    if 'attributes' in event:
        attributes = event['attributes']

    try:
        response = sqs.create_queue(
            QueueName=queue_name,
            Attributes=attributes
        )

        response.pop("ResponseMetadata")
    except Exception as e:
        print("The Following error occurred during the process:")
        print(e)
        return {
            "status": "FAILED",
            "message": "Error: " + str(type(e).__name__) + " - "+ str(e)
        }
    
    return {
        "status": "SUCCESS",
        "response": response
    }
