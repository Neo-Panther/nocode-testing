import boto3
import time

"""
  INFO: Logs the input and result of the operation of a test step in the log table.

  Input Format: ! denotes optional item
  ? denotes info
  event = {
    "log_table_name": "<DDB Logging Table Name>",
    "test_group_id": "<Current Test Group/Use Case ID>",
    "Payload": {
      "test": {<The input sent to test/validation lambda>},
      "test_scenario_id": "<Test Scenario ID>",
      "type": "<Test/validation type>"
    },
    "testResult": {
      "Payload": {
        "status": "<FAILED|SUCCESS>",
        !"response": "<Output of process on success>"
        !"message": "<The service error>"
        ? The function will work even if both are missing
      },
      ? rest of the items are ignored
    }
  }

  Because we are logging in both logger and finisher, I have discarded map states output
  Output Format: null
"""
def handler(event, context):
  # Get the service resource.
  ddb = boto3.resource('dynamodb')
  # Get the log table
  table = ddb.Table(event["log_table_name"])

  # Create Log Item
  inp=event["Payload"]
  output=event.pop("testResult")["Payload"]
  status=output.pop("status", "FAILED")
  item = {
    "TestGroupID": event["test_group_id"],
    "TestScenarioID": inp["test_scenario_id"],
    "Status": status,
    "Input": inp,
    "Output": output,
    "Timestamp": time.strftime("%DT%H:%M:%S", time.localtime())
  }

  # Put log item in log table
  response = table.put_item(Item=item)