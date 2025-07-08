import boto3
import json
import os
from botocore.exceptions import ClientError

# Initialize AWS client
dynamodb = boto3.resource('dynamodb')
match_table = dynamodb.Table(os.environ['MATCH_RESULTS_TABLE'])

def lambda_handler(event, context):
    try:
        # Extract user_id from Cognito claims
        user_id = event['claims']['sub']  # Using 'sub' as the unique user identifier from Cognito

        # Query match_results table for the user
        response = match_table.query(
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id}
        )
        print(f"Query response: {response}")
        # Prepare response with match details
        matches = response.get('Items', [])
        formatted_matches = [
            {
                'job_id': item['job_id'],
                'similarity_score': float(item['similarity_score']),
                'match_timestamp': int(item['match_timestamp']) if 'match_timestamp' in item else 0,
                'employment_type': item.get('employment_type','N/A'),
                'job_title': item.get('job_title','N/A'),
                'location': item.get('location', 'N/A'),
                'is_remote': item.get('is_remote', False),
                'posted_at': item.get('posted_at','N/A')
            } for item in matches
        ]

        return {
            'statusCode': 200,
            'body': json.dumps({'matches': formatted_matches})
        }

    except ClientError as e:
        print(f"AWS Client Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid request', 'details': str(e)})
        }