import os
import json
import unittest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

# Set environment variables for testing
os.environ['PHOTOS_TABLE'] = 'test-photos-table'
os.environ['PHOTOS_BUCKET'] = 'test-photos-bucket'

# Import the Lambda function
from src.get_photo.app import lambda_handler

class TestGetPhotoFunction(unittest.TestCase):
    """Test cases for the get_photo Lambda function"""

    @patch('src.get_photo.app.boto3')
    def test_successful_get_photo(self, mock_boto3):
        """Test successful photo retrieval"""
        # Mock DynamoDB and S3 clients
        mock_dynamodb_resource = MagicMock()
        mock_table = MagicMock()
        mock_s3_client = MagicMock()
        
        mock_boto3.resource.return_value = mock_dynamodb_resource
        mock_dynamodb_resource.Table.return_value = mock_table
        mock_boto3.client.return_value = mock_s3_client
        
        # Set up DynamoDB mock response
        mock_table.get_item.return_value = {
            'Item': {
                'photoId': 'test-photo-id',
                'fileName': 'test.jpg',
                'uploadTimestamp': '2023-01-01T12:00:00',
                's3Key': 'photos/test-photo-id/test.jpg'
            }
        }
        
        # Set up S3 presigned URL mock
        mock_s3_client.generate_presigned_url.return_value = 'https://test-presigned-url.com'
        
        # Create test event
        test_event = {
            'pathParameters': {
                'photoId': 'test-photo-id'
            }
        }
        
        # Call the Lambda function
        response = lambda_handler(test_event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['headers']['Content-Type'], 'application/json')
        
        # Parse the response body
        response_body = json.loads(response['body'])
        self.assertEqual(response_body['photoId'], 'test-photo-id')
        self.assertEqual(response_body['fileName'], 'test.jpg')
        self.assertEqual(response_body['uploadTimestamp'], '2023-01-01T12:00:00')
        self.assertEqual(response_body['downloadUrl'], 'https://test-presigned-url.com')
        
        # Verify DynamoDB get_item was called correctly
        mock_table.get_item.assert_called_once_with(
            Key={'photoId': 'test-photo-id'}
        )
        
        # Verify S3 generate_presigned_url was called correctly
        mock_s3_client.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={
                'Bucket': 'test-photos-bucket',
                'Key': 'photos/test-photo-id/test.jpg'
            },
            ExpiresIn=3600
        )

    @patch('src.get_photo.app.boto3')
    def test_missing_photo_id(self, mock_boto3):
        """Test retrieval with missing photo ID"""
        # Create test event with missing photo ID
        test_event = {
            'pathParameters': {}  # Missing photoId
        }
        
        # Call the Lambda function
        response = lambda_handler(test_event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Missing photo ID')
        
        # Verify DynamoDB and S3 were not called
        mock_boto3.resource.return_value.Table.return_value.get_item.assert_not_called()
        mock_boto3.client.return_value.generate_presigned_url.assert_not_called()

    @patch('src.get_photo.app.boto3')
    def test_photo_not_found(self, mock_boto3):
        """Test retrieval of non-existent photo"""
        # Mock DynamoDB client
        mock_dynamodb_resource = MagicMock()
        mock_table = MagicMock()
        
        mock_boto3.resource.return_value = mock_dynamodb_resource
        mock_dynamodb_resource.Table.return_value = mock_table
        
        # Set up DynamoDB mock response for non-existent item
        mock_table.get_item.return_value = {}  # No Item in response
        
        # Create test event
        test_event = {
            'pathParameters': {
                'photoId': 'non-existent-id'
            }
        }
        
        # Call the Lambda function
        response = lambda_handler(test_event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 404)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Photo not found')
        
        # Verify DynamoDB was called but S3 was not
        mock_table.get_item.assert_called_once()
        mock_boto3.client.return_value.generate_presigned_url.assert_not_called()

    @patch('src.get_photo.app.boto3')
    def test_s3_error_handling(self, mock_boto3):
        """Test error handling for S3 failures"""
        # Mock DynamoDB and S3 clients
        mock_dynamodb_resource = MagicMock()
        mock_table = MagicMock()
        mock_s3_client = MagicMock()
        
        mock_boto3.resource.return_value = mock_dynamodb_resource
        mock_dynamodb_resource.Table.return_value = mock_table
        mock_boto3.client.return_value = mock_s3_client
        
        # Set up DynamoDB mock response
        mock_table.get_item.return_value = {
            'Item': {
                'photoId': 'test-photo-id',
                'fileName': 'test.jpg',
                'uploadTimestamp': '2023-01-01T12:00:00',
                's3Key': 'photos/test-photo-id/test.jpg'
            }
        }
        
        # Set up S3 to raise an exception
        mock_s3_client.generate_presigned_url.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey', 'Message': 'The specified key does not exist.'}},
            'GetObject'
        )
        
        # Create test event
        test_event = {
            'pathParameters': {
                'photoId': 'test-photo-id'
            }
        }
        
        # Call the Lambda function
        response = lambda_handler(test_event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Failed to generate download URL')

    @patch('src.get_photo.app.boto3')
    def test_missing_path_parameters(self, mock_boto3):
        """Test retrieval with missing path parameters"""
        # Create test event with missing path parameters
        test_event = {}  # No pathParameters
        
        # Call the Lambda function
        response = lambda_handler(test_event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Missing photo ID')

if __name__ == '__main__':
    unittest.main()