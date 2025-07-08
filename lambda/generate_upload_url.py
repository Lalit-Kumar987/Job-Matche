import boto3
import json
from botocore.exceptions import ClientError

s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Extract user_id from Cognito authorizer claims
    claims = event.get('claims', {})
    user_id = claims.get('sub', 'unknown_user')
    print(f"Generating upload URL for user: {user_id}")
    
    bucket = "resume-input-dev"  # Replace with dynamic value if needed
    print(f"User ID: {user_id}")
    # Extract file name from the request body
    body = event.get('body', '')
    if body:
        body = json.loads(body) if isinstance(body, str) else body
    else:
        body = {}
    print(f"Body: {body}")
    file_name = body.get('fileName')
    file_type = body.get('fileType')

    if not file_name:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing fileName in request body'})
        }

    # Create a unique file key (e.g., userId/filename)
    file_key = f"{user_id}/{file_name}"

    print(f"File Key: {file_key}")
    try:
        url = s3.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': bucket,
                'Key': file_key,
                'Metadata': {'user-id': user_id},
                'ContentType': file_type
            },
            ExpiresIn=3600  # URL valid for 1 hour
        )
        print(f"Presigned URL: {url}")
        return {
            'statusCode': 200,
            'body': json.dumps({'uploadUrl': str(url), 'key': str(file_key), 'userId': str(user_id)})
        }
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }