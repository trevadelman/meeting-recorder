import requests
from typing import List
from .audio import TranscriptSegment

class LLMProcessor:
    def __init__(self, api_url="http://localhost:11434/api/generate"):
        self.api_url = api_url
        self.timeout = 30

    def generate_summary(self, transcript: List[TranscriptSegment]) -> str:
        """Generate a meeting summary using a local LLM"""
        full_text = "\n".join([
            f"{seg.speaker}: {seg.text}" for seg in transcript
        ])
        
        prompt = f"""As an AI meeting assistant, analyze this meeting transcript and provide:
1. Key Topics: Main subjects that were introduced or discussed
2. Context: Any background information or setup provided
3. Next Steps: Suggested follow-ups based on the topics mentioned

Keep the summary concise and focus on the introductory nature of the discussion if it was brief.

Meeting Transcript:
{full_text}"""

        try:
            response = requests.post(
                self.api_url,
                headers={'Content-Type': 'application/json'},
                json={
                    "model": "llama3:latest",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json()["response"]
            
        except requests.Timeout:
            return "Error: Summary generation timed out after 30 seconds"
        except requests.RequestException as e:
            return f"Error generating summary: {str(e)}"
        except Exception as e:
            return f"Unexpected error during summary generation: {str(e)}"
