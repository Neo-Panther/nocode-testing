import boto3, time, json

"""
  INFO: Used to insert specified minimum waiting time between any two step operations.

  Input Format:  ! denotes optional item
  ? denotes info
  event = {
    "token": "<this task's sfn token>",
    "wait_time": <number wait time in seconds>
    ? Current input range: 0-120
    ? The waiter will at least wait for this time (it is a lower bound, upper bound cannot be fixed)
  }
  
  Output Format:
    {
      "status": "SUCCESS",
      "response": "Wait Complete"
    }
"""

def handler(event, context):
  sfn = boto3.client("stepfunctions")
  time.sleep(float(event["wait_time"]))
  response = sfn.send_task_success(
    taskToken=event["token"],
    output=json.dumps({
      "status": "SUCCESS",
      "response": "Wait Complete"
    })
  )