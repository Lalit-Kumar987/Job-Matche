import boto3
import json
import os
from botocore.exceptions import ClientError

# Initialize AWS clients
sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')
user_topics_table = dynamodb.Table(os.environ['BOOKING_TABLE'])

def lambda_handler(event, context):
    try:
        # Extract user_id from Cognito authorizer claims
        claims = event.get('claims', {})
        user_id = claims.get('sub', 'unknown_user')
        print(f"Generating upload URL for user: {user_id}")

        body = event.get('body', '')
        if body:
            body = json.loads(body) if isinstance(body, str) else body
        else:
            body = {}
        email = body.get('email')
        print(f"Processing sign-in for user_id: {user_id}, email: {email}")

        # Check if topic exists in DynamoDB
        response = user_topics_table.get_item(Key={'user_id': user_id})
        if 'Item' not in response:
            # Create a new SNS topic
            topic_name = f"user-{user_id}"
            topic_response = sns.create_topic(Name=topic_name)
            topic_arn = topic_response['TopicArn']
            print(f"Created new topic: {topic_arn}")

            # Subscribe the user's email to the topic
            subscription_response = sns.subscribe(
                TopicArn=topic_arn,
                Protocol='email',
                Endpoint=email
            )
            print(f"Subscription requested: {subscription_response['SubscriptionArn']}")

            # Store topic ARN in DynamoDB
            user_topics_table.put_item(Item={
                'user_id': user_id,
                'topic_arn': topic_arn,
                'email': email
            })
        else:
            print(f"Topic already exists for user_id: {user_id}")

        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'subscription_initiated'})
        }

    except ClientError as e:
        print(f"AWS Client Error: {e}")
        return event  # Continue Cognito flow even if error occurs
    except Exception as e:
        print(f"Error: {e}")
        return event  # Continue Cognito flow even if error occurs