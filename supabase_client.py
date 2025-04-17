import os
from supabase import create_client, Client

def get_supabase_client():
    """
    Initialize and return a Supabase client using environment variables.
    
    Returns:
        A Supabase client instance
    
    Raises:
        ValueError: If environment variables are not set
    """
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables not set.")
    
    return create_client(supabase_url, supabase_key)

def update_document(user_id, video_id, update_data):
    """
    Update a document in Supabase with the provided data.
    
    Args:
        user_id: The user ID
        video_id: The video ID
        update_data: Dictionary containing the fields to update
        
    Returns:
        bool: True if update was successful
        
    Raises:
        Exception: If there was an error updating Supabase
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table("documents") \
            .update(update_data) \
            .eq("user_id", user_id) \
            .eq("video_id", video_id) \
            .execute()
            
        return True
        
    except Exception as e:
        print(f"Error updating Supabase document: {str(e)}")
        raise

def update_chapters(user_id, video_id, chapters):
    """Update document with chapters and set status to processing summaries."""
    update_data = {
        "chapters": chapters,
        "processing_status": "processing_summaries"
    }
    
    return update_document(user_id, video_id, update_data)

def update_summary(user_id, video_id, summary_text, summary_type):
    """Update document with a summary (short or long)."""
    update_data = {
        f"{summary_type}_summary": summary_text
    }
    
    # If this is the long summary (last to be generated), mark processing as complete
    if summary_type == 'long':
        update_data["processing_status"] = "completed"
    
    return update_document(user_id, video_id, update_data)

def update_transcript(user_id, video_id, transcript_text):
    """Update document with the full transcript text."""
    update_data = {
        "transcription": transcript_text
    }
    
    return update_document(user_id, video_id, update_data) 