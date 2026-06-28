import os
import time
import re
import asyncio
import edge_tts

class AudioGenerator:
    """The Model: Responsible for converting text scripts into premium, high-fidelity 
    neural MP3 audio tracks using Microsoft's cloud voice matrix.
    """

    def generate_slide_audio(self, text: str, output_path: str, voice_profile: str = "en-US-BrianNeural", max_retries: int = 3) -> bool:
        """Runs the asynchronous neural voice generation stream inside a synchronous wrapper."""
        # Sanitize text boundaries cleanly to strip raw markdown formatting out
        clean_text = re.sub(r'[\*#_~`>+\-\[\]\(\)]', ' ', text if text else "")
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        if not clean_text:
            clean_text = "Moving forward to the next presentation slide."

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Execute the async downloader safely inside the thread context loop
        for attempt in range(1, max_retries + 1):
            try:
                asyncio.run(self._download_neural_stream(clean_text, voice_profile, output_path))
                
                # Verify successful file compilation tracking
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return True
            except Exception as e:
                print(f"⚠️ Neural voice engine attempt {attempt} failed: {str(e)}")
                if attempt < max_retries:
                    time.sleep(1.5)
                continue

        # Widescreen Fallback Safeguard
        print(f"❌ Premium voice array exhausted. Generating fallback asset placeholder.")
        try:
            asyncio.run(self._download_neural_stream("Next slide.", "en-US-BrianNeural", output_path))
            return True
        except Exception as err:
            print(f"🚨 Master fallback failure: {str(err)}")
            return False

    async def _download_neural_stream(self, text: str, voice: str, path: str):
        """Streams high-quality cognitive voice models down to physical audio storage formats."""
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(path)