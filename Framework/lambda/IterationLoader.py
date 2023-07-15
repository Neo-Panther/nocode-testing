from typing import Any
import boto3
import time

"""
  INFO: Loads the next iteration from the iteration list, also removing it from the list to eliminate redundancy. Parallel Processing starts after this Lambda.

  ? denotes info
  Input Format:
  event = {
    "test_group_id": "<Id of this test group>",
    "iterations": [<list of iterations to do>]
  }
  
  Output Format:
  {
    "completed": <true|false>,
    ? end iteration on true
    "tests": [<list of tests to run in parallel>],
    ? each individual test is a list of steps for that test
    "iterations": [<list of remaining iterations>]
    ? input minus the first iteration (except when it was already empty)
  }
"""

def handler(event, context):
  iterations: list[list[Any]] = event["iterations"]
  # Get the service resource.
  ddb = boto3.resource('dynamodb')
  # Get the log table
  table = ddb.Table(event["log_table_name"])
  if not len(iterations):
    return {
      "completed": True,
      "tests": None,
      "iterations": None
    }
  iteration = iterations.pop(0)
  
  # Create Log item
  item = {
    "TestGroupID": event["test_group_id"],
    "TestScenarioID": 'T<Started>:S<'+ str(len(iterations)) +'>',
    "Status": "START",
    "Input": "Remaining Iterations: " + str(len(iterations)),
    "Output": "Iteration Started",
    "Timestamp": time.strftime("%DT%H:%M:%S", time.localtime())
  }
  # Put log in table
  response = table.put_item(Item=item)

  return {
    "completed": False,
    "tests": iteration,
    "iterations": iterations
  }