import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as task from 'aws-cdk-lib/aws-stepfunctions-tasks';
import { Construct } from 'constructs';

/**
 * This version uses a step function to combine all files,
 * Step 1) Initiate a parsing lambda, which runs in background, parses & processes all config and input files, aggregates them into individual test/validation scenarios, which are uploaded to a fifo sqs queue as messages, after end of all tasks, an empty completed message is sent to the queue
 * Step 2) Recieves a message from the fifo queue, reads its type and returns to the sfn
 * Choice> The type is used to determine which task to execute and the input is forwarded
 * Step 3) The selected task is executed with the given input
 * Step 4) The ouput of the function is sent to a logger state
 * End of Execution> When the completed message is encountered from the queue.
 * > We may stop the execution from the logger state on encountering a critical error
 */

export class FrameworkStack extends cdk.Stack {
  private parserFunc: lambda.Function;
  private stepLoaderFunc: lambda.Function;
  private iterationLoaderFunc: lambda.Function;
  private testFinisherFunc: lambda.Function;
  private iterationsFinisherFunc: lambda.Function;
  private stepLoggerFunc: lambda.Function;
  private stateMachine: sfn.StateMachine;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    /** ------------------ Lambda Handlers Definition ------------------ */

    // Main flow handlers
    this.parserFunc = new lambda.Function(this, "Parser Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      handler: 'Parser.handler',
      code: lambda.Code.fromAsset(`./lambda`),
      description: "Parses the input files, breaks file into test scenarios and sends to q",
      functionName: "ParserFn",
      timeout: cdk.Duration.minutes(1)
    });

    this.iterationLoaderFunc = new lambda.Function(this, "Iteration Loader Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      handler: 'IterationLoader.handler',
      code: lambda.Code.fromAsset(`./lambda`),
      description: "Loads the next iteration from q to sfn",
      functionName: "IterationLoaderFn",
      timeout: cdk.Duration.seconds(5)
    });

    this.stepLoaderFunc = new lambda.Function(this, "Step Loader Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      handler: 'TestLoader.handler',
      code: lambda.Code.fromAsset(`./lambda`),
      description: "Extracts the next step from steps in payload",
      functionName: "TestLoaderFn",
      timeout: cdk.Duration.seconds(5)
    });

    this.stepLoggerFunc = new lambda.Function(this, "Step Logger Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      handler: 'StepLogger.handler',
      timeout: cdk.Duration.seconds(10),
      code: lambda.Code.fromAsset(`./lambda`),
      description: "Logs the result of test/validation",
      functionName: "StepLoggerFn",
    })

    this.testFinisherFunc = new lambda.Function(this, "Test Finisher Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      handler: 'TestFinisher.handler',
      timeout: cdk.Duration.seconds(10),
      code: lambda.Code.fromAsset(`./lambda`),
      description: "Lambda to invoke after all steps of a test are complete, or a failure happens",
      functionName: "TestFinisherFn"
    });

    this.iterationsFinisherFunc = new lambda.Function(this, "Iterations Finisher Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      handler: 'IterationsFinisher.handler',
      timeout: cdk.Duration.seconds(10),
      code: lambda.Code.fromAsset(`./lambda`),
      description: "Lambda to invoke after all iterations of a test group are complete, or a failure happens",
      functionName: "IterationsFinisherFn"
    });
    
    const waiterFunc = new lambda.Function(this, "Waiter Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      handler: 'Waiter.handler',
      code: lambda.Code.fromAsset(`./lambda`),
      description: "Waits for the specified interval",
      functionName: "WaiterFn",
      timeout: cdk.Duration.minutes(3),
    });

    // DDB Test Scenario Lambdas
    const createEntryFunc = new lambda.Function(this, "Create Entry Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/DynamoDB`),
      functionName: "CreateEntryFn",
      handler: "CreateEntry.handler"
    })
    const createTableFunc = new lambda.Function(this, "Create Table Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/DynamoDB`),
      functionName: "CreateTableFn",
      handler: "CreateTable.handler"
    })
    const getEntryFunc = new lambda.Function(this, "Get Entry Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/DynamoDB`),
      functionName: "GetEntryFn",
      handler: "GetEntry.handler"
    })
    const updateEntryFunc = new lambda.Function(this, "Update Entry Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/DynamoDB`),
      functionName: "UpdateEntryFn",
      handler: "UpdateEntry.handler"
    })
    const deleteEntryFunc = new lambda.Function(this, "Delete Entry Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset('./lambda/DynamoDB'),
      functionName: "DeleteEntryFn",
      handler: "deleteEntry.lambda_handler"
    })
    const deleteTableFunc = new lambda.Function(this, "Delete Table Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset('./lambda/DynamoDB'),
      functionName: "DeleteTableFn",
      handler: "deleteTable.lambda_handler"
    })
    const entryExistFunc = new lambda.Function(this, "Does Entry Exist Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset('./lambda/DynamoDB'),
      functionName: "DoesEntryExistFn",
      handler: "doesEntryExist.lambda_handler"
    })
    const tableExistFunc = new lambda.Function(this, "Does table Exist Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset('./lambda/DynamoDB'),
      functionName: "DoesTableExistFn",
      handler: "doesTableExist.lambda_handler"
    })

    // S3 Test Scenarios
    const createBucketFunc = new lambda.Function(this, "Create Bucket Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/S3`),
      functionName: "CreateBucketFn",
      handler: "CreateBucket.handler"
    })
    const createFileFunc = new lambda.Function(this, "Create File Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/S3`),
      functionName: "CreateFileFn",
      handler: "CreateFile.handler"
    })
    const deleteFileFunc = new lambda.Function(this, "Delete File Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/S3`),
      functionName: "DeleteFileFn",
      handler: "DeleteFile.handler"
    })
    const deleteBucketFunc = new lambda.Function(this, "Delete Bucket Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/S3`),
      functionName: "DeleteBucketFn",
      handler: "deleteBucket.lambda_handler"
    })
    const bucketExistFunc = new lambda.Function(this, "Does Bucket Exist Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/S3`),
      functionName: "DoesBucketExistFn",
      handler: "doesBucketExist.lambda_handler"
    })
    const fileExistFunc = new lambda.Function(this, "Does File Exist Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/S3`),
      functionName: "DoesFileExistFn",
      handler: "doesFileExist.lambda_handler"
    })
    const readFileFunc = new lambda.Function(this, "Read File Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/S3`),
      functionName: "ReadFileFn",
      handler: "readFile.lambda_handler"
    })

    // SNS Test Scenarios
    const createTopicFunc = new lambda.Function(this, "Create Topic Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/SNS`),
      functionName: "CreateTopicFn",
      handler: "CreateTopic.handler"
    })
    const publishMessageFunc = new lambda.Function(this, "Publish Message Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/SNS`),
      functionName: "PublishMessageFn",
      handler: "PublishMessage.handler"
    })
    const deleteTopicFunc = new lambda.Function(this, "Delete Topic Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/SNS`),
      functionName: "DeleteTopicFn",
      handler: "DeleteTopic.handler"
    })
    const doesTopicExistFunc = new lambda.Function(this, "Does Topic Exist Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/SNS`),
      functionName: "DoesTopicExistFn",
      handler: "DoesTopicExist.handler"
    })

    //SQS Test Scenarios
    const sendMessageFunc = new lambda.Function(this, "Send Message Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/SQS`),
      functionName: "SendMessageFn",
      handler: "SendMessage.lambda_handler"
    })
    const readMessageFunc = new lambda.Function(this, "Receive Message Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/SQS`),
      functionName: "ReceiveMessageFn",
      handler: "ReadMessage.lambda_handler"
    })
    const deleteMessageFunc = new lambda.Function(this, "Delete Message Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/SQS`),
      functionName: "DeleteMessageFn",
      handler: "DeleteMessage.lambda_handler"
    })
    const doesQueueExistFunc = new lambda.Function(this, "Does Queue Exist Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/SQS`),
      functionName: "DoesQueueExistFn",
      handler: "DoesQueueExist.lambda_handler"
    })
    const createQueueFunc = new lambda.Function(this, "Create Queue Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/SQS`),
      functionName: "CreateQueueFn",
      handler: "CreateQueue.lambda_handler"
    })
    const deleteQueueFunc = new lambda.Function(this, "Delete Queue Function", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset(`./lambda/SQS`),
      functionName: "DeleteQueueFn",
      handler: "DeleteQueue.lambda_handler"
    })

    /** ------------------ Step functions Definition ------------------ */

    // Main Flow States
    const parseJsonSt = new task.LambdaInvoke(this, 'Start Input Parsing', {
      lambdaFunction: this.parserFunc,
      payload: sfn.TaskInput.fromJsonPathAt('$'),
      resultSelector: {
        "iterations.$": "$.Payload.iterations"
      },
      inputPath: '$',
      resultPath: '$.Payload',
      outputPath: '$'
    });

    const loadNextIterationSt = new task.LambdaInvoke(this, "Load Next Iteration", {
      lambdaFunction: this.iterationLoaderFunc,
      payload: sfn.TaskInput.fromObject({
        test_group_id: sfn.JsonPath.stringAt('$.test_group_id'),
        log_table_name: sfn.JsonPath.stringAt('$.log_table_name'),
        iterations: sfn.JsonPath.listAt('$.Payload.iterations')
      }),
      inputPath: '$',
      resultSelector: {
        "completed.$": "$.Payload.completed",
        "tests.$": "$.Payload.tests",
        "iterations.$": "$.Payload.iterations"
      },
      resultPath: '$.Payload',
      outputPath: '$'
    });

    const loadNextStepSt = new task.LambdaInvoke(this, "Load Next Step", {
      lambdaFunction: this.stepLoaderFunc,
      payload: sfn.TaskInput.fromObject({
        test_group_id: sfn.JsonPath.stringAt('$.test_group_id'),
        log_table_name: sfn.JsonPath.stringAt('$.log_table_name'),
        test_id: sfn.JsonPath.numberAt('$.test_id'),
        steps: sfn.JsonPath.listAt('$.steps'),
        step_id: sfn.JsonPath.numberAt('$.Payload.step_id')
      }),
      inputPath: '$',
      resultSelector: {
        "test_scenario_id.$": "$.Payload.test_scenario_id",
        "step_id.$": "$.Payload.step_id",
        "type.$": "$.Payload.type",
        "test.$": "$.Payload.test"
      },
      resultPath: '$.Payload',
      outputPath: '$'
    });

    const logStepResultSt = new task.LambdaInvoke(this, "Log Step Results", {
      lambdaFunction: this.stepLoggerFunc,
      payload: sfn.TaskInput.fromJsonPathAt('$'),
      inputPath: '$',
      resultPath: sfn.JsonPath.DISCARD,
      outputPath: '$'
    }).next(loadNextStepSt);

    const finishTestGroupSt = new task.LambdaInvoke(this, "Finish Test Group Execution", {
      lambdaFunction: this.iterationsFinisherFunc,
      payload: sfn.TaskInput.fromJsonPathAt('$'),
      inputPath: '$',
      resultPath: '$.output',
      outputPath: "$"
    }); 

    const finishTestSt = new task.LambdaInvoke(this, "Finish Test Execution", {
      lambdaFunction: this.testFinisherFunc,
      payload: sfn.TaskInput.fromJsonPathAt('$'),
      inputPath: '$',
      resultPath: '$.output',
      outputPath: "$"
    });

    const waiterSt = new task.LambdaInvoke(this, "Wait X Seconds", {
      lambdaFunction: waiterFunc,
      integrationPattern: sfn.IntegrationPattern.WAIT_FOR_TASK_TOKEN,
      payload: sfn.TaskInput.fromObject({
        token: sfn.JsonPath.taskToken,
        wait_time: sfn.JsonPath.stringAt('$.Payload.test.wait_time')
      }),
      resultPath: "$.testResult.Payload",
      outputPath: "$"
    }).next(logStepResultSt);

    // DDB Test Scenario States
    const createEntrySt = new task.LambdaInvoke(this, "Create Entry Test",{
      lambdaFunction: createEntryFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);
    const createTableSt = new task.LambdaInvoke(this, "Create Table Test",{
      lambdaFunction: createTableFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);
    const getEntrySt = new task.LambdaInvoke(this, "Get Entry Test",{
      lambdaFunction: getEntryFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);
    const updateEntrySt = new task.LambdaInvoke(this, "Update Entry Test",{
      lambdaFunction: updateEntryFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);
    const deleteEntrySt = new task.LambdaInvoke(this, "Delete Entry Test", {
      lambdaFunction: deleteEntryFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt)
    const deleteTableSt = new task.LambdaInvoke(this, "Delete Table Test", {
      lambdaFunction: deleteTableFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt)
    const entryExistSt = new task.LambdaInvoke(this, "Does Entry Exist Test", {
      lambdaFunction: entryExistFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt)
    const tableExistSt = new task.LambdaInvoke(this, "Does Table Exist Test", {
      lambdaFunction: tableExistFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt)

    // S3 Test Scenario States
    const createBucketSt = new task.LambdaInvoke(this, "Create Bucket Test",{
      lambdaFunction: createBucketFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);
    const createFileSt = new task.LambdaInvoke(this, "Create File Test",{
      lambdaFunction: createFileFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);
    const deleteFileSt = new task.LambdaInvoke(this, "Delete File Test",{
      lambdaFunction: deleteFileFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);
    const deleteBucketSt = new task.LambdaInvoke(this, "Delete Bucket Test",{
      lambdaFunction: deleteBucketFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);
    const bucketExistSt = new task.LambdaInvoke(this, "Does Bucket Exist Test",{
      lambdaFunction: bucketExistFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);
    const fileExistSt = new task.LambdaInvoke(this, "Does file Exist Test",{
      lambdaFunction: fileExistFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);
    const readFileSt = new task.LambdaInvoke(this, "Read File Test",{
      lambdaFunction: readFileFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);

    // SNS Test Scenario States
    const createTopicSt = new task.LambdaInvoke(this, "Create Topic Test",{
      lambdaFunction: createTopicFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);
    const deleteTopicSt = new task.LambdaInvoke(this, "Delete Topic Test",{
      lambdaFunction: deleteTopicFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);
    const publishMessageSt = new task.LambdaInvoke(this, "Publish Message Test",{
      lambdaFunction: publishMessageFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);
    const doesTopicExistSt = new task.LambdaInvoke(this, "Does Topic Exist Validation",{
      lambdaFunction: doesTopicExistFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);

    //SQS Test Scenario States
    const sendMessageSt = new task.LambdaInvoke(this, "Send Message Test",{
      lambdaFunction: sendMessageFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);
    const readMessageSt = new task.LambdaInvoke(this, "Receive Message Test",{
      lambdaFunction: readMessageFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);
    const deleteMessageSt = new task.LambdaInvoke(this, "Delete Message Test",{
      lambdaFunction: deleteMessageFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);
    const doesQueueExistSt = new task.LambdaInvoke(this, "Does Queue Exist Test",{
      lambdaFunction: doesQueueExistFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);
    const createQueueSt = new task.LambdaInvoke(this, "Create Queue Test",{
      lambdaFunction: createQueueFunc,
      inputPath: "$.Payload.test",  
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);
    const deleteQueueSt = new task.LambdaInvoke(this, "Delete Queue Test",{
      lambdaFunction: deleteQueueFunc,
      inputPath: "$.Payload.test",
      resultPath: "$.testResult",
      outputPath: "$"
    }).next(logStepResultSt);

    // A pass state to handle unknown operation values
    const unknownOperationSt = new sfn.Pass(this, "Unknown Operation Requested", {
      inputPath: "$",
      resultPath: "$.testResult",
      parameters: {
        "Payload": {
          "status": "FAILED",
          "message.$": "States.Format('Unknown Operation Requested: {}', $.Payload.type)"
        }
      },
      outputPath: "$"
    }).next(logStepResultSt);

    // The choice state
    const chooseOperationSt = new sfn.Choice(this, 'Choose Test Scenario')
    .when(sfn.Condition.stringEquals('$.Payload.type', 'CreateEntry'), createEntrySt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'CreateTable'), createTableSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'GetEntry'), getEntrySt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'UpdateEntry'), updateEntrySt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'DeleteEntry'), deleteEntrySt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'DeleteTable'), deleteTableSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'DoesEntryExist'), entryExistSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'DoesTableExist'), tableExistSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'CreateBucket'), createBucketSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'CreateFile'), createFileSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'DeleteFile'), deleteFileSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'DeleteBucket'), deleteBucketSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'DoesBucketExist'), bucketExistSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'DoesFileExist'), fileExistSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'ReadFile'), readFileSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'CreateTopic'), createTopicSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'DeleteTopic'), deleteTopicSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'DoesTopicExist'), doesTopicExistSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'PublishMessage'), publishMessageSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'SendMessage'), sendMessageSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'ReadMessage'), readMessageSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'DeleteMessage'), deleteMessageSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'DoesQueueExist'), doesQueueExistSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'CreateQueue'), createQueueSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'DeleteQueue'), deleteQueueSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'Wait'), waiterSt)
    .when(sfn.Condition.stringEquals('$.Payload.type', 'Completed'), finishTestSt)
    .otherwise(unknownOperationSt);

    // The Map State Subflow
    const testFlow = loadNextStepSt.next(chooseOperationSt);

    const processIterationSt = new sfn.Map(this, "Process Iterations", {
      inputPath: '$',
      itemsPath: '$.Payload.tests',
      resultPath: sfn.JsonPath.DISCARD,
      maxConcurrency: 39,
      parameters: {
        "test_id.$": "$$.Map.Item.Value.test_id",
        "steps.$": "$$.Map.Item.Value.steps",
        "Payload": {
          "step_id": -1
        },
        "log_table_name.$": "$.log_table_name",
        "test_group_id.$": "$.test_group_id"
      }
    }).iterator(testFlow).next(loadNextIterationSt);

    const areIterationsOverSt = new sfn.Choice(this, "Are Iteraions Over?")
    .when(sfn.Condition.booleanEquals("$.Payload.completed", false), processIterationSt)
    .otherwise(finishTestGroupSt);

    // The State Machine Flow
    const frameworkFlow=parseJsonSt.next(loadNextIterationSt).next(areIterationsOverSt);

    // The state machine
    this.stateMachine = new sfn.StateMachine(this, 'FrameworkStateMachine', {
      definition: frameworkFlow,
      timeout: cdk.Duration.minutes(10),
      stateMachineName: "FrameworkStateMachine"
    });

    /** ------------------ Policy Statement Definition ------------------ */
    // All these roles give full access to each resource, we can fine tune it for specific resources
    const fullSFNState = new iam.PolicyStatement({
      effect:iam.Effect.ALLOW,
      actions:[
        "states:*"
      ],
      resources: [
        "*"
      ]
    });
    const invokeLambda = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions:[
        "lambda:InvokeFunction"
      ],
      resources: [
        "*"
      ]
    });
    const readS3 = new iam.PolicyStatement({
      effect:iam.Effect.ALLOW,
      actions:[
        "s3:Get*",
        "s3:List*"
      ],
      resources: [
        "*"
      ]
    });
    const fullDDB = new iam.PolicyStatement({
      effect:iam.Effect.ALLOW,
      actions:[
        "dynamodb:*",
      ],
      resources: [
        "*"
      ]
    });
    const fullS3 = new iam.PolicyStatement({
      effect:iam.Effect.ALLOW,
      actions:[
        "s3:*"
      ],
      resources: [
        "*"
      ]
    })
    const fullSNS = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions:[
        "sns:*"
      ],
      resources: [
        "*"
      ]
    })
    const fullSQS = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions:[
        "sqs:*"
      ],
      resources: [
        "*"
      ]
    })

    /** ------------------ Lambda Wise Execution Roles Definition ------------------ */
    // DDB Test and Validation Lambdas
    createEntryFunc.addToRolePolicy(fullDDB);
    createTableFunc.addToRolePolicy(fullDDB);
    getEntryFunc.addToRolePolicy(fullDDB);
    updateEntryFunc.addToRolePolicy(fullDDB);
    deleteEntryFunc.addToRolePolicy(fullDDB);
    deleteTableFunc.addToRolePolicy(fullDDB);
    entryExistFunc.addToRolePolicy(fullDDB);
    tableExistFunc.addToRolePolicy(fullDDB);

    // S3 Test and Validation Lambdas
    createBucketFunc.addToRolePolicy(fullS3);
    createFileFunc.addToRolePolicy(fullS3);
    deleteFileFunc.addToRolePolicy(fullS3);
    deleteBucketFunc.addToRolePolicy(fullS3);
    bucketExistFunc.addToRolePolicy(fullS3);
    fileExistFunc.addToRolePolicy(fullS3);
    readFileFunc.addToRolePolicy(fullS3);

    // SNS Test and Validation Lambdas
    createTopicFunc.addToRolePolicy(fullSNS);
    deleteTopicFunc.addToRolePolicy(fullSNS);
    doesTopicExistFunc.addToRolePolicy(fullSNS);
    publishMessageFunc.addToRolePolicy(fullSNS);

    // SQS Test and Validation Lambdas
    sendMessageFunc.addToRolePolicy(fullSQS);
    readMessageFunc.addToRolePolicy(fullSQS);
    deleteMessageFunc.addToRolePolicy(fullSQS);
    doesQueueExistFunc.addToRolePolicy(fullSQS);
    createQueueFunc.addToRolePolicy(fullSQS);
    deleteQueueFunc.addToRolePolicy(fullSQS);
    
    // Main Flow Lambdas
    this.parserFunc.addToRolePolicy(readS3);
    this.parserFunc.addToRolePolicy(fullDDB);
    this.stepLoaderFunc.addToRolePolicy(fullDDB);
    this.iterationLoaderFunc.addToRolePolicy(fullDDB);
    this.stepLoggerFunc.addToRolePolicy(fullDDB);
    this.testFinisherFunc.addToRolePolicy(fullDDB);
    this.iterationsFinisherFunc.addToRolePolicy(fullDDB);
    waiterFunc.addToRolePolicy(fullSFNState);

    /** ------------------ Main SFN Execution Role Definition ------------------ */
    this.stateMachine.addToRolePolicy(invokeLambda);
  }
}
