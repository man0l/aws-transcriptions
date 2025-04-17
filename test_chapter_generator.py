import unittest
from unittest.mock import patch, MagicMock
import os
import io
import sys
from chapter_generator import GeminiClient, generate_chapters_with_gemini

class CaptureOutput:
    """Context manager to capture stdout and stderr"""
    def __init__(self):
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        self._stdout = sys.stdout
        self._stderr = sys.stderr

    def __enter__(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        return self

    def __exit__(self, *args):
        sys.stdout = self._stdout
        sys.stderr = self._stderr

class TestGeminiClient(unittest.TestCase):
    def setUp(self):
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'GEMINI_API_KEY': 'test_api_key',
            'GEMINI_MODEL_NAME': 'test_model'
        })
        self.env_patcher.start()
        
    def tearDown(self):
        self.env_patcher.stop()

    def test_init_with_env_vars(self):
        """Test client initialization using environment variables"""
        client = GeminiClient()
        self.assertEqual(client.api_key, 'test_api_key')
        self.assertEqual(client.model_name, 'test_model')

    def test_init_with_params(self):
        """Test client initialization using constructor parameters"""
        client = GeminiClient(api_key='custom_key', model_name='custom_model')
        self.assertEqual(client.api_key, 'custom_key')
        self.assertEqual(client.model_name, 'custom_model')

    def test_init_no_api_key(self):
        """Test client initialization with no API key"""
        self.env_patcher.stop()  # Remove environment variables
        with self.assertRaises(ValueError):
            GeminiClient()

    @patch('google.genai.Client')
    def test_generate_content_streaming(self, mock_genai_client):
        """Test content generation with streaming"""
        # Mock the streaming response
        mock_chunk1 = MagicMock()
        mock_chunk1.text = "First "
        mock_chunk2 = MagicMock()
        mock_chunk2.text = "response"
        
        mock_stream = MagicMock()
        mock_stream.generate_content_stream.return_value = [mock_chunk1, mock_chunk2]
        
        mock_genai_client.return_value.models = mock_stream
        
        client = GeminiClient()
        with CaptureOutput():  # Capture any print statements
            response = client.generate_content("Test prompt", stream=True)
        
        self.assertEqual(response, "First response")

    @patch('google.genai.Client')
    def test_generate_content_non_streaming(self, mock_genai_client):
        """Test content generation without streaming"""
        # Mock the non-streaming response
        mock_response = MagicMock()
        mock_response.text = "Test response"
        
        mock_generate = MagicMock()
        mock_generate.generate_content.return_value = mock_response
        
        mock_genai_client.return_value.models = mock_generate
        
        client = GeminiClient()
        with CaptureOutput():  # Capture any print statements
            response = client.generate_content("Test prompt", stream=False)
        
        self.assertEqual(response, "Test response")

class TestChapterGeneration(unittest.TestCase):
    def setUp(self):
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'GEMINI_API_KEY': 'test_api_key',
            'GEMINI_MODEL_NAME': 'test_model'
        })
        self.env_patcher.start()
        
        # Sample transcript with timestamps
        self.sample_transcript = """[00:00] Welcome to this video about Python programming.
[00:15] Today we'll learn about functions and classes.
[02:30] Let's start with functions first.
[05:45] Now moving on to classes.
[10:00] That's all for today, thanks for watching!"""
        
    def tearDown(self):
        self.env_patcher.stop()

    @patch.object(GeminiClient, 'generate_content')
    def test_generate_chapters(self, mock_generate_content):
        """Test chapter generation with mock response"""
        # Mock the Gemini response
        expected_chapters = """00:00 Introduction to Python
02:30 Understanding Functions
05:45 Classes in Python
10:00 Conclusion"""
        mock_generate_content.return_value = expected_chapters
        
        # Test chapter generation
        with CaptureOutput() as output:  # Capture print statements
            result = generate_chapters_with_gemini(self.sample_transcript, 15)
        
        self.assertEqual(result, expected_chapters)
        
        # Verify the mock was called
        mock_generate_content.assert_called_once()
        
        # Verify prompt contains required elements
        call_args = mock_generate_content.call_args[0][0]
        self.assertIn("Objective: Generate meaningful video chapters", call_args)
        self.assertIn(self.sample_transcript, call_args)
        self.assertIn("15 minutes", call_args)
        
        # Verify output contains expected log message
        self.assertIn("Generated chapters:", output.stdout.getvalue())

    @patch.object(GeminiClient, 'generate_content')
    def test_generate_chapters_error(self, mock_generate_content):
        """Test chapter generation error handling"""
        # Mock an error in content generation
        mock_generate_content.side_effect = Exception("API Error")
        
        # Test error handling
        with CaptureOutput() as output:  # Capture print statements
            result = generate_chapters_with_gemini(self.sample_transcript, 15)
        
        self.assertEqual(result, "00:00 Introduction\n01:00 Main Content")
        
        # Verify error message was logged
        self.assertIn("Error during chapter generation: API Error", output.stdout.getvalue())

if __name__ == '__main__':
    unittest.main(verbose=2)  # Use verbose output for better test reporting 