import boto3

"""
  Input Format: ! denotes optional item
  ? denotes info
  event = {
    "topic_arn": "<Your Topic ARN>"
  }

  Output Format:
    {
      "status": "<FAILED|SUCCESS>",
      !"response": "<Output of process on success>"
      !"message": "<The service error>"
    }
"""
def handler(event, context):
  # Extracting and validating input
  if 'mock' in event and event['mock'] == True:
    return {
      "status": "SUCCESS",
      "response": "mocked"
    }

  # Get the service resource.
  sns = boto3.client('sns')
  # Get the event system
  event_system = sns.meta.events

  # Put values in params dict
  def param_injector(params, **kwargs):
    params["TopicArn"] = event["topic_arn"]
  event_system.register('provide-client-params.sns.DeleteTopic', param_injector)

  try:
    # Perform operation
    response = sns.delete_topic()

    # Delete irrelevant info
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