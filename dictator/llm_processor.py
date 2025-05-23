"""LLM post-processing for transcribed text based on application context."""

import logging
import os
import textwrap
from typing import Optional

import litellm

from .exceptions import LLMProcessingError
from .prompt_manager import PromptManager
from .text_typer import TextTyper
from .window_detector import WindowDetector

logger = logging.getLogger(__name__)


class LLMPostProcessor:
    """Post-processes transcribed text using LLM based on application context."""

    def __init__(self, model: str = "gemini/gemini-2.0-flash"):
        """Initialize the LLM post-processor.

        Args:
            model: The LiteLLM model identifier to use for processing
        """
        self.model = model
        self.window_detector = WindowDetector()
        self.prompt_manager = PromptManager()
        self._validate_api_key()

    def _validate_api_key(self) -> None:
        """Validate that required API key is available."""
        if not os.getenv("GEMINI_API_KEY"):
            raise LLMProcessingError(
                "GEMINI_API_KEY environment variable is required for LLM post-processing"
            )

    def process_transcript(self, transcript: str) -> str:
        """Process transcript based on the currently focused application.

        Args:
            transcript: The original transcribed text

        Returns:
            Processed text, or original transcript if processing fails/not needed
        """
        try:
            # Get the context-specific prompt
            prompt = self._get_context_prompt()

            if not prompt:
                return transcript

            logger.info(
                f"Processing transcript with LLM (length: {len(transcript)} chars)"
            )
            processed_text = self._call_llm(transcript, prompt)

            if processed_text:
                logger.info(
                    f"LLM processing successful (length: {len(processed_text)} chars)"
                )
                return processed_text
            else:
                logger.warning("LLM returned empty response, using original transcript")
                return transcript

        except Exception as e:
            logger.error(f"LLM processing failed: {e}, using original transcript")
            return transcript

    def process_transcript_streaming(self, transcript: str, text_typer):
        """Process transcript with streaming output and real-time typing.

        Args:
            transcript: The original transcribed text
            text_typer: TextTyper instance for typing text chunks
        """
        try:
            # Get the context-specific prompt
            prompt = self._get_context_prompt()

            if not prompt:
                text_typer.type_text_chunk(transcript)
                return

            # Check if we should add indicator for this app
            window_info = self.window_detector.get_focused_window_info()
            app_class = window_info.get("class", "")
            add_indicator = self.prompt_manager.should_add_indicator_for_app(app_class)

            logger.info(
                f"Processing transcript with streaming LLM (length: {len(transcript)} chars)"
            )
            self._call_llm_streaming(transcript, prompt, text_typer, add_indicator)

        except Exception as e:
            logger.error(
                f"Streaming LLM processing failed: {e}, typing original transcript"
            )
            text_typer.type_text_chunk(transcript)

    def _get_context_prompt(self) -> Optional[str]:
        """Get the appropriate prompt based on the current application context.

        Returns:
            Prompt string if context-specific processing is needed, None otherwise
        """
        try:
            window_info = self.window_detector.get_focused_window_info()
            app_class = window_info.get("class", "")

            return self.prompt_manager.get_prompt_for_app(app_class)

        except Exception as e:
            logger.warning(f"Failed to determine context: {e}")
            return None

    def _call_llm(self, transcript: str, prompt_template: str) -> Optional[str]:
        """Call the LLM API to process the transcript.

        Args:
            transcript: The original transcribed text
            prompt_template: The prompt template with {transcript} and optional {window_title} placeholders

        Returns:
            Processed text from the LLM, or None if call fails
        """
        try:
            # Get window title for context-aware prompts
            window_info = self.window_detector.get_focused_window_info()
            window_title = window_info.get("name", "")

            # Format the prompt with transcript and window title
            formatted_prompt = textwrap.dedent(
                self.prompt_manager.format_prompt(
                    prompt_template, transcript, window_title
                )
            ).strip()

            # Call LiteLLM
            response = litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": formatted_prompt}],
                temperature=0.3,  # Low temperature for consistent output
                max_tokens=1000,  # Reasonable limit for transcript processing
                timeout=30,  # 30 second timeout
            )

            if response and response.choices and len(response.choices) > 0:
                processed_text = response.choices[0].message.content
                if processed_text:
                    return processed_text.strip()

            logger.warning("LLM response was empty or malformed")
            return None

        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise LLMProcessingError(f"Failed to process transcript with LLM: {e}")

    def _call_llm_streaming(
        self,
        transcript: str,
        prompt_template: str,
        text_typer: TextTyper,
        add_indicator: bool = False,
    ) -> None:
        """Call the LLM API with streaming to process the transcript.

        Args:
            transcript: The original transcribed text
            prompt_template: The prompt template with {transcript} and optional {window_title} placeholders
            text_typer: TextTyper instance for typing text chunks
            add_indicator: Whether to add LLM indicator at the end
        """
        try:
            # Get window title for context-aware prompts
            window_info = self.window_detector.get_focused_window_info()
            window_title = window_info.get("name", "")

            # Format the prompt with transcript and window title
            formatted_prompt = textwrap.dedent(
                self.prompt_manager.format_prompt(
                    prompt_template, transcript, window_title
                )
            ).strip()

            # Call LiteLLM with streaming
            response = litellm.completion(
                model=self.model,
                messages=[{"role": "user", "content": formatted_prompt}],
                temperature=0.3,  # Low temperature for consistent output
                max_tokens=1000,  # Reasonable limit for transcript processing
                timeout=30,  # 30 second timeout
                stream=True,  # Enable streaming
            )

            # Process streaming response
            chunks_processed = False
            for chunk in response:
                try:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, "content") and delta.content:
                            # Type each chunk as it arrives
                            text_typer.type_text_chunk(delta.content)
                            chunks_processed = True
                except Exception as chunk_error:
                    logger.warning(f"Error processing chunk: {chunk_error}")
                    continue

            # Add indicator at the end if configured and we processed content
            if add_indicator and chunks_processed:
                # Flush any buffered newlines before adding indicator
                text_typer.flush_remaining_content()
                indicator = self.prompt_manager.get_llm_indicator()
                logger.info(f"Adding LLM indicator: {indicator}")
                text_typer.type_text_chunk(indicator)

        except Exception as e:
            logger.error(f"Streaming LLM API call failed: {e}")
            raise LLMProcessingError(
                f"Failed to process transcript with streaming LLM: {e}"
            )

    def is_enabled(self) -> bool:
        """Check if LLM post-processing is enabled and properly configured.

        Returns:
            True if post-processing can be used, False otherwise
        """
        try:
            return bool(os.getenv("GEMINI_API_KEY"))
        except Exception:
            return False
