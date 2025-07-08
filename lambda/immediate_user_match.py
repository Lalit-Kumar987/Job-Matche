import boto3
import json
import os
import time
from datetime import datetime, timezone, timedelta
import numpy as np
from scipy.spatial import distance
from decimal import Decimal

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
match_table = dynamodb.Table(os.environ['MATCH_RESULTS_TABLE'])
job_table = dynamodb.Table(os.environ['JOB_POSTINGS_TABLE'])
applicant_embeddings = dynamodb.Table(os.environ['USER_EMBEDDINGS_TABLE'])

def lambda_handler(event, context):
    try:
        print("Starting immediate user match at:", time.ctime())

        # Extract user_id from SNS message
        user_id = json.loads(event['Records'][0]['Sns']['Message'])['user_id']

        # Define time window for recent jobs (last 24 hours)
        threshold_time = int((datetime.now(timezone.utc) - timedelta(hours=24)).timestamp())

        # Fetch user embedding
        embedding_response = applicant_embeddings.scan(
            FilterExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': user_id}
        )
        items = embedding_response['Items']
        if not items or 'embedding' not in items[0]:
            print(f"No embedding found for user_id: {user_id}")
            return {
                'statusCode': 200,
                'body': json.dumps({'status': 'no_embedding'})
            }
        user_embedding = np.array(json.loads(items[0]['embedding']))

        # Fetch recent jobs
        jobs = job_table.scan(
            FilterExpression='posted_timestamp >= :threshold',
            ExpressionAttributeValues={':threshold': threshold_time}
        )['Items']

        matches = []
        for job in jobs:
            job_embedding = np.array(json.loads(job['embedding'])) if job.get('embedding') else None
            if job_embedding is None or len(job_embedding) == 0:
                continue
            similarity = 1 - distance.cosine(np.ravel(user_embedding), np.ravel(job_embedding))
            if similarity > 0.7:  # Same threshold as match Lambda
                matches.append({
                    'user_id': user_id,
                    'job_id': job['job_id'],
                    'similarity_score': Decimal(str(similarity)),
                    'match_timestamp': int(time.time()),
                    'employment_type': job['employment_type'],
                    'job_title': job.get('job_title','N/A'),
                    'location': job.get('location', 'N/A'),
                    'is_remote': job.get('is_remote', False),
                    'posted_at': job.get('posted_at','N/A')
                })

        # Store matches in DynamoDB
        for match in matches:
            match_table.put_item(Item=match)
            print(f"Matched {match['user_id']} with {match['job_id']} (Score: {match['similarity_score']})")

        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'immediate_match_complete', 'match_count': len(matches)})
        }

    except Exception as e:
        print(f"Error in immediate match: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }