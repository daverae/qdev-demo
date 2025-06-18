import os
import json
import base64
import unittest
from unittest.mock import patch, MagicMock

# Set environment variables for testing
os.environ['PHOTOS_TABLE'] = 'test-photos-table'
os.environ['PHOTOS_BUCKET'] = 'test-photos-bucket'

# Import the Lambda function
from src.upload_photo.app import lambda_handler

class TestUploadPhotoFunction(unittest.TestCase):
    """Test cases for the upload_photo Lambda function"""

    @patch('src.upload_photo.app.boto3')
    def test_successful_upload(self, mock_boto3):
        """Test successful photo upload"""
        # Mock S3 and DynamoDB clients
        mock_s3_client = MagicMock()
        mock_dynamodb_resource = MagicMock()
        mock_table = MagicMock()
        
        mock_boto3.client.return_value = mock_s3_client
        mock_boto3.resource.return_value = mock_dynamodb_resource
        mock_dynamodb_resource.Table.return_value = mock_table
        
        # Create test image data
        test_image = b'test image data'
        test_image_base64 = base64.b64encode(test_image).decode('utf-8')
        
        # Create test event
        test_event = {
            'body': json.dumps({
                'fileName': 'test.jpg',
                'fileContent': test_image_base64
            })
        }
        
        # Call the Lambda function
        response = lambda_handler(test_event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 201)
        self.assertEqual(response['headers']['Content-Type'], 'application/json')
        
        # Parse the response body
        response_body = json.loads(response['body'])
        self.assertIn('photoId', response_body)
        self.assertEqual(response_body['fileName'], 'test.jpg')
        self.assertIn('uploadTimestamp', response_body)
        
        # Verify S3 put_object was called
        mock_s3_client.put_object.assert_called_once()
        call_args = mock_s3_client.put_object.call_args[1]
        self.assertEqual(call_args['Bucket'], 'test-photos-bucket')
        self.assertIn('photos/', call_args['Key'])
        self.assertEqual(call_args['ContentType'], 'image/jpeg')
        
        # Verify DynamoDB put_item was called
        mock_table.put_item.assert_called_once()
        item = mock_table.put_item.call_args[1]['Item']
        self.assertEqual(item['fileName'], 'test.jpg')
        self.assertIn('photoId', item)
        self.assertIn('uploadTimestamp', item)
        self.assertIn('s3Key', item)

    @patch('src.upload_photo.app.boto3')
    def test_missing_file_content(self, mock_boto3):
        """Test upload with missing file content"""
        # Create test event with missing file content
        test_event = {
            'body': json.dumps({
                'fileName': 'test.jpg',
                # Missing fileContent
            })
        }
        
        # Call the Lambda function
        response = lambda_handler(test_event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Missing file content')
        
        # Verify S3 and DynamoDB were not called
        mock_boto3.client.return_value.put_object.assert_not_called()
        mock_boto3.resource.return_value.Table.return_value.put_item.assert_not_called()

    @patch('src.upload_photo.app.boto3')
    def test_missing_body(self, mock_boto3):
        """Test upload with missing request body"""
        # Create test event with missing body
        test_event = {}
        
        # Call the Lambda function
        response = lambda_handler(test_event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Missing request body')

    @patch('src.upload_photo.app.boto3')
    def test_invalid_json(self, mock_boto3):
        """Test upload with invalid JSON in body"""
        # Create test event with invalid JSON
        test_event = {
            'body': 'not valid json'
        }
        
        # Call the Lambda function
        response = lambda_handler(test_event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Invalid request format')

    @patch('src.upload_photo.app.boto3')
    def test_s3_error_handling(self, mock_boto3):
        """Test error handling for S3 failures"""
        # Mock S3 client to raise an exception
        mock_s3_client = MagicMock()
        mock_s3_client.put_object.side_effect = Exception("S3 error")
        mock_boto3.client.return_value = mock_s3_client
        
        # Create test event
        test_image = b'test image data'
        test_image_base64 = base64.b64encode(test_image).decode('utf-8')
        test_event = {
            'body': json.dumps({
                'fileName': 'test.jpg',
                'fileContent': test_image_base64
            })
        }
        
        # Call the Lambda function
        response = lambda_handler(test_event, {})
        
        # Verify the response
        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertIn('error', response_body)
        self.assertEqual(response_body['error'], 'Internal server error')

if __name__ == '__main__':
    unittest.main()