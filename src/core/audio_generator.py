import os
import re
import asyncio
import edge_tts


def _sanitize_for_tts(text: str) -> str:
    """
    Strips emoji and other characters that edge-tts's underlying transport
    has been observed to choke on with encoding errors.
    """
    if not text:
        return text

    emoji_pattern = re.compile(
        "["
        "\U0001F300-\U0001FAFF"
        "\U00002600-\U000027BF"
        "\U0001F1E6-\U0001F1FF"
        "\U00002190-\U000021FF"
        "\U00002B00-\U00002BFF"
        "\U0000FE0F"
        "]+",
        flags=re.UNICODE,
    )
    cleaned = emoji_pattern.sub("", text)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned).strip()
    return cleaned


class AudioGenerator:
    def __init__(self):
        pass

    def generate_slide_audio(self, text, output_path, voice_profile="en-US-BrianNeural"):
        """
        Synthesizes a single script string into audio. Sequential, blocking.
        """
        target_dir = os.path.dirname(output_path)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)

        safe_text = _sanitize_for_tts(text)
        if not safe_text.strip():
            safe_text = "This slide contains a visual element. Let us take a moment before moving on."

        async def _synthesize():
            communicate = edge_tts.Communicate(safe_text, voice_profile)
            await communicate.save(output_path)

        asyncio.run(_synthesize())

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError(f"TTS produced no output for: {output_path}")

        print(f"[Audio] OK slide -> {os.path.basename(output_path)} ({os.path.getsize(output_path)} bytes)")
        return output_path

    def generate_all_slide_audio(self, slide_scripts, audio_dir, voice_profile="en-US-BrianNeural", max_concurrent=6):
        """
        Sequential fallback: generates audio one slide at a time.
        Slower than concurrent but completely reliable -- no asyncio.gather,
        no semaphore, no shared event loop state between slides.
        Each slide gets its own clean asyncio.run() call.
        """
        os.makedirs(audio_dir, exist_ok=True)

        output_paths = []
        failures = []

        for idx, text in enumerate(slide_scripts, start=1):
            output_path = os.path.join(audio_dir, f"slide_{idx}.mp3")
            try:
                self.generate_slide_audio(text, output_path, voice_profile)
                output_paths.append(output_path)
            except Exception as e:
                print(f"[Audio] FAILED slide {idx}: {type(e).__name__}: {e}")
                failures.append((idx, str(e)))

        if failures:
            details = "; ".join(f"slide {n}: {err}" for n, err in failures)
            raise RuntimeError(
                f"Audio generation failed for {len(failures)} of {len(slide_scripts)} "
                f"slide(s). Details: {details}"
            )

        return output_paths
