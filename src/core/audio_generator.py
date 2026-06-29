import os
import asyncio
import edge_tts

class AudioGenerator:
    def __init__(self):
        pass

    def generate_slide_audio(self, text, output_path, voice_profile="en-US-BrianNeural"):
        """
        Synthesizes script strings into high-fidelity neural audio formats asynchronously.
        """
        # Ensure target subdirectories exist natively before writing output files
        target_dir = os.path.dirname(output_path)
        os.makedirs(target_dir, exist_ok=True)
        
        async def _synthesize():
            communicate = edge_tts.Communicate(text, voice_profile)
            await communicate.save(output_path)
            
        # Run the asynchronous edge-tts operations inside the pipeline loop
        asyncio.run(_synthesize())
        return output_path
