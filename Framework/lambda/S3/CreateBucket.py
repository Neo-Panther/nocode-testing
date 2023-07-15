import boto3, os

"""
  Input Format: ! denotes optional item
  ? denotes info
  event = {
    "bucket_name": "<Your Bucket Name>",
    !"bucket_location": "<The region code where to create the bucket>"
    ? If not defined, the lambdas' region is used (eg. "us-east-1")
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
  # Find lambdas' location
  loc = os.environ["AWS_REGION"]
  if "bucket_location" in event:
    loc = event["bucket_location"]

  try:
    # Create the S3 Bucket (1 location has different command - That is some lazy(?) coding).
    if loc == 'us-east-1':
      response = s3.create_bucket(Bucket=event["bucket_name"])
    else:
      response = s3.create_bucket(Bucket=event["bucket_name"], CreateBucketConfiguration={"LocationConstraint": loc})
    
    # Delete irrelevant info
    response.pop("ResponseMetadata")
  except Exception as e:
    return {
      "status": "FAILED",
      "message": "Error: " + str(type(e).__name__) + " - "+ str(e)
    }
  return {
      "status": "SUCCESS",
      "response": response
    }



