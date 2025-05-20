"""
LLM interface for the MATLAB AI Agent.

This module handles interactions with the OpenAI API for code generation
and error correction.
"""

import os
import re
from typing import Dict, List, Optional

import openai
from openai import OpenAI
from dotenv import load_dotenv


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
        # Load environment variables
        load_dotenv()

        # Initialize OpenAI client
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def generate_code(
        self, prompt: str, conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate MATLAB code based on the provided prompt.

        Args:
            prompt: The description of the MATLAB code to generate.
            conversation_history: Optional conversation history for context.

        Returns:
            Generated MATLAB code as a string.
        """
        system_message = """
        You are an expert MATLAB programmer specializing in generating code for simulations.
        Generate ONLY clean, optimized, and functional MATLAB code based on the user's description.
        Do not include explanations or introductory/concluding comments, just MATLAB code with appropriate in-code comments.
        For ODE simulations, use ode45 or ode15s functions and always produce a graphical visualization.
        """

        messages = [
            {"role": "system", "content": system_message}
        ]

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add the current prompt
        messages.append(
            {"role": "user", "content": f"Generate MATLAB code for: {prompt}"})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=2000
            )
            code = response.choices[0].message.content.strip()

            # Clean up the code (remove markdown if present)
            return self._clean_code(code)
        except Exception as e:
            print(f"Error generating code: {e}")
            return f"% Error generating code: {e}"

    def fix_code(self, code: str, error_messages: List[str]) -> str:
        """
        Fix MATLAB code based on error messages.

        Args:
            code: The original MATLAB code.
            error_messages: A list of error messages to address.

        Returns:
            Fixed MATLAB code.
        """
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

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=2000
            )
            fixed_code = response.choices[0].message.content.strip()

            # Clean up the code (remove markdown if present)
            return self._clean_code(fixed_code)
        except Exception as e:
            print(f"Error fixing code: {e}")
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
