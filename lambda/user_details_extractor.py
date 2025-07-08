import boto3
import json
import os
from datetime import datetime, timezone
import openai
import re


# Initialize AWS clients
textract = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')  # Added for SNS publishing

# Retrieve API key and table names from environment variables
openai.api_key = os.environ['OPENAI_API_KEY']
applicant_details_table = os.environ['APPLICANT_DETAILS_TABLE']
user_embeddings_table = os.environ['USER_EMBEDDINGS_TABLE']
user_match_topic_arn = os.environ['USER_MATCH_TOPIC_ARN']  # Added for triggering immediate match

# Helper function to extract text from a block
def get_text(block, block_map):
    if 'Relationships' not in block:
        return ''
    texts = []
    for rel in block['Relationships']:
        if rel['Type'] == 'CHILD':
            for cid in rel['Ids']:
                word = block_map.get(cid)
                if word and word['BlockType'] == 'WORD':
                    texts.append(word['Text'])
    return ' '.join(texts)

def extract_key_value_pairs(key_map, value_map, block_map):
    kvs = {}
    for key_id, key_block in key_map.items():
        value_block = None
        if 'Relationships' in key_block:
            for rel in key_block['Relationships']:
                if rel['Type'] == 'VALUE':
                    for val_id in rel['Ids']:
                        value_block = value_map.get(val_id)
                        if value_block:
                            key_text = get_text(key_block, block_map)
                            val_text = get_text(value_block, block_map)
                            kvs[key_text] = val_text
    return kvs

def get_openai_embedding(text):
    try:
        response = openai.Embedding.create(model="text-embedding-ada-002", input=text)
        return response['data'][0]['embedding']
    except Exception as e:
        print(f"Error in OpenAI embedding: {e}")
        return None

def extract_resume_details(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a resume parser. Extract name, email, phone, skills, and education. Return a JSON object."},
                {"role": "user", "content": text}
            ],
            max_tokens=500
        )
        raw_content = response.choices[0].message['content']

        # Remove markdown code block wrapper if present
        cleaned_content = re.sub(r'^```json\s*|\s*```$', '', raw_content.strip(), flags=re.MULTILINE)

        # Now parse JSON
        result = json.loads(cleaned_content)
        return result
    except Exception as e:
        print(f"Error in OpenAI chat completion: {e}")
        return {"name": "Unknown", "email": "No email", "phone": "No phone", "skills": "Unknown", "education": "Not mentioned"}

def lambda_handler(event, context):
    message = json.loads(event['Records'][0]['Sns']['Message'])
    job_id = message['jobId']
    user_id = message.get('userId', 'unknown')
    print(f"Processing job {job_id}")
    print(f"User ID: {user_id}")   
    # Fetch Textract results
    response = textract.get_document_analysis(JobId=job_id)
    print(f"Textract results fetched {response}")
    blocks = response['Blocks']

    # Map blocks for key-value extraction
    key_map = {}
    value_map = {}
    block_map = {}

    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block
        if block['BlockType'] == 'KEY_VALUE_SET':
            if 'KEY' in block['EntityTypes']:
                key_map[block_id] = block
            else:
                value_map[block_id] = block

    kvs = extract_key_value_pairs(key_map, value_map, block_map)
    print(f"Key-value pairs extracted {kvs}")
    # Prepare text for OpenAI processing
    all_text = ' '.join(block['Text'] for block in blocks if block['BlockType'] == 'WORD' and 'Text' in block)

    print(f"All text: {all_text}")

    # Get embedding and extract details
    # embedding = get_openai_embedding(all_text)

    # print(f"Embedding: {embedding}")

    resume_details = extract_resume_details(all_text)
    # Use skills text for embedding if available, otherwise fall back to all text
    skills_text = resume_details.get('skills', all_text)
    skills_embedding = get_openai_embedding(skills_text) 
    print(f"Resume details: {resume_details}")

    # Prepare user item for applicant details (excluding embeddings)
    applicant_item = {
        'user_id': user_id,
        'upload_timestamp': datetime.now(timezone.utc).isoformat(),
        'name': kvs.get('Name', resume_details.get('name', 'Unknown')),
        'email': kvs.get('Email', resume_details.get('email', 'No email')),
        'phone': kvs.get('Phone', resume_details.get('phone', 'No phone')),
        'skills': kvs.get('Skills', resume_details.get('skills', 'Unknown')),
        'education': kvs.get('Education', resume_details.get('education', 'Not mentioned'))
    }
    
    # Save to DynamoDB applicant details table
    applicant_table = dynamodb.Table(applicant_details_table)
    try:
        applicant_table.put_item(Item=applicant_item)
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Applicant Details save failed', 'details': str(e)})
        }

    # Save embedding to user embeddings table if available
    if skills_embedding:
        embedding_item = {
            'user_id': user_id,
            'embedding': str(skills_embedding)
        }
        embeddings_table = dynamodb.Table(user_embeddings_table)
        try:
            embeddings_table.put_item(Item=embedding_item)
        except Exception as e:
            # Continue even if embedding save fails, as it's secondary
            pass
    
    # Trigger immediate user match after successful embedding save
    try:
        sns.publish(
            TopicArn=user_match_topic_arn,
            Message=json.dumps({'user_id': user_id})
        )
        print(f"Triggered immediate match for user_id: {user_id}")
    except Exception as e:
        print(f"Error triggering immediate match: {e}")
        # Continue even if SNS fails, as it's non-critical

    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'stored', 'resume_details': resume_details})
    }