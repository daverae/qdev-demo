# Serverless Photo Application

This repository contains a serverless photo application built using AWS CDK. The application allows users to upload and retrieve photos through a simple web interface.

## Project Structure

```
photo-app/
├── src/
│   ├── upload_photo/
│   │   ├── app.py                # Lambda function for uploading photos
│   │   └── requirements.txt      # Dependencies for upload function
│   ├── get_photo/
│   │   ├── app.py                # Lambda function for retrieving photos
│   │   └── requirements.txt      # Dependencies for get function
│   └── frontend/
│       └── index.html            # Simple HTML frontend for testing
├── tests/
│   └── unit/
│       ├── test_upload_photo.py  # Unit tests for upload function
│       └── test_get_photo.py     # Unit tests for get function
├── cdk/
│   ├── app.py                    # CDK app entry point
│   ├── photo_app_stack.py        # CDK stack definition
│   └── requirements.txt          # CDK dependencies
├── template.yaml                 # SAM template for compatibility
├── .gitignore                    # Git ignore file
└── README.md                     # This file
```

## Features

- Upload photos to S3 via API Gateway
- Retrieve photos using pre-signed URLs
- Store photo metadata in DynamoDB
- Simple HTML frontend for testing

For detailed documentation, please see the [photo-app/README.md](photo-app/README.md) file.