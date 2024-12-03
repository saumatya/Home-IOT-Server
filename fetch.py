import boto3
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access the variables
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region = os.getenv('AWS_DEFAULT_REGION')

# Initialize DynamoDB with loaded credentials
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=region
)

# Example: Access a specific table
table = dynamodb.Table('tbl_opla_data')
response = table.scan()
print(response['Items'])
