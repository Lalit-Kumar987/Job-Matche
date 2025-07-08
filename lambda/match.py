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
applicant_table = dynamodb.Table(os.environ['APPLICANT_DETAILS_TABLE'])
match_table = dynamodb.Table(os.environ['MATCH_RESULTS_TABLE'])
job_table = dynamodb.Table(os.environ['JOB_POSTINGS_TABLE'])
applicant_embeddings = dynamodb.Table(os.environ['APPLICANT_EMBEDDING_TABLE'])
user_topics_table = dynamodb.Table(os.environ['USER_TOPICS_TABLE'])
sns = boto3.client('sns')

def lambda_handler(event, context):
    try:
        print("Starting matching process at:", time.ctime())

        # Define time window for recent jobs (last 24 hours)
        threshold_time = int((datetime.now(timezone.utc) - timedelta(hours=24)).timestamp())

       # Fetch all user embeddings
        users = applicant_table.scan()['Items']
        user_embeddings = {}
        for user in users:
            user_id = user['user_id']
            embedding_response = applicant_embeddings.scan(
                FilterExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id}
            )
            items = embedding_response['Items']
            if items and 'embedding' in items[0]:
                user_embeddings[user_id] = np.array(json.loads(items[0]['embedding']))

        # print(user_embeddings)
        # Fetch recently fetched jobs
        jobs = job_table.scan(
            FilterExpression='posted_timestamp >= :threshold',
            ExpressionAttributeValues={':threshold': threshold_time}
        )['Items']
        # print(jobs)

        matches = []
        user_matches = {}  # Dictionary to aggregate matches by user_id
        for job in jobs:
            print("job:", 0)
            job_embedding = np.array(json.loads(job['embedding'])) if job.get('embedding') else None
            print("job_embedding:", 1)
            if job_embedding is None or len(job_embedding) == 0:
                continue  # Skip jobs without valid embeddings
            print("user_embedding:", user_embeddings)
            for user_id, user_embedding in user_embeddings.items():
                if user_embedding is not None and len(user_embedding) > 0:  # Check for valid embedding
                    print("user_embedding:", user_embedding)
                    print("job_embedding:", job_embedding)
                    similarity = 1 - distance.cosine(np.ravel(user_embedding), np.ravel(job_embedding))
                    if similarity > 0.7:  # Threshold for match
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
                        if user_id not in user_matches:
                            user_matches[user_id] = []
                        user_matches[user_id].append({
                            'job_id': job['job_id'],
                            'job_title': job.get('job_title', 'Unknown'),
                            'location': job.get('location', 'Unknown'),
                            'similarity_score': Decimal(str(similarity)),  # Convert to string for email
                            'employment_type': job['employment_type'],
                            'is_remote': job.get('is_remote', False),
                            'posted_at': job.get('posted_at','N/A')
                        })

        # Store matches in DynamoDB
        for match in matches:
            match_table.put_item(Item=match)
            print(f"Matched {match['user_id']} with {match['job_id']} (Score: {match['similarity_score']})")

        # Send email notifications for each user
        for user_id, jobs_list in user_matches.items():
            # Fetch the user's topic ARN
            topic_response = user_topics_table.get_item(Key={'user_id': user_id})
            if 'Item' in topic_response and 'topic_arn' in topic_response['Item']:
                topic_arn = topic_response['Item']['topic_arn']
                # Prepare email message
                message = {
                    'default': json.dumps({
                        'user_id': user_id,
                        'message': f"New job matches found:\n" + "\n".join(
                            [f"- {job['job_title']} ({job['location']}) - Similarity: {job['similarity_score']}" for job in jobs_list]
                        )
                    }),
                    'email': f"Subject: New Job Matches for {user_id}\n\nDear User,\n\nThe following job matches were found based on your resume:\n" + "\n".join(
                        [f"- {job['job_title']} ({job['location']}) - Similarity: {job['similarity_score']}" for job in jobs_list]
                    ) + "\n\nBest,\nResume Matcher Team"
                }
                sns.publish(
                    TopicArn=topic_arn,
                    Message=json.dumps(message),
                    MessageStructure='json'
                )
                print(f"Sent email notification to {user_id} with {len(jobs_list)} jobs")
            else:
                print(f"No topic found for user_id: {user_id}")

        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'matching_complete', 'match_count': len(matches)})
        }

    except Exception as e:
        print(f"Error in matching: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }