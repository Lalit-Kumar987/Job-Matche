import boto3
import json
import os
from botocore.exceptions import ClientError
from decimal import Decimal

# Initialize AWS client
dynamodb = boto3.resource('dynamodb')
job_table = dynamodb.Table(os.environ['JOB_POSTINGS_TABLE'])

def lambda_handler(event, context):
    try:
        # Extract job_id from the request body
        print(event)
        body = event.get('body', '')
        if body:
            body = json.loads(body) if isinstance(body, str) else body
        else:
            body = {}
        
        job_id = body.get('job_id')
        if not job_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing job_id in request body'})
            }
        print(job_id)
        # Fetch job details from job_postings table
        response = job_table.get_item(
            Key={'job_id': job_id}
        )
        job = response.get('Item')

        if not job:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Job not found'})
            }
        print(job)
        # Pre-convert all Decimal values to float
        for key, value in job.items():
            if hasattr(value, 'to_integral_value'):  # Check if value is a Decimal
                job[key] = float(value)

        # Prepare response with all fields except embedding
        formatted_job = {key: value for key, value in job.items() if key != 'embedding'}
        # Use original logic for posted_timestamp
        formatted_job['posted_timestamp'] = int(job['posted_timestamp']) if 'posted_timestamp' in job else 0

        return {
            'statusCode': 200,
            'body': json.dumps({'job': formatted_job})
        }

    except ClientError as e:
        print(f"AWS Client Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON in request body', 'details': str(e)})
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid request', 'details': str(e)})
        }