"""
LLM Client — Google Gemini integration (gemini-3.6-flash).

Wraps the Google GenAI SDK with structured prompt templates,
JSON-mode parsing, and error handling for the agent pipeline.
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any

from google import genai
from google.genai import types
from loguru import logger
from dotenv import load_dotenv

load_dotenv(override=True)


class GeminiClient:
    """Thin wrapper around the Google GenAI SDK for structured agent interactions."""

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your-gemini-api-key-here":
            raise EnvironmentError(
                "GEMINI_API_KEY is not set. Add your key to the .env file."
            )
        self.client = genai.Client(api_key=api_key)
        self.primary_model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        self.light_model = os.getenv("GEMINI_LIGHT_MODEL", "gemini-3.5-flash-lite")
        logger.info(f"GeminiClient models: Primary={self.primary_model}, Light={self.light_model}")

    def generate(self, prompt: str, system_instruction: str = "", model: str = None) -> str:
        """Generate a plain-text response with fallback."""
        preferred_model = model or self.primary_model
        fallback_model = self.light_model if preferred_model == self.primary_model else self.primary_model

        config = types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=8192,
        )
        if system_instruction:
            config.system_instruction = system_instruction

        try:
            response = self.client.models.generate_content(
                model=preferred_model,
                contents=prompt,
                config=config,
            )
            return response.text.strip()
        except Exception as e:
            # Scrub API key from any error messages to prevent console leaks
            error_msg = str(e).replace(self.client.api_key, "********") if getattr(self, 'client', None) and hasattr(self.client, 'api_key') else str(e)
            logger.warning(f"Generation failed with {preferred_model}: {error_msg}")
            logger.info(f"Retrying with fallback model: {fallback_model} in 2s...")
            time.sleep(2)
            try:
                response = self.client.models.generate_content(
                    model=fallback_model,
                    contents=prompt,
                    config=config,
                )
                return response.text.strip()
            except Exception as fallback_err:
                error_msg = str(fallback_err).replace(self.client.api_key, "********") if getattr(self, 'client', None) and hasattr(self.client, 'api_key') else str(fallback_err)
                logger.error(f"Fallback generation failed: {error_msg}")
                raise RuntimeError(f"LLM generation failed on both models") from fallback_err

    def generate_json(self, prompt: str, system_instruction: str = "", model: str = None) -> dict[str, Any]:
        """Generate a response and parse it as JSON with fallback."""
        preferred_model = model or self.primary_model
        fallback_model = self.light_model if preferred_model == self.primary_model else self.primary_model

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.7,
            max_output_tokens=8192,
        )
        if system_instruction:
            config.system_instruction = system_instruction

        try:
            response = self.client.models.generate_content(
                model=preferred_model,
                contents=prompt,
                config=config,
            )
            return self._parse_json(response.text.strip())
        except Exception as e:
            error_msg = str(e).replace(self.client.api_key, "********") if getattr(self, 'client', None) and hasattr(self.client, 'api_key') else str(e)
            logger.warning(f"JSON Generation failed with {preferred_model}: {error_msg}")
            logger.info(f"Retrying JSON with fallback model: {fallback_model} in 2s...")
            time.sleep(2)
            try:
                response = self.client.models.generate_content(
                    model=fallback_model,
                    contents=prompt,
                    config=config,
                )
                return self._parse_json(response.text.strip())
            except Exception as fallback_err:
                error_msg = str(fallback_err).replace(self.client.api_key, "********") if getattr(self, 'client', None) and hasattr(self.client, 'api_key') else str(fallback_err)
                logger.error(f"Fallback JSON generation failed: {error_msg}")
                raise RuntimeError(f"LLM JSON generation failed on both models") from fallback_err

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        """Parse JSON from raw text, handling markdown fences if present."""
        # Strip markdown code fences if the LLM wraps the output
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return json.loads(cleaned)
