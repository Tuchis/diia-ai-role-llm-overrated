# services.py
import boto3
import uuid
import time
from botocore.config import Config
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from config import settings

# --- AWS CLIENTS ---
# We use a specific signature version for Presigned URLs to work correctly
# If credentials are provided in env vars, use them. Otherwise, boto3 will use IAM role.
def _create_s3_client():
    kwargs = {
        'region_name': settings.AWS_REGION,
        'config': Config(signature_version='s3v4')
    }
    # Only pass credentials if they are explicitly provided
    if settings.AWS_ACCESS_KEY_ID:
        kwargs['aws_access_key_id'] = settings.AWS_ACCESS_KEY_ID
        kwargs['aws_secret_access_key'] = settings.AWS_SECRET_ACCESS_KEY
        if settings.AWS_SESSION_TOKEN:
            kwargs['aws_session_token'] = settings.AWS_SESSION_TOKEN
    return boto3.client('s3', **kwargs)

def _create_dynamodb_client():
    kwargs = {'region_name': settings.AWS_REGION}
    # Only pass credentials if they are explicitly provided
    if settings.AWS_ACCESS_KEY_ID:
        kwargs['aws_access_key_id'] = settings.AWS_ACCESS_KEY_ID
        kwargs['aws_secret_access_key'] = settings.AWS_SECRET_ACCESS_KEY
        if settings.AWS_SESSION_TOKEN:
            kwargs['aws_session_token'] = settings.AWS_SESSION_TOKEN
    return boto3.resource('dynamodb', **kwargs)

s3_client = _create_s3_client()
dynamo_client = _create_dynamodb_client()

users_table = dynamo_client.Table(settings.DYNAMODB_USERS_TABLE)
requests_table = dynamo_client.Table(settings.DYNAMODB_REQUESTS_TABLE)


# --- AUTHENTICATION ---
def verify_google_token(token: str):
    """
    Verifies the JWT token sent from frontend against Google's servers.
    Returns user info if valid, raises ValueError if not.
    """
    try:
        id_info = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
        return id_info
    except ValueError as e:
        print(f"Token verification failed: {e}")
        return None


def get_or_create_user(user_data):
    """
    Checks if user exists in DynamoDB. If not, creates them.
    Returns the user dictionary.
    """
    user_email = user_data['email']

    # Try to get user
    response = users_table.get_item(Key={'email': user_email})
    if 'Item' in response:
        return response['Item']

    # Create new user
    new_user = {
        'email': user_email,
        'name': user_data.get('name', 'Unknown'),
        'picture': user_data.get('picture', ''),
        'created_at': int(time.time())
    }
    users_table.put_item(Item=new_user)
    return new_user


# --- S3 LOGIC ---
def upload_file_to_s3(user_email: str, filename: str, file_type: str, file_content: bytes):
    """
    Upload file directly to S3 through backend.
    """
    # Create a unique file path: raw/user@email.com/uuid/filename
    request_id = str(uuid.uuid4())
    end = filename.split('.')[-1]
    object_name = f"raw/{user_email}/{request_id}/file.{end}"

    try:
        s3_client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=object_name,
            Body=file_content,
            ContentType=file_type
        )
        return {"s3_key": object_name, "request_id": request_id}
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None


def generate_presigned_upload_url(user_email: str, filename: str, file_type: str):
    """
    DEPRECATED: Generates a secure URL so Frontend can upload DIRECTLY to S3.
    Kept for backwards compatibility.
    """
    # Create a unique file path: raw/user@email.com/uuid.pdf
    request_id = str(uuid.uuid4())
    object_name = f"raw/{user_email}/{request_id}/{filename}"

    try:
        url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.S3_BUCKET_NAME,
                'Key': object_name,
                'ContentType': file_type
            },
            ExpiresIn=300  # URL valid for 5 minutes
        )
        return {"upload_url": url, "s3_key": object_name, "request_id": request_id}
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        return None


def download_file_from_s3(s3_key: str):
    """
    Download file from S3 and return file content and metadata.
    """
    try:
        response = s3_client.get_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=s3_key
        )
        return {
            'content': response['Body'].read(),
            'content_type': response.get('ContentType', 'application/octet-stream'),
            'filename': s3_key.split('/')[-1]
        }
    except Exception as e:
        print(f"Error downloading from S3: {e}")
        return None


def generate_presigned_download_url(s3_key: str):
    """
    DEPRECATED: Generate presigned download URL.
    Kept for backwards compatibility.
    """
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.S3_BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=3600
        )
        return url
    except Exception as e:
        return None


# --- REQUEST TRACKING ---
def create_translation_request(user_email: str, request_id: str, s3_key: str, doc_type: str):
    item = {
        'request_id': request_id,
        'user_email': user_email,  # Global Secondary Index (GSI) recommended here
        'status': 'UPLOADED',  # UPLOADED -> PROCESSING -> COMPLETED
        'document_type': doc_type,
        's3_input_key': s3_key,
        's3_output_key': None,
        'created_at': int(time.time())
    }
    requests_table.put_item(Item=item)
    return item


def get_request_status(request_id: str):
    response = requests_table.get_item(Key={'request_id': request_id})
    return response.get('Item', None)


def get_user_documents(user_email: str):
    """
    Fetch all documents for a user.
    Note: This requires a Global Secondary Index (GSI) on user_email in DynamoDB.
    For MVP, we'll use scan with filter (not recommended for production).
    """
    try:
        # Using scan for MVP - in production, use a GSI query
        response = requests_table.scan(
            FilterExpression='user_email = :email',
            ExpressionAttributeValues={':email': user_email}
        )
        items = response.get('Items', [])

        # Sort by created_at descending (newest first)
        items.sort(key=lambda x: x.get('created_at', 0), reverse=True)

        return items
    except Exception as e:
        print(f"Error fetching user documents: {e}")
        return []