"""
LLM interface for the MATLAB AI Agent.

This module handles interactions with the OpenAI API for code generation
and error correction.
"""

import os
import pathlib
from typing import Dict, List, Optional, Callable

from openai import OpenAI
from dotenv import load_dotenv
from .utils.prompt_generator import generate_prompt
from .utils.logger import logger


class LLMInterface:
    """
    Interface to language models for MATLAB code generation and error correction.

    This class handles interactions with the OpenAI API, including formatting
    prompts and parsing responses.
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize the LLM interface.

        Args:
            model: The name of the OpenAI model to use.
        """
        logger.debug(f"Initializing LLMInterface with model: {model}")

        # Load environment variables
        load_dotenv()

        # Check for API key
        if not os.getenv("OPENAI_API_KEY"):
            logger.warning("OPENAI_API_KEY not found in environment variables")

        # Initialize OpenAI client
        try:
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            logger.debug("OpenAI client initialized")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
            raise

        self.model = model
        self.system_message = self._load_system_prompt()
        logger.debug(
            f"System prompt loaded ({len(self.system_message)} characters)")

    def _load_system_prompt(self) -> str:
        """
        Load system prompt from external file or generate default.

        Returns:
            The loaded system prompt as a string.
        """
        prompt_file = pathlib.Path(".matlab_ai_prompt")

        if prompt_file.exists():
            logger.debug(f"Loading system prompt from {prompt_file}")
            return prompt_file.read_text(encoding="utf-8")

        logger.info("System prompt file not found, generating default")
        generate_prompt()
        logger.success(f"Default system prompt generated at {prompt_file}")
        return prompt_file.read_text(encoding="utf-8")

    def generate_code(
            self,
            prompt: str,
            conversation_history: Optional[List[Dict[str, str]]] = None,
            progress_callback: Optional[Callable[[int], None]] = None
    ) -> str:
        """
        Generate MATLAB code based on the provided prompt.

        Args:
            prompt: The prompt describing the code to generate
            conversation_history: Optional conversation history for context
            progress_callback: Optional callback function for progress updates

        Returns:
            Generated MATLAB code as string
        """
        logger.debug(f"Prompt summary: {prompt[:50]}...")

        if progress_callback:
            progress_callback(10)  # Starting code generation

        messages = [{"role": "system", "content": self.system_message}]

        if conversation_history:
            messages.extend(conversation_history)
            logger.debug(
                f"Added {len(conversation_history)} messages from conversation history")

        messages.append(
            {"role": "user", "content": f"Generate MATLAB code for: {prompt}"})

        if progress_callback:
            progress_callback(20)  # Messages prepared

        try:
            logger.debug(f"Calling OpenAI API with model: {self.model}")

            if progress_callback:
                progress_callback(30)  # API call started

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=2000
            )

            if progress_callback:
                progress_callback(70)  # API call completed

            code = response.choices[0].message.content.strip()
            logger.debug(f"Received {len(code)} characters of code from API")

            if progress_callback:
                progress_callback(90)  # Processing response

            cleaned_code = self._clean_code(code)

            if progress_callback:
                progress_callback(100)  # Complete

            return cleaned_code
        except Exception as e:
            logger.error(f"Error generating code: {e}")

            if progress_callback:
                progress_callback(100)  # Complete (but with error)

            return f"% Error generating code: {e}"

    def fix_code(
            self,
            code: str,
            error_messages: List[str],
            progress_callback: Optional[Callable[[int], None]] = None
    ) -> str:
        """
        Fix MATLAB code based on error messages.

        Args:
            code: The original MATLAB code.
            error_messages: A list of error messages to address.
            progress_callback: Optional callback function for progress updates

        Returns:
            Fixed MATLAB code.
        """
        logger.info(f"Fixing code with {len(error_messages)} error messages")

        if progress_callback:
            progress_callback(10)  # Starting code fixing

        system_message = """
        You are an expert MATLAB programmer specializing in fixing code errors.
        Correct the provided MATLAB code based on the error messages.
        Return ONLY the corrected code without explanations.
        """

        prompt = f"""
        The following MATLAB code has errors:

        ```matlab
        {code}
        ```

        Error messages:
        {' '.join(error_messages)}

        Please fix the code and return ONLY the corrected version.
        """

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]

        logger.debug("Prepared messages for code fixing")

        if progress_callback:
            progress_callback(30)  # Messages prepared

        try:
            logger.debug(f"Calling OpenAI API with model: {self.model}")

            if progress_callback:
                progress_callback(40)  # API call started

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=2000
            )

            if progress_callback:
                progress_callback(80)  # API call completed

            fixed_code = response.choices[0].message.content.strip()
            logger.debug(
                f"Received {len(fixed_code)} characters of fixed code")

            # Clean up the code (remove markdown if present)
            clean_code = self._clean_code(fixed_code)

            if progress_callback:
                progress_callback(100)  # Complete

            return clean_code
        except Exception as e:
            logger.error(f"Error fixing code: {e}")

            if progress_callback:
                progress_callback(100)  # Complete (but with error)

            return code  # Return original code if fixing fails

    @staticmethod
    def _clean_code(code: str) -> str:
        """
        Clean up code by removing markdown formatting if present.

        Args:
            code: Code that might contain markdown formatting.

        Returns:
            Clean code without markdown formatting.
        """
        # Remove markdown code blocks
        if code.startswith("```matlab"):
            code = code[10:]
        elif code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]

        return code.strip()
