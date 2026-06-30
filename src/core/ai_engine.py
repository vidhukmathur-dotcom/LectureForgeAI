import os
import json
import requests


class AIEngine:
    """The Model: Interacts with the Groq API to generate professional, slide-bound
    academic scripts using high-performance open-source models like Llama 3.3.

    Narration is generated in ONE call covering the whole deck (so the model
    retains full context across slides for natural narrative flow), but the
    OUTPUT FORMAT is strict JSON -- an array of per-slide strings -- rather
    than free-form text with hand-typed "--- Slide N ---" markers.

    Why this matters: with free-form text + regex parsing, slide boundaries
    were only as reliable as the model's adherence to a repeated formatting
    pattern across many sections, which degraded on longer decks (markers
    occasionally dropped, or false-positive "Slide N" mentions mid-narration
    fragmenting the wrong section). With JSON array output, slide identity
    IS the array index -- there's no marker to drop, parse, or misread.
    """

    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY", "")
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model_name = "llama-3.3-70b-versatile"

    def generate_lecture_narration(self, extracted_slide_text: str, total_slides: int) -> list:
        """
        Generates an engaging lecture script that synthesizes slide points
        naturally, returning a list of per-slide narration strings.

        Args:
            extracted_slide_text: combined text of all slides (as produced by
                PowerPointProcessor.extract_text()), with "--- Slide N ---"
                separators marking where each slide's source text begins.
            total_slides: expected number of slides, used to validate the
                response and retry once if the model returns a mismatched
                count.

        Returns:
            List[str] of length total_slides, in slide order.
        """
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY environment variable is not set. Please supply a valid Groq access key.")

        narration_list = self._request_narration(extracted_slide_text, total_slides)

        if len(narration_list) != total_slides:
            # Occasionally a structured generation still returns the wrong
            # count (e.g. the model merges or splits a section). Retry once
            # with an explicit correction nudge before falling back.
            narration_list = self._request_narration(
                extracted_slide_text,
                total_slides,
                retry_correction=(
                    f"Your previous response had {len(narration_list)} entries, "
                    f"but there are exactly {total_slides} slides. "
                    f"You MUST return exactly {total_slides} entries in the 'slides' array, "
                    f"one per slide, in order, with no merging or splitting of slides."
                ),
            )

        # If it's still wrong after the retry, pad or truncate rather than
        # crashing outright -- a slightly imperfect video is better than no
        # video, and this should be rare given the retry above.
        if len(narration_list) < total_slides:
            shortfall = total_slides - len(narration_list)
            narration_list += [
                f"Moving forward to slide {len(narration_list) + i + 1}."
                for i in range(shortfall)
            ]
        elif len(narration_list) > total_slides:
            narration_list = narration_list[:total_slides]

        return narration_list

    def _request_narration(self, extracted_slide_text, total_slides, retry_correction=None):
        system_instruction = (
            "You are an elite higher education professor delivering a professional, clear classroom lecture. "
            "Your task is to write a spoken narration script based on the extracted slide text provided below.\n\n"
            "CRITICAL CONSTRAINTS FOR BALANCED NARRATION:\n"
            "1. DO NOT JUST READ THE SLIDE: Do not read the bullet points word-for-word. Instead, synthesize, "
            "explain, and elaborate on the points naturally as a human instructor would. Use professional spoken transitions "
            "that reference earlier and upcoming slides where it aids flow, since you can see the full deck's content below.\n"
            "2. STAY ANCHORED TO THE FACTS: While you should explain the text naturally, you must NOT introduce "
            "completely new external data, outside anecdotes, or ungrounded case examples.\n"
            f"3. MATCH SLIDE COUNT EXACTLY: The presentation has exactly {total_slides} slides. "
            f"You MUST return exactly {total_slides} entries in the JSON array below -- one per slide, in order. "
            "Do not skip, merge, or split slides.\n\n"
            "STRICT OUTPUT FORMAT — JSON ONLY:\n"
            "Respond with ONLY a single JSON object, no other text before or after it, no markdown code fences, "
            "in exactly this shape:\n"
            '{"slides": ["narration text for slide 1", "narration text for slide 2", ...]}\n'
            f"The 'slides' array must have exactly {total_slides} string elements."
        )

        user_content = f"Here is the extracted slide text source material:\n{extracted_slide_text}"
        if retry_correction:
            user_content = f"{retry_correction}\n\n{user_content}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.3,
            # Groq supports OpenAI-compatible structured output mode for
            # several models, which constrains the response to valid JSON
            # at the API level rather than relying purely on prompt
            # instructions. If your model/account doesn't support this
            # parameter, remove it -- the prompt instructions above are
            # still a strong fallback on their own.
            "response_format": {"type": "json_object"},
        }

        try:
            response = requests.post(self.base_url, json=payload, headers=headers, timeout=120)
            response_data = response.json()

            if response.status_code != 200:
                error_msg = response_data.get("error", {}).get("message", "Unknown API breakdown.")
                raise RuntimeError(f"Groq API Refusal ({response.status_code}): {error_msg}")

            raw_content = response_data["choices"][0]["message"]["content"].strip()

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to reach Groq API: {str(e)}")
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected Groq API response shape: {str(e)}")

        return self._parse_narration_json(raw_content)

    def _parse_narration_json(self, raw_content: str) -> list:
        """
        Parses the model's JSON response into a list of narration strings.
        Tolerates the model occasionally wrapping the JSON in markdown code
        fences despite instructions not to, since that's a common minor
        deviation worth defending against rather than crashing on.
        """
        cleaned = raw_content.strip()

        # Strip markdown code fences if present (```json ... ``` or ``` ... ```)
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1] if cleaned.count("```") >= 2 else cleaned.strip("`")
            cleaned = cleaned.strip()
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Groq returned a response that wasn't valid JSON, even after cleanup. "
                f"Parse error: {str(e)}. Raw response started with: {raw_content[:200]!r}"
            )

        slides = parsed.get("slides")
        if not isinstance(slides, list):
            raise RuntimeError(
                f"Groq's JSON response didn't contain a 'slides' array as expected. "
                f"Got keys: {list(parsed.keys()) if isinstance(parsed, dict) else type(parsed)}"
            )

        return [str(s).strip() for s in slides]
