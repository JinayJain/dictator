"""LLM post-processing for transcribed text based on application context."""

import logging
import os
from typing import Optional

import litellm

from .exceptions import LLMProcessingError
from .prompt_manager import PromptManager
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
                logger.debug("No context-specific processing needed, returning original transcript")
                return transcript
            
            logger.info(f"Processing transcript with LLM (length: {len(transcript)} chars)")
            processed_text = self._call_llm(transcript, prompt)
            
            if processed_text:
                logger.info(f"LLM processing successful (length: {len(processed_text)} chars)")
                return processed_text
            else:
                logger.warning("LLM returned empty response, using original transcript")
                return transcript
                
        except Exception as e:
            logger.error(f"LLM processing failed: {e}, using original transcript")
            return transcript
    
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
            prompt_template: The prompt template with {transcript} placeholder
            
        Returns:
            Processed text from the LLM, or None if call fails
        """
        try:
            # Format the prompt with the transcript
            formatted_prompt = prompt_template.format(transcript=transcript)
            
            # Call LiteLLM
            response = litellm.completion(
                model=self.model,
                messages=[
                    {
                        "role": "user", 
                        "content": formatted_prompt
                    }
                ],
                temperature=0.3,  # Low temperature for consistent output
                max_tokens=1000,  # Reasonable limit for transcript processing
                timeout=30  # 30 second timeout
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
    
    def is_enabled(self) -> bool:
        """Check if LLM post-processing is enabled and properly configured.
        
        Returns:
            True if post-processing can be used, False otherwise
        """
        try:
            return bool(os.getenv("GEMINI_API_KEY"))
        except Exception:
            return False