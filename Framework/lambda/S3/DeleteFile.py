import boto3

"""
  Input Format: ! denotes optional item
  ? denotes info
  event = {
    "bucket_name": "<Your Bucket Name>",
    "file_name": "<Your File Name>",
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
  
  # Get the service client.
  s3 = boto3.client("s3")
  # Put in contents a temp file

  try:
    response = s3.delete_object(Bucket=event["bucket_name"], Key=event["file_name"])
  except Exception as e:
    return {
      "status": "FAILED",
      "message": "Error: " + str(type(e).__name__) + " - "+ str(e)
    }
  return {
      "status": "SUCCESS",
      "response": response
    }
