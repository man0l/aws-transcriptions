import os
from google import genai
from google.genai import types

class GeminiClient:
    def __init__(self, api_key=None, model_name=None):
        """
        Initialize the Gemini client.
        
        Args:
            api_key: Optional API key. If not provided, will try to get from environment.
            model_name: Optional model name. If not provided, will use default from environment.
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not provided and not found in environment variables.")
            
        self.model_name = model_name or os.environ.get("GEMINI_MODEL_NAME", "gemini-1.5-pro-latest")
        self.client = genai.Client(api_key=self.api_key)

    def generate_content(self, prompt, response_type="text/plain", stream=True):
        """
        Generate content using Gemini model.
        
        Args:
            prompt: The prompt text to send to Gemini
            response_type: MIME type for response (default: text/plain)
            stream: Whether to stream the response (default: True)
            
        Returns:
            Generated content as string
        """
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            response_mime_type=response_type,
        )

        try:
            if stream:
                response_text = ""
                for chunk in self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=contents,
                    config=generate_content_config,
                ):
                    if chunk.text:
                        response_text += chunk.text
                return response_text.strip()
            else:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=generate_content_config,
                )
                return response.text.strip()
        except Exception as e:
            print(f"Error during content generation: {str(e)}")
            raise 