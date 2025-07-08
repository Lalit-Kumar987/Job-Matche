import boto3
import json
import os
import time
from botocore.exceptions import ClientError

s3 = boto3.client('s3')
textract = boto3.client('textract')
sns = boto3.client('sns')

def lambda_handler(event, context):
    print(event)
    message = json.loads(event['Records'][0]['Sns']['Message'])
    job_id = message['jobId']
    user_id = message.get('userId', 'unknown')  # Extract user_id from message
    
    max_attempts = 10
    print(job_id)
    for attempt in range(max_attempts):
        response = textract.get_document_analysis(JobId=job_id)
        status = response['JobStatus']
        print(f"Job {job_id} status: {status}")
        
        if status in ['SUCCEEDED', 'FAILED']:
            break
        time.sleep(5)  # Poll every 5 seconds
        
    if status == 'SUCCEEDED':
        blocks = response['Blocks']
        while 'NextToken' in response:
            response = textract.get_document_analysis(JobId=job_id, NextToken=response['NextToken'])
            blocks.extend(response['Blocks'])
        
        sns.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Message=json.dumps({'jobId': job_id, 'userId': user_id})
        )
        print("Published to ResumeProcessingTopic")
    else:
        print(f"Job {job_id} failed")
        
    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'triggered'})
    }