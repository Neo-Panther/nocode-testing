from contextlib import suppress
from typing import Any
import boto3
import json, time

"""
  INFO: The first function called by the sfn. Parses the input files and divides the tests in input into iteration lists as per their dependencies. Iteration list is a list of lists of tests where each sublist has tests which run in parallel. Each sublist is hereafter called an iteration.

  Input Format:  ! denotes optional item
  event = {
    "test_group_id": "<Id of this test group>",
    "log_table_name": "<Name of the ddb logging table>"
    "bucket_name": "<Your Bucket Name>",
    "test_group": {
      "<test_name>": [<dependencies>]
    }
    ? check README for more info
  }

  Output Format:
  {
    "iterations": [[<list of tests for ith iteration>],]
  }
"""

def handler(event: dict[str, Any], context):
  # To Log the start of Execution
  # Get the service resource.
  ddb = boto3.resource('dynamodb')
  ddbclient = boto3.client('dynamodb')
  # Get the log table
  table = ddb.Table(event["log_table_name"])

  try:
    # Try getting table info
    table.load()
  except ddbclient.exceptions.ResourceNotFoundException:
    # Create Table since it does not exists
    ddbclient.create_table(
      TableName=event["log_table_name"],
      KeySchema=[
        {
          "AttributeName": "TestGroupID",  
          "KeyType": "HASH"
        },
        {
          "AttributeName": "TestScenarioID",
          "KeyType": "RANGE"
        },
      ],
      AttributeDefinitions=[{
        "AttributeName": "TestGroupID",
        "AttributeType": "S"
      },
      {
        "AttributeName": "TestScenarioID",
        "AttributeType": "S"
      }],
      ProvisionedThroughput={
        "ReadCapacityUnits": 10,
        "WriteCapacityUnits": 10
      }
    )
    time.sleep(20)
    table.load()

  # Get s3 client
  s3 = boto3.client('s3')

  # Sort file names into iteration list for map input, here is the sorting info:
  """
    eg input: test_group = {
      "a_test_without_dependencies.json": [],
      "a_test_with_dependencies.json": ["a_dependent_test.json", "another_dependent_test.json"],
      "a_test_to_fill_space.json": ["*"],
      "a_dependent_test.json": ["second_level_dependency.json"]
    }
    eg output iteration list = [["a_test_without_dependencies.json", "another_dependent_test.json", "second_level_dependency.json"], ["a_dependent_test.json"], ["a_test_with_dependencies.json"], ["a_test_to_fill_space.json"]]

    each subarray is a different iteration (batch for parallel processing), all items in a subarray are run parallely
  """
  testGroup: dict[str, list[str]] = event["test_group"]
  iterationsFilesList: list[list[str]] = [[]]
  end: list[str] = []
  preTestGroup = dict(testGroup)
  for file in preTestGroup:
    for depend in preTestGroup[file]:
      if depend == "*":
        end.append(file)
        testGroup.pop(file)
      elif depend not in testGroup:
        iterationsFilesList[-1].append(depend)

  while(testGroup):
    for file in preTestGroup:
      if not preTestGroup[file]:
        iterationsFilesList[-1].append(file)
        testGroup.pop(file)
    preTestGroup = testGroup
    for file in preTestGroup:
      for depend in preTestGroup[file]:
        if depend not in testGroup:
          testGroup[file].remove(depend)
    iterationsFilesList.append([])
    preTestGroup = dict(testGroup)

  iterationsFilesList.pop(-1)
  if end:
    iterationsFilesList.append(end)
  
  # Create Log item
  item = {
    "TestGroupID": event["test_group_id"],
    "TestScenarioID": 'T<Null>:S<Null>',
    "Status": "START",
    "Input": event,
    "Output": "Input Parsing Finished, Created Iteration List: " + str(iterationsFilesList) + "\n Started Downloading tests from S3 bucket",
    "Timestamp": time.strftime("%DT%H:%M:%S", time.localtime())
  }
  # Put log in table
  response = table.put_item(Item=item)

  # Load the test steps with the same structure in output as in iteration list created above
  output: list[list[dict[str, Any]]] = []
  for iterationFiles in iterationsFilesList:
    output.append([])
    for testFile in iterationFiles:
      # Download the test file > Parse it > Add to iteration
      with open("/tmp/input.json", "wb") as f:
        s3.download_fileobj(event["bucket_name"], testFile, f)
      with open("/tmp/input.json", "r") as f:
        test: dict[Any, Any] = json.load(f)
        output[-1].append({"test_id": testFile,
                           "steps": test["steps"]})
  return {
    "iterations": output
  }
