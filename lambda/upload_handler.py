import boto3
import json
import os

s3 = boto3.client('s3')
textract = boto3.client('textract')
sns = boto3.client('sns')

def lambda_handler(event, context):
    print(event)
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    response = s3.head_object(Bucket=bucket, Key=key)
    user_id = response['Metadata'].get('user-id', 'unknown')

    print(bucket)
    print(key)
    response = textract.start_document_analysis(
        DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': key}},
        FeatureTypes=['FORMS']
    )
    job_id = response['JobId']
    print(response)

    sns.publish(
        TopicArn=os.environ['TEXTRACT_JOB_TOPIC_ARN'],
        Message=json.dumps({'jobId': job_id, 'userId': user_id})
    )

    return {
        'statusCode': 200,
        'body': json.dumps({'jobId': response['JobId'], 'userId': user_id})
    }