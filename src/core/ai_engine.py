import os
import requests

class AIEngine:
    """The Model: Interacts with the Groq API to generate professional, slide-bound 
    academic scripts using high-performance open-source models like Llama 3.3.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY", "")
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model_name = "llama-3.3-70b-versatile"

    def generate_lecture_narration(self, extracted_slide_text: str) -> str:
        """Generates an engaging lecture script that synthesizes slide points naturally 
        without wandering off into ungrounded tangents or simply reading text aloud.
        """
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY environment variable is not set. Please supply a valid Groq access key.")

        system_instruction = (
            "You are an elite higher education professor delivering a professional, clear classroom lecture. "
            "Your task is to write a spoken narration script based on the extracted slide text provided below.\n\n"
            "CRITICAL CONSTRAINTS FOR BALANCED NARRATION:\n"
            "1. DO NOT JUST READ THE SLIDE: Do not read the bullet points word-for-word. Instead, synthesize, "
            "explain, and elaborate on the points naturally as a human instructor would. Use professional spoken transitions.\n"
            "2. STAY ANCHORED TO THE FACTS: While you should explain the text naturally, you must NOT introduce "
            "completely new external data, outside anecdotes, or ungrounded case examples.\n"
            "3. MATCH SLIDE COUNT: Provide an explicit entry for every single slide. Do not skip or combine slide data.\n\n"
            "STRICT FORMATTING OUTPUT RULE:\n"
            "Separate each slide's script using the exact marker formatting shown below. Use this layout:\n"
            "--- Slide 1 ---\n"
            "[Write the synthesized, professional lecture narration text here]\n"
            "--- Slide 2 ---\n"
            "[Write the synthesized, professional lecture narration text here]\n"
        )
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Here is the extracted slide text source material:\n{extracted_slide_text}"}
            ],
            "temperature": 0.3
        }
        
        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            response_data = response.json()
            
            if response.status_code == 200:
                return response_data["choices"][0]["message"]["content"].strip()
            else:
                error_msg = response_data.get("error", {}).get("message", "Unknown API breakdown.")
                raise RuntimeError(f"Groq API Refusal ({response.status_code}): {error_msg}")
                
        except Exception as e:
            print(f"🚨 Groq Script Generation Error: {str(e)}")
            raise RuntimeError(f"Failed to compile script text via Groq AI: {str(e)}")