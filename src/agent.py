"""
Main agent implementation for the MATLAB AI Agent.

This module contains the core MatlabAIAgent class that orchestrates the generation,
validation, and execution of MATLAB code.
"""

from typing import List
from .engine import MatlabEngine
from .llm import LLMInterface

class MatlabAIAgent:
    """
    AI-powered agent for MATLAB code generation and execution.

    This class provides the main interface for generating MATLAB code using LLMs,
    validating it with MATLAB's linting tools, and executing simulations.
    """

    def __init__(self, matlab_startup: bool = True, verbose: bool = True):
        """
        Initialize the MATLAB AI Agent.

        Args:
            matlab_startup: Whether to start the MATLAB engine during initialization.
            verbose: Whether to print verbose output during operations.
        """
        self.conversation_history = []
        self.matlab_code = ""
        self.mlint_results = []
        self.simulation_results = {}
        self.verbose = verbose

        # Initialize components
        self.llm = LLMInterface()
        self.matlab = MatlabEngine(startup=matlab_startup)

        if self.verbose and self.matlab.is_available:
            print("MATLAB Engine started successfully.")
        elif self.verbose:
            print("MATLAB Engine not available. Code will be generated but not executed.")

    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation history.

        Args:
            role: The role of the message sender ('user' or 'assistant').
            content: The content of the message.
        """
        self.conversation_history.append({"role": role, "content": content})

    def generate_matlab_code(self, prompt: str) -> str:
        """
        Generate MATLAB code using the LLM based on the provided prompt.

        Args:
            prompt: The description of the MATLAB code to generate.

        Returns:
            The generated MATLAB code as a string.
        """
        if self.verbose:
            print("Generating MATLAB code...")

        self.matlab_code = self.llm.generate_code(
            prompt, conversation_history=self.conversation_history
        )

        if self.verbose:
            print("Code generation complete.")

        return self.matlab_code

    def validate_with_mlint(self) -> List[str]:
        """
        Validate the generated MATLAB code using MATLAB's linting tools.

        Returns:
            A list of error/warning messages from the linting process.
        """
        if self.verbose:
            print("Validating MATLAB code with mlint...")

        self.mlint_results = self.matlab.validate_code(self.matlab_code)

        if self.verbose:
            if not self.mlint_results:
                print("✅ Validation successful: No errors or warnings.")
            else:
                print(f"⚠️ Validation found {len(self.mlint_results)} issues.")

        return self.mlint_results

    def execute_simulation(self) -> str:
        """
        Execute the MATLAB simulation.

        Returns:
            A string describing the execution result.
        """
        if self.verbose:
            print("Executing MATLAB simulation...")

        result, self.simulation_results = self.matlab.execute_code(self.matlab_code)

        if self.verbose:
            if self.simulation_results.get("success", False):
                print("✅ Simulation executed successfully.")
                if self.simulation_results.get("figure"):
                    print(f"Figure saved to: {self.simulation_results['figure']}")
            else:
                print(f"❌ Simulation execution failed: {result}")

        return result

    def fix_code_with_llm(self, error_messages: List[str]) -> str:
        """
        Use the LLM to fix errors in the MATLAB code.

        Args:
            error_messages: A list of error messages to address.

        Returns:
            The fixed MATLAB code.
        """
        if not error_messages:
            return self.matlab_code

        if self.verbose:
            print("Attempting to fix code with LLM...")

        self.matlab_code = self.llm.fix_code(self.matlab_code, error_messages)

        if self.verbose:
            print("Code fixing complete.")

        return self.matlab_code

    def __del__(self):
        """Clean up resources when the object is destroyed."""
        if hasattr(self, "matlab"):
            self.matlab.shutdown()