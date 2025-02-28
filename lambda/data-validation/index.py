import json
import boto3
import os
import logging
import datetime
from jsonschema import validate, ValidationError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3 = boto3.client('s3')
sns = boto3.client('sns')

# Environment variables
SCHEMA_BUCKET = os.environ['SCHEMA_BUCKET']
SCHEMA_KEY = os.environ['SCHEMA_KEY']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

def load_schema():
    """Load the JSON schema from S3"""
    try:
        response = s3.get_object(Bucket=SCHEMA_BUCKET, Key=SCHEMA_KEY)
        schema_content = response['Body'].read().decode('utf-8')
        return json.loads(schema_content)
    except Exception as e:
        logger.error(f"Error loading schema: {str(e)}")
        raise

def validate_data(data, schema):
    """Validate data against the schema"""
    validation_errors = []
    
    try:
        validate(instance=data, schema=schema)
        return True, []
    except ValidationError as e:
        validation_errors.append(str(e))
        return False, validation_errors

def send_notification(message, subject):
    """Send SNS notification"""
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject=subject
        )
        logger.info(f"Notification sent: {subject}")
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")

def lambda_handler(event, context):
    """Lambda function handler"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Get bucket and key from the event
    if 'Records' in event:
        # S3 event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
    elif 'bucket' in event and 'key' in event:
        # Direct invocation
        bucket = event['bucket']
        key = event['key']
    else:
        error_msg = "Invalid event structure. Expected S3 event or direct invocation with bucket and key."
        logger.error(error_msg)
        return {
            'statusCode': 400,
            'body': json.dumps({'error': error_msg})
        }
    
    try:
        # Load the schema
        schema = load_schema()
        
        # Get the data file from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        file_content = response['Body'].read().decode('utf-8')
        
        # Parse the data
        if key.endswith('.json'):
            data = json.loads(file_content)
        elif key.endswith('.csv'):
            # For CSV, we'd need to parse it into a structure
            # This is a simplified example
            import csv
            from io import StringIO
            
            csv_data = []
            csv_file = StringIO(file_content)
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                csv_data.append(row)
            data = csv_data
        else:
            error_msg = f"Unsupported file format: {key}"
            logger.error(error_msg)
            return {
                'statusCode': 400,
                'body': json.dumps({'error': error_msg})
            }
        
        # Validate the data
        is_valid, errors = validate_data(data, schema)
        
        # Prepare the result
        result = {
            'file': f"s3://{bucket}/{key}",
            'timestamp': datetime.datetime.now().isoformat(),
            'is_valid': is_valid,
            'errors': errors
        }
        
        # Send notification if validation fails
        if not is_valid:
            error_message = f"Data validation failed for file s3://{bucket}/{key}\n\nErrors:\n" + "\n".join(errors)
            send_notification(error_message, "Data Validation Failure")
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
    
    except Exception as e:
        error_msg = f"Error processing file s3://{bucket}/{key}: {str(e)}"
        logger.error(error_msg)
        send_notification(error_msg, "Data Processing Error")
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_msg})
        }

