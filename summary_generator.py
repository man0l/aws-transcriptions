import json
import os
from gemini_client import GeminiClient
from supabase_client import update_summary

def generate_summary(transcript_text, summary_type):
    """Generate either a short or long summary using Gemini."""
    try:
        gemini = GeminiClient()
        
        if summary_type == 'short':
            prompt = f"""Generate a very concise 1-2 sentence summary of the following transcript that captures its main point or key takeaway. Keep it under 50 words.

Transcript:
{transcript_text}"""
        else:  # long summary
            prompt = f"""Generate a detailed summary of the following transcript. The summary should:
1. Be around 4-6 paragraphs
2. Capture all major points and key details
3. Maintain the logical flow of ideas
4. Be written in clear, professional language
5. Be comprehensive enough for someone to understand the full content without watching the video

Transcript:
{transcript_text}"""

        return gemini.generate_content(prompt)
        
    except Exception as e:
        print(f"Error generating {summary_type} summary: {str(e)}")
        return f"Error generating {summary_type} summary."

def lambda_handler(event, context):
    try:
        # Get the event detail - it's already a dictionary, no need to parse
        event_detail = event['detail']
        
        user_id = event_detail['user_id']
        video_id = event_detail['video_id']
        transcript_text = event_detail['transcript_text']
        summary_type = event_detail['summary_type']
        
        print(f"Generating {summary_type} summary for video {video_id}")
        
        # Generate the summary
        summary = generate_summary(transcript_text, summary_type)
        
        # Update Supabase with the summary
        try:
            update_summary(user_id, video_id, summary, summary_type)
            print(f"Updated document with {summary_type} summary")
            
            # Log status update if this is the long summary
            if summary_type == 'long':
                print("Document processing marked as completed")
        except Exception as e:
            print(f"Error updating Supabase: {str(e)}")
            raise
        
        return {
            'statusCode': 200,
            'body': f"{summary_type} summary generated and saved successfully"
        }
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        raise 