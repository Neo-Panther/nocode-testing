import boto3

"""
  Input Format: ! denotes optional item
  ? denotes info
  event = {
    "queue_name": "<Your Topic Name>",
    !MaxNumberOfMessages: <1-10> ? default 1
    !WaitTimeSeconds: <0-20> ? default 0
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
    MaxNumberOfMessages = 1
    WaitTimeSeconds = 0
    if 'MaxNumberOfMessages' in event:
        MaxNumberOfMessages = event['MaxNumberOfMessages']
    
    if 'WaitTimeSeconds' in event:
        WaitTimeSeconds = event['WaitTimeSeconds']


    try:
        queue_url = sqs.get_queue_url(
            QueueName=queue_name
        )

        data = sqs.receive_message(
            QueueUrl=queue_url['QueueUrl'],
            MaxNumberOfMessages=MaxNumberOfMessages,
            WaitTimeSeconds=WaitTimeSeconds
        )

        response = {}

        if 'Messages' in data:
            for message in data['Messages']:
                response[message['MessageId']] = [message['Body'], message['ReceiptHandle']]

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