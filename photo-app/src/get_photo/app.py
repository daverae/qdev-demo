import os
import json
import boto3
import logging
from botocore.exceptions import ClientError

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
    Lambda function to handle photo retrieval.
    
    This function:
    1. Extracts the photo ID from the path parameters
    2. Retrieves the photo metadata from DynamoDB
    3. Generates a pre-signed URL for the S3 object
    4. Returns the URL in the response
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response with pre-signed URL
    """
    try:
        logger.info("Received get photo request")
        
        # Extract photo ID from path parameters
        if 'pathParameters' not in event or not event['pathParameters'] or 'photoId' not in event['pathParameters']:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing photo ID'})
            }
        
        photo_id = event['pathParameters']['photoId']
        
        # Retrieve photo metadata from DynamoDB
        photos_table = dynamodb.Table(PHOTOS_TABLE)
        response = photos_table.get_item(
            Key={'photoId': photo_id}
        )
        
        # Check if the photo exists
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Photo not found'})
            }
        
        photo_metadata = response['Item']
        s3_key = photo_metadata['s3Key']
        
        # Generate pre-signed URL (valid for 1 hour)
        try:
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': PHOTOS_BUCKET,
                    'Key': s3_key
                },
                ExpiresIn=3600  # 1 hour
            )
        except ClientError as e:
            logger.error(f"Error generating pre-signed URL: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Failed to generate download URL'})
            }
        
        # Return the pre-signed URL
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # For CORS
            },
            'body': json.dumps({
                'photoId': photo_id,
                'fileName': photo_metadata['fileName'],
                'uploadTimestamp': photo_metadata['uploadTimestamp'],
                'downloadUrl': presigned_url
            })
        }
        
    except Exception as e:
        logger.error(f"Error retrieving photo: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }