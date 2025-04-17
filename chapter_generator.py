import json
import boto3
import os
import requests
import time
import re
from urllib.parse import urlparse, unquote_plus
from gemini_client import GeminiClient
from supabase_client import update_chapters

def format_time(seconds):
    """Convert seconds to HH:MM:SS format"""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    else:
        return f"{m:02d}:{s:02d}"

def format_transcript_with_detailed_timestamps(items, interval_seconds=10):
    """
    Format transcript with timestamps at regular intervals.
    
    Args:
        items: List of transcript items from AWS Transcribe JSON.
        interval_seconds: Target interval for timestamp insertion (in seconds).
        
    Returns:
        A string with the transcript text and timestamps inserted at regular intervals.
    """
    if not items:
        return ""
    
    result = []
    last_timestamp = -999  # Initialize with a very low value to ensure first timestamp is included
    current_timestamp = 0
    
    for item in items:
        try:
            if item.get('type') == 'pronunciation':
                # Get word and its timestamp
                word = item['alternatives'][0]['content']
                current_timestamp = float(item.get('start_time', 0))
                
                # Insert timestamp if enough time has passed since the last one
                if current_timestamp - last_timestamp >= interval_seconds:
                    minute = int(current_timestamp / 60)
                    second = int(current_timestamp % 60)
                    timestamp_str = f"[{minute:02d}:{second:02d}]"
                    
                    # Add spacing around timestamp for readability
                    if result and not result[-1].endswith(' '):
                        result.append(' ')
                    
                    result.append(timestamp_str + ' ')
                    last_timestamp = current_timestamp
                
                # Add the word
                result.append(word)
                
                # Add space after word unless it's the end of a sentence
                if not word.endswith(('.', '!', '?', ',')):
                    result.append(' ')
                    
            elif item.get('type') == 'punctuation':
                # Add punctuation without space
                result.append(item['alternatives'][0]['content'])
                
        except (KeyError, ValueError) as e:
            # Skip problematic items but log them
            continue
    
    return ''.join(result).strip()

def generate_chapters_with_gemini(detailed_transcript_text, video_duration_minutes):
    """
    Use Gemini to generate chapters based on transcript with timestamps.
    
    Args:
        detailed_transcript_text: The transcript text with timestamps.
        video_duration_minutes: Estimated duration of the video in minutes.
        
    Returns:
        String containing generated chapter list.
    """
    try:
        gemini = GeminiClient()
        
        prompt = f"""Objective: Generate meaningful video chapters based on the provided transcript, prioritizing logical content structure over arbitrary time intervals.

**Context:**
You are analyzing a transcript for a video that is approximately {video_duration_minutes} minutes long. Your goal is to create chapter markers that significantly enhance viewer navigation by identifying the distinct thematic sections, topic shifts, or key stages within the content.

**Core Chaptering Principles:**

1.  **Content is King:** The primary driver for creating a chapter break MUST be a logical shift in topic, a new major point being introduced, the start of a distinct step in a process, or a significant transition in the narrative. Do *not* create chapters just to fill time or meet a specific count.
2.  **Identify Logical Segments:** Read through the transcript and identify the natural breakpoints where the focus changes. Think about how you would outline the video's content – these outline points often make good chapters.
3.  **Viewer Navigation:** Chapters should help viewers find specific information or skip to sections of interest. Each chapter title should clearly signal the content of that segment.
4.  **Meaningful Duration:** While there's no fixed length, chapters should generally cover a substantial enough segment of content to be meaningful. Avoid extremely short chapters (e.g., under 15-20 seconds) unless they mark a very distinct, quick, but important transition or point.
5.  **Duration as Context, Not a Rule:** Use the total video duration ({video_duration_minutes} minutes) as a *general indicator*. Longer videos (e.g., 30+ minutes) are *more likely* to contain numerous distinct sections warranting more chapters. Shorter videos (e.g., under 10 minutes) might only have a few key sections. **However, the actual number of chapters must be determined by the content structure, not a predefined count based on duration.**
6.  **Full Coverage:** Ensure chapters span the entire video, starting at 00:00 and with the final chapter covering the concluding part of the video.

**Timestamp Instructions (Strict Adherence Required):**

1.  The transcript contains timestamps in `[MM:SS]` format.
2.  For each chapter you identify:
    a. Pinpoint the exact sentence or key phrase in the transcript where the new topic or logical section actually begins.
    b. Locate the [MM:SS] timestamp in the transcript that occurs immediately before or exactly at this identified starting sentence/phrase.
    c. Crucial Verification: Read the text immediately following the selected [MM:SS] timestamp. Confirm that this text genuinely marks the beginning of the new topic described by your chapter title. The timestamp MUST align closely with the actual start of the content for that chapter.
    d. Discrepancy Handling: If the [MM:SS] timestamp that occurs before the topic starts feels significantly too early (i.e., the topic clearly starts much later between two timestamps), prioritize the content alignment. Select the [MM:SS] timestamp that is closest to the actual start, even if it means the chapter technically begins a few seconds after the timestamp appears. The goal is for the timestamp click to land the viewer at the correct starting point of the discussion.
3.  **Remove the brackets** `[]` from the selected timestamp when creating the chapter list.
4.  Format **all** timestamps as `MM:SS`, including leading zeros for both minutes and seconds (e.g., `00:00`, `04:30`, `15:05`).

**Chapter Title Guidelines:**

1.  Keep titles concise (ideally 2-5 words).
2.  Make titles highly descriptive and accurately reflect the content of that chapter segment.
3.  Avoid overly generic titles like "Introduction," "Middle," "Conclusion" unless the content *truly* fits only that generic description (e.g., a formal introduction section). Prefer titles like "Understanding the Problem," "Step 1: Gathering Materials," "Analyzing the Results," "Final Thoughts & Next Steps."
4.  **IMPORTANT: Detect the language of the input transcript and use that SAME LANGUAGE for all chapter titles.** The chapter titles should be in the same language as the transcript content.

**Output Format (Strict Adherence Required):**

*   Your output MUST consist ONLY of the chapter list.
*   Each line must follow the format: `MM:SS Chapter Title`
*   All chapter titles MUST be in the same language as the transcript.
*   Do NOT include brackets, extra words, explanations, notes, or any text before or after the chapter list.

Here is the transcript:
{detailed_transcript_text}"""

        response = gemini.generate_content(prompt)
        print("Generated chapters:")
        print(response)
        return response
        
    except Exception as e:
        print(f"Error during chapter generation: {str(e)}")
        return "00:00 Introduction\n01:00 Main Content"

def extract_plain_transcript(transcript_json):
    """
    Extract plain text from the transcript JSON and return it.
    
    Args:
        transcript_json: The parsed JSON transcript
        
    Returns:
        str: Plain text transcript extracted from the JSON
    """
    # Extract the full text from the transcript
    if 'results' in transcript_json and 'transcripts' in transcript_json['results']:
        return transcript_json['results']['transcripts'][0]['transcript']
    return ""

def schedule_summary_generation(user_id, video_id, transcript_text, summary_type, delay_minutes=0):
    """
    Schedule a summary generation event using EventBridge.
    
    Args:
        user_id: The user ID
        video_id: The video ID
        transcript_text: The plain transcript text
        summary_type: Either 'short' or 'long'
        delay_minutes: Number of minutes to delay the event
    """
    try:
        events = boto3.client('events')
        
        # Calculate the event time
        event_time = time.time() + (delay_minutes * 60)
        
        # Create the event detail
        event_detail = {
            'user_id': user_id,
            'video_id': video_id,
            'transcript_text': transcript_text,
            'summary_type': summary_type
        }
        
        # Put the event
        response = events.put_events(
            Entries=[
                {
                    'Time': time.gmtime(event_time),
                    'Source': 'custom.transcription',
                    'DetailType': 'SummaryGenerationRequest',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': 'default'
                }
            ]
        )
        
        print(f"Scheduled {summary_type} summary generation event with response: {response}")
        return response
        
    except Exception as e:
        print(f"Error scheduling summary generation: {str(e)}")
        raise

def lambda_handler(event, context):
    try:
        s3 = boto3.client('s3')
        
        # Parse uploaded object details
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        # S3 event notifications URL-encode the key, so we need to decode it properly
        decoded_key = unquote_plus(key)
        
        print(f"Processing file: s3://{bucket}/{decoded_key}")
        
        # Only process JSON files in the transcripts folder
        if not key.startswith('transcripts/') or not key.endswith('.json'):
            print(f"Skipping non-transcript file: {key}")
            return {
                'statusCode': 200,
                'body': 'Not a transcript JSON file'
            }
        
        # Get the transcript file
        transcript_file = s3.get_object(Bucket=bucket, Key=decoded_key)
        transcript_content = transcript_file['Body'].read().decode('utf-8')
        transcript_json = json.loads(transcript_content)
        
        # Extract the full text from the transcript (for fallback)
        full_transcript_text = transcript_json['results']['transcripts'][0]['transcript']
        
        # Extract items with timestamps for detailed formatting
        items = transcript_json['results']['items']
        
        # Determine video duration from the last timestamp in the items
        video_duration_seconds = 0
        for item in reversed(items):
            if item.get('type') == 'pronunciation' and 'end_time' in item:
                video_duration_seconds = float(item.get('end_time', 0))
                break
        
        video_duration_minutes = round(video_duration_seconds / 60)
        if video_duration_minutes < 1:
            video_duration_minutes = 1  # Minimum 1 minute
            
        print(f"Estimated video duration: {video_duration_minutes} minutes")
        
        # Format transcript with detailed timestamps
        detailed_transcript_text = format_transcript_with_detailed_timestamps(items, interval_seconds=10)
        
        if not detailed_transcript_text:
            print("Warning: Could not create detailed transcript with timestamps.")
            print("Falling back to raw transcript text (no timestamps).")
            detailed_transcript_text = full_transcript_text
            
        transcript_sample = detailed_transcript_text[:200] + "..." if len(detailed_transcript_text) > 200 else detailed_transcript_text
        print(f"Successfully retrieved and formatted transcript ({len(detailed_transcript_text)} chars)")
        print(f"Sample with timestamps: {transcript_sample}")
        
        # Generate chapters using Gemini
        chapters = generate_chapters_with_gemini(detailed_transcript_text, video_duration_minutes)
        
        # Extract plain transcript text
        plain_transcript = extract_plain_transcript(transcript_json)
        
        # Extract user_id and video_id from the filename
        base_name = os.path.basename(key).split('.')[0]
        match = re.match(r'transcribe_([^_]+)_([^_]+)_\d+$', base_name)
        
        if not match:
            raise ValueError(f"Could not extract user_id and video_id from filename: {base_name}")
            
        user_id = match.group(1)
        video_id = match.group(2)
        
        # Save chapters to S3
        chapters_output_key = f"chapters/{user_id}/{video_id}_chapters.txt"
        transcript_output_key = f"plain_text/{user_id}/{video_id}_transcript.txt"
        
        # Ensure directories exist
        for output_key in [chapters_output_key, transcript_output_key]:
            if '/' in output_key:
                directory_path = '/'.join(output_key.split('/')[:-1]) + '/'
                try:
                    s3.head_object(Bucket=bucket, Key=directory_path)
                except:
                    s3.put_object(Bucket=bucket, Key=directory_path, Body='')
        
        # Save files to S3
        s3.put_object(Bucket=bucket, Key=chapters_output_key, Body=chapters, ContentType='text/plain')
        s3.put_object(Bucket=bucket, Key=transcript_output_key, Body=plain_transcript, ContentType='text/plain')
        
        print(f"Chapters saved to s3://{bucket}/{chapters_output_key}")
        print(f"Plain transcript saved to s3://{bucket}/{transcript_output_key}")
        
        # Update document with chapters and set status to processing_summaries
        try:
            update_chapters(user_id, video_id, chapters)
            print("Updated document with chapters and set status to processing_summaries")
        except Exception as e:
            print(f"Error updating Supabase: {str(e)}")
            raise
        
        # Schedule summary generation events
        # Schedule short summary first
        schedule_summary_generation(user_id, video_id, full_transcript_text, 'short', delay_minutes=1)
        # Schedule long summary with 1-minute delay
        schedule_summary_generation(user_id, video_id, full_transcript_text, 'long', delay_minutes=2)
        
        return {
            'statusCode': 200,
            'body': f"Processing complete. Chapters saved and summary generation scheduled."
        }
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        raise 