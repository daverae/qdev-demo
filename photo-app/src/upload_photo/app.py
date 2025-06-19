import os
import json
import uuid
import base64
import boto3
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Get environment variables
PHOTOS_TABLE = os.environ['PHOTOS_TABLE']
PHOTOS_BUCKET = os.environ['PHOTOS_BUCKET']

def lambda_handler(event, context):
    """
    Lambda function to handle photo uploads.
    
    This function:
    1. Parses the incoming request
    2. Extracts the photo data and metadata
    3. Generates a unique ID for the photo
    4. Uploads the photo to S3
    5. Stores the metadata in DynamoDB
    6. Returns a response with the photo ID
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    try:
        logger.info("Received upload request")
        
        # Parse request body
        if 'body' not in event or not event['body']:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing request body'})
            }
        
        # Check if the body is base64 encoded
        is_base64_encoded = event.get('isBase64Encoded', False)
        body = event['body']
        
        if is_base64_encoded:
            body = base64.b64decode(body)
            
        # For simplicity, we assume the body contains JSON with base64 encoded image
        # In a real application, you would parse multipart/form-data
        try:
            if isinstance(body, bytes):
                body = body.decode('utf-8')
            
            request_data = json.loads(body)
            file_name = request_data.get('fileName', 'unnamed.jpg')
            file_content_base64 = request_data.get('fileContent', '')
            
            if not file_content_base64:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Missing file content'})
                }
                
'body': json.dumps({'error': 'Missing file content'})
                }
                
            # TODO: Implement streaming or chunked upload for large files
            file_content = base64.b64decode(file_content_base64)
        except Exception as e:
            logger.error(f"Error parsing request body: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing request body: {str(e)}")
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid request format'})
            }
        
        # Generate a unique ID for the photo
        photo_id = str(uuid.uuid4())
        
        # Determine content type (in a real app, you'd detect this from the file)
        content_type = 'image/jpeg'  # Default
        if file_name.lower().endswith('.png'):
            content_type = 'image/png'
        elif file_name.lower().endswith('.gif'):
            content_type = 'image/gif'
        
        # Upload the photo to S3
        s3_key = f"photos/{photo_id}/{file_name}"
        s3_client.put_object(
            Bucket=PHOTOS_BUCKET,
            Key=s3_key,
            Body=file_content,
            ContentType=content_type
        )
        
        # Store metadata in DynamoDB
        timestamp = datetime.utcnow().isoformat()
        photos_table = dynamodb.Table(PHOTOS_TABLE)
        photos_table.put_item(
            Item={
                'photoId': photo_id,
                'fileName': file_name,
                'uploadTimestamp': timestamp,
                's3Key': s3_key
            }
        )
        
        # Return success response
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # For CORS
            },
            'body': json.dumps({
                'photoId': photo_id,
                'fileName': file_name,
                'uploadTimestamp': timestamp
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }