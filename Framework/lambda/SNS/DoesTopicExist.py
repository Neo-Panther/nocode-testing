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
      !"response": <true|false>
      ? the result of the validation
      !"message": "<The service error>"
    }
"""
def handler(event, context):
  # Get the service resource.
  sns = boto3.client('sns')
  # Get the event system
  event_system = sns.meta.events

  # Put values in params dict
  def param_injector(params, **kwargs):
    params["TopicArn"] = event["topic_arn"]
  event_system.register('provide-client-params.sns.GetTopicAttributes', param_injector)

  try:
    # Perform operation
    response = sns.get_topic_attributes()

    # Delete irrelevant info
    response.pop("ResponseMetadata")
  except sns.exceptions.NotFoundException as e:
    return {
      "status": "SUCCESS",
      "response": False
    }
  except Exception as e:
    print("The Following error occurred during the process:")
    print(e)
    return {
      "status": "FAILED",
      "message": "Error: " + str(type(e).__name__) + " - "+ str(e)
    }
  return {
      "status": "SUCCESS",
      "response": True
    }