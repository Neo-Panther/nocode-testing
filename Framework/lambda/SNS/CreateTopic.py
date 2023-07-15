import boto3

"""
  Input Format: ! denotes optional item
  ? denotes info
  event = {
    "topic_name": "<Your Topic Name>",
    !"fifo": <true|false>,
    !"content_based_deduplication": <true|false> ? used only when "fifo" is true, default true, "message_deduplication id" must be provided with each message if false,
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
  
  # Get the service resource.
  sns = boto3.client('sns')
  # Get the event system
  event_system = sns.meta.events

  # Put values in params dict
  def param_injector(params, **kwargs):
    topicName = event["topic_name"]
    attributes = {"DisplayName":event["topic_name"]}
    if "fifo" in event and event["fifo"] == True:
      topicName += ".fifo"
      attributes["FifoTopic"] = "true"
      attributes["ContentBasedDeduplication"] = "true"
    if "content_based_deduplication" in event and event["content_based_deduplication"] == False:
      attributes["ContentBasedDeduplication"] = "false"
    params["Attributes"] = attributes
    params["Name"] = topicName
  event_system.register('provide-client-params.sns.CreateTopic', param_injector)

  try:
    # Perform operation
    response = sns.create_topic()

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