import boto3
import json
import requests
import os
import time
from botocore.exceptions import ClientError
from decimal import Decimal
import openai

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['JOB_POSTINGS_TABLE'])
sns = boto3.client('sns')

# Retrieve API key from environment variable
openai.api_key = os.environ['OPENAI_API_KEY']

def get_openai_embedding(texts):
    try:
        # Batch all texts into a single API call
        response = openai.Embedding.create(model="text-embedding-ada-002", input=texts)
        return [data['embedding'] for data in response['data']]
    except Exception as e:
        print(f"Error in OpenAI embedding: {e}")
        return [None] * len(texts)  # Return None embeddings for failed calls

def lambda_handler(event, context):
    try:
        print("Starting API requests at:", time.ctime())

        # Get queries from event or use broad default search
        job_queries = event.get('job_queries')
        if not job_queries:
            job_queries = [
                {"job_title": "developer", "location": "new york"},
                {"job_title": "software engineer", "location": "remote"}
            ]

        all_job_data = []
        num_pages = int(event.get('num_pages', 1))  # Default to 1 page for testing

        for query in job_queries:
            job_descriptions = []
            job_items = []
            for page in range(1, num_pages + 1):
                url = "https://jsearch.p.rapidapi.com/search"
                querystring = {
                    "query": f"{query['job_title']} {query['location']}",
                    "page": str(page),
                    "num_pages": "1"  # 1 page at a time
                }
                headers = {
                    "X-RapidAPI-Key": "730a07317fmsh9e75a7045abb786p14566fjsncc5584ddd7e6",  # Replace if expired
                    "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
                }

                response = requests.get(url, headers=headers, params=querystring)
                response.raise_for_status()
                job_data = response.json()

                print(f"API Response - Page {page} for {query['job_title']} in {query['location']}:")
                print(json.dumps(job_data))

                for idx, job in enumerate(job_data.get('data', []), start=1):
                    timestamp = int(time.time())
                    job_id = f"JOB-{page}-{idx}-{timestamp}-{query['job_title'].replace(' ', '-')}"
                    item = {
                        'job_id': job_id,
                        'job_title': job.get('job_title', 'Unknown'),
                        'location': job.get('job_location', query['location']),
                        'median_salary': Decimal(str(job.get('salary_median', 0))),
                        'min_salary': Decimal(str(job.get('salary_min', 0))),
                        'max_salary': Decimal(str(job.get('salary_max', 0))),
                        'description': job.get('job_description', f"Job posting for {job.get('job_title', 'Unknown')} in {job.get('job_location', query['location'])}"),
                        'employment_type': job.get('job_employment_type', 'Unknown'),
                        'is_remote': bool(job.get('job_is_remote', False)),
                        'posted_at': job.get('job_posted_at_datetime_utc', 'Unknown'),
                        'benefits': job.get('job_benefits', 'Not specified'),
                        'apply_link': job.get('job_apply_link', 'No apply link available'),
                        'highlights': job.get('job_highlights', {'Qualifications': [], 'Responsibilities': [], 'Benefits': []}),
                        'posted_timestamp': int(job.get('job_posted_at_timestamp') or timestamp),
                        'apply_options': job.get('apply_options', [])
                    }
                    job_items.append(item)
                    job_descriptions.append(item['description'])
                    print(f"Prepared job: {job_id} - {item['job_title']} in {item['location']}")

                # Batch embed job descriptions for this page
                embeddings = get_openai_embedding(job_descriptions)
                for item, embedding in zip(job_items, embeddings):
                    if embedding:
                        item['embedding'] = str(embedding)  # Store as string for DynamoDB
                    table.put_item(Item=item)
                    print(f"Inserted job with embedding: {item['job_id']} - {item['job_title']}")

                all_job_data.append(job_data)

                # Publish to MatchUpdateTopic to trigger match Lambda
                sns.publish(
                    TopicArn=os.environ['MATCH_UPDATE_TOPIC_ARN'],
                    Message=json.dumps({'status': 'jobs_fetched', 'page': page, 'query': query})
                )
                print(f"Published to MatchUpdateTopic for page {page}")

                # Rate limit safety
                time.sleep(1)

        return {
            'statusCode': 200,
            'body': json.dumps('Job data stored in DynamoDB successfully'),
            'job_data': all_job_data
        }

    except ClientError as e:
        print(f"AWS Client Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"AWS Client Error: {str(e)}")
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }