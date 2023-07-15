import boto3

"""
  Input Format: ! denotes optional item
  ? denotes info
  event = {
    ? at least one of "topic_arn" or "target_arn" must be defined
    "topic_arn": "<Your Topic ARN>",
    "target_arn": "<Your Target ARN>",
    !"message_structure": "json",
    ? json (only valid value) means you will provide different string message values to different endpoint (eg. "http") keys. "default" key and its value is mandatory ()
    "message": "<String for text message and json string for json>",
    !"subject": "<string subject>",
    !"message_deduplication_id"='<string id>',
    ? required for fifo topics with contents based deduplication set to false
    !"message_group_id": "<string id>"
    ? required for all fifo topics
    !"mock": <true|false>
  }

  Output Format:
    {
      "status": "<FAILED|SUCCESS>",
      !"response": "<Output of process on success>"
      !"message": "<The service error>"
    }
"""

def handler(event, context):
  # Mock if needed
  if 'mock' in event and event['mock'] == True:
    return {
      "status": "SUCCESS",
      "response": "mocked"
    }

  # Get the service resource
  sns = boto3.client('sns')
  # Get the event system
  event_system = sns.meta.events

  # Put values in params dict
  def param_injector(params, **kwargs):
    if "target_arn" in event:
      params["TargetArn"] = event["target_arn"]
    elif "topic_arn" in event:
      params["TopicArn"] = event["topic_arn"]
    else:
      params["PhoneNumber"] = event["phone_number"]
    if "message_structure" in event:
      params["MessageStructure"] = "json"
    params["Message"] = event["message"]
    if "subject" in event:
      params["Subject"] = event["subject"]
    if "message_deduplication_id" in event:
      params["MessageDeduplicationId"] = event["message_deduplication_id"]
    if "message_group_id" in event:
      params["MessageGroupId"] = event["message_group_id"]
  event_system.register('provide-client-params.sns.Publish', param_injector)

  try:
    # Perform operation
    response = sns.publish()

    # Delete irrelevant info
    response.pop("ResponseMetadata")
  except Exception as e:
    print("The Following error occurred while creating the entity:")
    print(e)
    return {
      "status": "FAILED",
      "message": "Error: " + str(type(e).__name__) + " - "+ str(e)
    }
  return {
      "status": "SUCCESS",
      "response": response
    }
