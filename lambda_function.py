import boto3
import os
from urllib.parse import urlparse, quote, unquote_plus
import time
import re

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
        
        # Extract user ID and video ID from the key path
        # Expected format: raw-media/USER_ID/VIDEO_ID.mp4 or users/USER_ID/videos/VIDEO_ID.mp4
        path_parts = decoded_key.split('/')
        
        user_id = None
        video_id = None
        
        # Try to find user ID and video ID in the path
        if len(path_parts) >= 3 and path_parts[0] == "raw-media":
            # Format: raw-media/USER_ID/VIDEO_ID.mp4
            user_id = path_parts[1]
            video_filename = path_parts[2]
            # Extract video ID by removing the extension
            video_id = os.path.splitext(video_filename)[0]
        elif len(path_parts) >= 4 and path_parts[0] == "users" and path_parts[2] == "videos":
            # Format: users/USER_ID/videos/VIDEO_ID.mp4
            user_id = path_parts[1]
            video_filename = path_parts[3]
            # Extract video ID by removing the extension
            video_id = os.path.splitext(video_filename)[0]
        
        # Generate timestamp for unique job name
        timestamp = int(time.time())
        
        # Fall back to timestamp if we couldn't extract the IDs
        if not user_id or not video_id:
            print("Could not extract user ID and video ID from path, using timestamp instead")
            job_name = f'transcribe_{timestamp}'
        else:
            # Use user ID and video ID for the job name, but ensure it's valid for AWS Transcribe
            # AWS Transcribe job names can only contain alphanumeric characters, hyphens, and underscores
            # They must be less than 200 characters
            # Clean user_id and video_id to ensure they're valid
            clean_user_id = re.sub(r'[^a-zA-Z0-9_-]', '', user_id)
            clean_video_id = re.sub(r'[^a-zA-Z0-9_-]', '', video_id)
            
            # Truncate if necessary (leaving room for timestamp)
            if len(clean_user_id) > 80:
                clean_user_id = clean_user_id[:80]
            if len(clean_video_id) > 70:
                clean_video_id = clean_video_id[:70]
                
            job_name = f'transcribe_{clean_user_id}_{clean_video_id}_{timestamp}'
            print(f"Using job name based on user ID and video ID with timestamp: {job_name}")
        
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