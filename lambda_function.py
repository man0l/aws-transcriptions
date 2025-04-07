import boto3
import os
from urllib.parse import urlparse, quote, unquote_plus
import time

def lambda_handler(event, context):
    try:
        s3 = boto3.client('s3')
        transcribe = boto3.client('transcribe', region_name='eu-central-1')
        
        # Parse uploaded object details
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        # S3 event notifications URL-encode the key, so we need to decode it properly
        # using unquote_plus which also replaces plus signs with spaces
        decoded_key = unquote_plus(key)
        
        # Verify that the object exists by attempting to get its metadata
        try:
            s3.head_object(Bucket=bucket, Key=decoded_key)
            print(f"Successfully verified S3 object exists: s3://{bucket}/{decoded_key}")
        except Exception as e:
            print(f"Error verifying S3 object: {str(e)}")
            # If the object doesn't exist with the decoded key, try using the original key
            try:
                s3.head_object(Bucket=bucket, Key=key)
                print(f"Original key exists, using it instead: s3://{bucket}/{key}")
                decoded_key = key
            except:
                raise ValueError(f"Cannot find S3 object with either decoded key '{decoded_key}' or original key '{key}'")
        
        # Generate a unique job name using timestamp
        timestamp = int(time.time())
        job_name = f'transcribe_{timestamp}'
        
        # Get the file extension for MediaFormat
        file_extension = decoded_key.split('.')[-1].lower()
        if file_extension == 'mp4':
            media_format = 'mp4'
        else:
            raise ValueError(f'Unsupported file format: {file_extension}')
        
        print(f'Starting transcription job: {job_name} for file: {decoded_key}')
        
        # Construct the S3 URI for the transcription job
        media_file_uri = f's3://{bucket}/{decoded_key}'
        print(f'Using media URI: {media_file_uri}')
        
        response = transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': media_file_uri},
            MediaFormat=media_format,
            IdentifyLanguage=True,
            OutputBucketName=os.environ['OUTPUT_BUCKET'],
            OutputKey=f'transcripts/{job_name}.json',
            Settings={
                
            },
            Subtitles={
                'Formats': ['srt']
            }
        )
        
        print(f'Transcription job started successfully: {response}')
        return {
            'statusCode': 200,
            'body': {
                'jobName': job_name,
                'status': 'started'
            }
        }
        
    except Exception as e:
        print(f'Error processing file: {str(e)}')
        raise 