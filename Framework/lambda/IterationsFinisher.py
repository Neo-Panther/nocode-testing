import boto3
import time

"""
  INFO: Called after the iteration list becomes empty. Logs the completion of the test group in the log table.

  Input Format:  ! denotes optional item
  ? denotes info
  event = {
    "test_group_id": "<Id of this test group>",
    "log_table_name": "<Name of table for logging>",
    ? we list the required input here, other data is also saved in the log
  }

  Output Format:
  {
    'status': "SUCCESS",
    'response': "Test Group Execution Completed"
  }
"""
def handler(event, context):
  # Get the service resource.
  ddb = boto3.resource('dynamodb')
  # Get the log table
  table = ddb.Table(event["log_table_name"])

  # Create Log item
  inp=event
  item = {
    "TestGroupID": event["test_group_id"],
    "TestScenarioID": "T<Completed>:S<Completed>",
    "Status": "FINISH",
    "Input": inp,
    "Output": "Test Group Completed Successfully",
    "Timestamp": time.strftime("%DT%H:%M:%S", time.localtime())
  }

  # Perform operation
  response = table.put_item(Item=item)
  return {
    'status': "SUCCESS",
    'response': "Test Group Execution Completed"
  }