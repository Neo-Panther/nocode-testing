import boto3
import time

"""
  INFO: Called after the test's steps list becomes empty. Logs the completion of the test in the log table.

  Input Format:  ! denotes optional item
  ? denotes info
  event = {
    "test_group_id": "<Id of this test group>",
    "log_table_name": "<Name of table for logging>",
    "test_scenario_id": "<format T<test_id>:S-1>",
    ? index of step = -1 when control reaches here
    ? we list the required input here, other data is also saved in the log
  }

  Output Format:
  {
    'status': "SUCCESS",
    'response': "Test Execution Completed"
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
    "TestScenarioID": event["Payload"]["test_scenario_id"],
    "Status": "FINISH",
    "Input": inp,
    "Output": "Test Completed Successfully",
    "Timestamp": time.strftime("%DT%H:%M:%S", time.localtime())
  }
  # Put log in table
  response = table.put_item(Item=item)
  return {
    'status': "SUCCESS",
    'response': "Test Execution Completed"
  }