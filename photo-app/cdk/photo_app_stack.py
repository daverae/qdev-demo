from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as apigwv2_integrations,
    aws_iam as iam,
    RemovalPolicy,
    Duration,
    CfnOutput
)
from constructs import Construct

class PhotoAppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create S3 bucket for photos (private)
        photos_bucket = s3.Bucket(
            self, "PhotosBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            cors=[s3.CorsRule(
                allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.PUT, s3.HttpMethods.POST],
                allowed_origins=["*"],  # For production, restrict to your domain
                allowed_headers=["*"],
                max_age=3000
            )]
        )

        # Create DynamoDB table for photo metadata
        photos_table = dynamodb.Table(
            self, "PhotosTable",
            partition_key=dynamodb.Attribute(
                name="photoId",
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY,
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )

        # Create Lambda function for uploading photos
        upload_photo_function = lambda_.Function(
            self, "UploadPhotoFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../src/upload_photo"),
            handler="app.lambda_handler",
            timeout=Duration.seconds(30),
            environment={
                "PHOTOS_TABLE": photos_table.table_name,
                "PHOTOS_BUCKET": photos_bucket.bucket_name
            }
        )

        # Create Lambda function for getting photos
        get_photo_function = lambda_.Function(
            self, "GetPhotoFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset("../src/get_photo"),
            handler="app.lambda_handler",
            timeout=Duration.seconds(10),
            environment={
                "PHOTOS_TABLE": photos_table.table_name,
                "PHOTOS_BUCKET": photos_bucket.bucket_name
            }
        )

        # Grant permissions to Lambda functions
        photos_bucket.grant_put(upload_photo_function)
        photos_bucket.grant_read(get_photo_function)
        photos_table.grant_write_data(upload_photo_function)
        photos_table.grant_read_data(get_photo_function)

        # Create API Gateway HTTP API
        http_api = apigwv2.HttpApi(
            self, "PhotosApi",
            cors_preflight={
                "allow_origins": ["*"],  # For production, restrict to your domain
                "allow_methods": [apigwv2.CorsHttpMethod.ANY],
                "allow_headers": ["*"],
                "max_age": Duration.days(1)
            }
        )

        # Add routes to API Gateway
        http_api.add_routes(
            path="/photos",
            methods=[apigwv2.HttpMethod.POST],
            integration=apigwv2_integrations.HttpLambdaIntegration(
                "UploadPhotoIntegration", upload_photo_function
            )
        )

        http_api.add_routes(
            path="/photos/{photoId}",
            methods=[apigwv2.HttpMethod.GET],
            integration=apigwv2_integrations.HttpLambdaIntegration(
                "GetPhotoIntegration", get_photo_function
            )
        )
        
        # Output the API URL
        CfnOutput(
            self, "ApiUrl",
            value=http_api.url if http_api.url else "https://api-url-not-available",
            description="URL of the HTTP API"
        )