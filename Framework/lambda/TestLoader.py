from typing import Any
import boto3
import time
"""
  INFO: Loads an individual operation from a list of steps from a test. The appropriate Test or Validation Lambda is called after this step.

  Input Format:  ! denotes optional item
  ? denotes info
  event = {
    "test_id": <int index of the test in the sfn input array>,
    "test_group_id": "<Id of this test group>",
    "steps": [<list of steps to do, empty if test is complete>],
    "step_id": <index of the current step, used in logging>
  }
  
  Output Format:
  {
    "test_scenario_id": "T<test_id>:S<index of step in steps>",
    ? id = "T<test_id>:S-1" when all steps of this step are complete
    "step_id": <index of the current step, used in logging and loading next step>
    ? index = -1 before starting this test
    "type": "<type of test step, used in choose test scenario>",
    "test": {all the data required for this test step}
  }
"""

def handler(event, context):
  output: dict[str, Any] = {}
  steps: list[dict[str, Any]] = event["steps"]
  testID: str = event["test_id"]
  stepID: int = event["step_id"]
  stepID += 1
  # Get the service resource.
  ddb = boto3.resource('dynamodb')
  # Get the log table
  table = ddb.Table(event["log_table_name"])
  if stepID == len(steps):
    output = {
      "test_scenario_id": f'T<{testID}>:S<Completed>',
      "step_id": stepID,
      "type": "Completed",
      "test": None
    }
  else:
    step = steps[stepID]
    
    # Create Log item
    item = {
      "TestGroupID": event["test_group_id"],
      "TestScenarioID": f'T<{testID}>:S<'+ str(len(steps) - stepID - 1) +'>',
      "Status": "START",
      "Input": "Remaining Steps: " + str(len(steps) - stepID - 1),
      "Output": "Iteration Started",
      "Timestamp": time.strftime("%DT%H:%M:%S", time.localtime())
    }
    # Put log in table
    response = table.put_item(Item=item)

    output = {
      "test_scenario_id": f'T<{testID}>:S<{step["operation"]}>',
      "step_id": stepID,
      "type": step["operation"],
      "test": step["input"]
    }
  return output