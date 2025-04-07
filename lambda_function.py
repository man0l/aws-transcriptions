import boto3
import os
from urllib.parse import urlparse, quote
import time

def lambda_handler(event, context):
    try:
        s3 = boto3.client('s3')
        transcribe = boto3.client('transcribe', region_name='eu-central-1')
        
        # Parse uploaded object details
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        # URL encode the key while preserving the path structure
        encoded_key = '/'.join(quote(part, safe='') for part in key.split('/'))
        media_uri = f's3://{bucket}/{encoded_key}'
        
        # Configure transcription parameters
        # Generate a unique job name using timestamp
        timestamp = int(time.time())
        job_name = f'transcribe_{timestamp}'
        
        # Get the file extension for MediaFormat
        file_extension = key.split('.')[-1].lower()
        if file_extension == 'mp4':
            media_format = 'mp4'
        else:
            raise ValueError(f'Unsupported file format: {file_extension}')
        
        print(f'Starting transcription job: {job_name} for file: {key}')
        print(f'Using encoded media URI: {media_uri}')
        
        response = transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': media_uri},
            MediaFormat=media_format,
            LanguageCode='bg-BG',
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