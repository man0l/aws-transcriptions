import boto3
import os
from urllib.parse import urlparse

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    transcribe = boto3.client('transcribe')
    
    # Parse uploaded object details
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    media_uri = f's3://{bucket}/{key}'
    
    # Configure transcription parameters
    job_name = f'transcribe_{key.split(".")[0]}'
    
    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': media_uri},
        MediaFormat=key.split('.')[-1],
        OutputBucketName=os.environ['OUTPUT_BUCKET'],
        OutputKey=f'transcripts/{job_name}.json',
        Settings={
            'ShowSpeakerLabels': True,
            'MaxSpeakerLabels': 5,
            'EnableWordTimeOffsets': True
        }
    )
    
    return {'statusCode': 200} 