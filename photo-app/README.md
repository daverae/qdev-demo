# Serverless Photo Application

A serverless application for uploading and retrieving photos using AWS services.

## Architecture

This application uses the following AWS services:
- **API Gateway**: HTTP API with endpoints for uploading and retrieving photos
- **Lambda**: Functions for processing uploads and generating download URLs
- **S3**: Storage for the photos
- **DynamoDB**: Storage for photo metadata

```
                  ┌─────────────┐
                  │             │
                  │   Client    │
                  │             │
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │             │
                  │ API Gateway │
                  │             │
                  └──────┬──────┘
                         │
           ┌─────────────┴─────────────┐
           │                           │
           ▼                           ▼
    ┌─────────────┐             ┌─────────────┐
    │   Upload    │             │     Get     │
    │   Lambda    │             │   Lambda    │
    └──────┬──────┘             └──────┬──────┘
           │                           │
     ┌─────┴───────┐             ┌─────┴───────┐
     │             │             │             │
     ▼             ▼             ▼             │
┌─────────┐   ┌─────────┐   ┌─────────┐        │
│         │   │         │   │         │        │
│    S3   │   │ DynamoDB│   │ DynamoDB│        │
│         │   │         │   │         │        │
└─────────┘   └─────────┘   └─────────┘        │
     ▲                                         │
     │                                         │
     └─────────────────────────────────────────┘
```

## Setup Instructions

### Prerequisites
- AWS CLI configured with appropriate credentials
- Node.js and npm installed
- Python 3.8+ installed
- AWS CDK installed (`npm install -g aws-cdk`)

### Deployment Steps

1. Install CDK dependencies:
   ```
   cd cdk
   pip install -r requirements.txt
   ```

2. Bootstrap CDK (if not already done):
   ```
   cdk bootstrap
   ```

3. Deploy the application:
   ```
   cdk deploy
   ```

4. After deployment, the API Gateway URL will be displayed in the output. Use this URL to access the application.

### Local Development

1. Install Lambda function dependencies:
   ```
   cd src/upload_photo
   pip install -r requirements.txt
   cd ../get_photo
   pip install -r requirements.txt
   ```

2. Run unit tests:
   ```
   cd tests
   pytest
   ```

3. Open the frontend in a web browser:
   ```
   open src/frontend/index.html
   ```

## Usage

### Upload a Photo
- Use the web interface to upload photos
- Or make a POST request to `/photos` endpoint with multipart/form-data

### Retrieve a Photo
- Use the web interface to view uploaded photos
- Or make a GET request to `/photos/{photoId}` to get a pre-signed URL

## Design Decisions and Assumptions

- Photos are stored in a private S3 bucket and accessed via pre-signed URLs
- Pre-signed URLs expire after 1 hour
- Photo IDs are generated as UUIDs
- DynamoDB is used for metadata storage with photoId as the partition key
- API Gateway HTTP API is used for simplicity and cost-effectiveness
- Lambda functions follow the principle of least privilege

## Security Considerations

- S3 bucket is private with no public access
- Lambda functions have minimal IAM permissions
- API can be secured with additional authentication mechanisms if needed