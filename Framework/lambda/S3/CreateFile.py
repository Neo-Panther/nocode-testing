import boto3, json

"""
  Input Format: ! denotes optional item
  ? denotes info
  event = {
    "bucket_name": "<Your Bucket Name>",
    "file_name": "<Your File Name (to be used in the s3 bucket)>",
    "file_contents": <json file contents as a json object>,
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
  with open("/tmp/temp.json", "w") as f:
    json.dump(event["file_contents"], f)

  try:
    response = None
    # Upload the file
    with open("/tmp/temp.json", "rb") as f:
      response = s3.upload_fileobj(f, event["bucket_name"], event["file_name"])
    
  except Exception as e:
    return {
      "status": "FAILED",
      "message": "Error: " + str(type(e).__name__) + " - "+ str(e)
    }
  return {
      "status": "SUCCESS",
      "response": response
    }



