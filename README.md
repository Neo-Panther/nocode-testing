# nocode-testing

This is a Integration Test Framework which allows developers/users to run their integration test based on json config files.

## To Deploy
Open the Framework folder in terminal

Ensure aws-cdk is installed and [bootstrapped](https://docs.aws.amazon.com/cdk/latest/guide/bootstrapping.html)

```
$ npm install -g aws-cdk
$ cdk bootstrap
```

Build, Synth and Deploy
```
$ npm run build
$ cdk synth
$ cdk deploy
```


## Logging
The logging table is a ddb table with the following primary key structure:
```
"key": {
  "hash_key": {
    ? provided as input to sfn
    "name": "TestGroupID",
    "type": "S"
  },
  "sort_key": {
    ? generated as "T<<file name in input>>:S<<operation>>", <> is included
    "name": "TestScenarioID",
    "type": "S"
  }
}
```
The table is in PROVISIONED mode
other attributes:
```
"Status": <"SUCCESS" for execution without error| "FAILED" if an error was encountered>,
"Input": <the object sent as input to the operation (test step)>
"Output": <the object given as output of the operation (test step)>
"Timestamp": <the timestamp (based on the lambda's environment) of the completion of operation (as a string, format: "Month/Date/Year T Hour:Minute:Second" (all as 2 digit numbers))>
```

Log entries are created at the following points in the execution of the framework (in order):
1. After the creation of the iteraion list and before the download of input tests from s3 (the iteration list is logged)
2. Before the start of every iteration (number of remaining iterations logged)
3. Before execution of each step operation (remaining number of steps is logged, excluding the current step)
4. After the execution of each step (its inpjut and output is logged)
5. After the finish of a test (all steps complete)
6. After the finish of the test group (all iterations complete)

## The Input

### State Machine Input
This input is sent to start the execution of the state machine
(? denotes info)
```
{
  "bucket_name": "<Bucket with all input files>",
  "log_table_name": "<DDB Logging Table Name>",
  ? will be created if no such table exists
  "test_group_id": "<Current Test Group/Use Case ID>",
  "test_group": {
    "<test_name>": ["<dependency test list>"]
    ? the tests in the dependency list will run BEFORE the test they are attached with.
    ? a test will run in the immediate next iteration once all its dependencies have finished execution
    ? tests mentioned in the dependency lists need not be mentioned separately in the test group.
    ? if the tests have dependencies of their own, they must be added in the above format
    ? giving "*" as a dependency makes the respective test run in the last iteration
    ? circular dependencies are not supported
  },
  ? any other items are ignored by the state machine, but logged in the db
}
```
In the absence of dependencies, framework will maximise parallel test execution

### Input Files
An input file is a json file representing 1 test with following format:
```
{
  ? any other items are ignored by the framework
  "steps": [
    {
      "operation": "<The operation performed in this step>"
      ? must be one of ths specified lambdas
      "input": {
        ? The input required for the operation, check individual lambdas for required info
      }
    },
    ? Each list item is a json object with all info for 1 test/validation scenario (step)
  ]
}
The responsibility of clean up of resources used in the test_group falls to the user (more tests for cleanup may be assigned to the test group)
```

### Input Assumptions
These restrictions are placed on the input, the execution will fail or produce incorrect results if these are not followed. The framework will not verify the input for these.
1. The input provided is in the correct format and has all required information for the test
2. In the case of parallel runs, each run will have tests with mutually exclusive resources modified, althoud read may be done on the same resource

## Sample Input
Input to sfn for the sample test in this version (give "*" as dependency, to run a test at the end):
{
  "bucket_name": "testingframeworkbucket",
  "log_table_name": "test_log_table",
  "test_group_id": "finalsnow",
  "test_group": {
    "badtask.json": [],
    "ddbtest.json": ["s3test.json"]
  },
  "Comment": "..."
}

## TASKS LEFT:
1. Creation of API Endpoints for the framework