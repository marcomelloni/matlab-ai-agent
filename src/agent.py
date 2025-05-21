"""
Main agent implementation for the MATLAB AI Agent.

This module contains the core MatlabAIAgent class that orchestrates the generation,
validation, and execution of MATLAB code.
"""

from typing import List, Optional, Callable, Dict

from .engine import MatlabEngine
from .llm import LLMInterface
from .utils.logger import logger, LogLevel


class MatlabAIAgent:
    """
    AI-powered agent for MATLAB code generation and execution.

    This class provides the main interface for generating MATLAB code using LLMs,
    validating it with MATLAB's linting tools, and executing simulations.
    """

    def __init__(self, matlab_startup: bool = True, verbose: bool = False):
        """
        Initialize the MATLAB AI Agent.

        Args:
            matlab_startup: Whether to start the MATLAB engine during initialization.
            verbose: Whether to print verbose output during operations.
        """
        logger.debug(
            f"Initializing MatlabAIAgent (matlab_startup={matlab_startup}, verbose={verbose})")
        self.conversation_history = []
        self.matlab_code = ""
        self.mlint_results = []
        self.simulation_results = {}
        self.verbose = verbose

        # Set logging level based on verbosity
        if verbose:
            logger.set_level(LogLevel.DEBUG.value)
            logger.debug("Verbose mode enabled - setting log level to DEBUG")

        # Initialize components
        try:
            logger.debug("Initializing LLM interface")
            self.llm = LLMInterface()
            logger.success("LLM interface initialized successfully")
        except Exception as e:
            logger.critical(f"Failed to initialize LLM interface: {e}")
            raise

        try:
            logger.debug(
                f"Initializing MATLAB engine (startup={matlab_startup})")
            self.matlab = MatlabEngine(startup=matlab_startup)

            if self.matlab.is_available:
                logger.success("MATLAB Engine initialized successfully")
            else:
                logger.warning("MATLAB Engine not available")
                if self.verbose:
                    print(
                        "MATLAB Engine not available. Code will be generated but not executed.")
        except Exception as e:
            logger.error(f"Failed to initialize MATLAB engine: {e}")
            if self.verbose:
                print(f"Failed to initialize MATLAB engine: {e}")

    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation history.

        Args:
            role: The role of the message sender ('user' or 'assistant').
            content: The content of the message.
        """
        logger.debug(
            f"Adding message with role '{role}' ({len(content)} chars)")
        self.conversation_history.append({"role": role, "content": content})

    def generate_matlab_code(
            self,
            prompt: str,
            progress_callback: Optional[Callable[[int], None]] = None
    ) -> str:
        """
        Generate MATLAB code using the LLM based on the provided prompt.

        Args:
            prompt: The description of the MATLAB code to generate.
            progress_callback: Optional callback function for progress updates

        Returns:
            The generated MATLAB code as a string.
        """
        logger.info("Generating MATLAB code from prompt")
        logger.debug(f"Prompt: {prompt[:50]}...")

        if self.verbose:
            print("Generating MATLAB code...")

        self.matlab_code = self.llm.generate_code(
            prompt,
            conversation_history=self.conversation_history,
            progress_callback=progress_callback
        )

        logger.success(
            f"Code generation complete ({len(self.matlab_code)} chars)")

        return self.matlab_code

    def validate_with_mlint(self) -> List[str]:
        """
        Validate the generated MATLAB code using MATLAB's linting tools.

        Returns:
            A list of error/warning messages from the linting process.
        """
        logger.info("Validating MATLAB code with mlint")

        if self.verbose:
            print("Validating MATLAB code with mlint...")

        self.mlint_results = self.matlab.validate_code(self.matlab_code)

        if not self.mlint_results or self.mlint_results == [
                "No issues found."]:
            logger.success("Validation successful: No errors or warnings")
            if self.verbose:
                print("✅ Validation successful: No errors or warnings.")
        else:
            logger.warning(
                f"Validation found {len(self.mlint_results)} issues")
            if self.verbose:
                print(f"⚠️ Validation found {len(self.mlint_results)} issues.")

        return self.mlint_results

    def execute_simulation(
            self,
            progress_callback: Optional[Callable[[int], None]] = None
    ) -> str:
        """
        Execute the MATLAB simulation.

        Args:
            progress_callback: Optional callback function for progress updates

        Returns:
            A string describing the execution result.
        """
        logger.debug("Executing MATLAB simulation")

        result, self.simulation_results = self.matlab.execute_code(
            self.matlab_code, progress_callback=progress_callback)

        if self.simulation_results.get("success", False):
            figure_path = self.simulation_results.get("figure")
            if figure_path:
                logger.info(f"Figure saved to: {figure_path}")
        else:
            error = self.simulation_results.get("error", "Unknown error")
            logger.error(f"Simulation execution failed: {error}")

        return result

    def fix_code_with_llm(
            self,
            error_messages: List[str],
            progress_callback: Optional[Callable[[int], None]] = None
    ) -> str:
        """
        Use the LLM to fix errors in the MATLAB code.

        Args:
            error_messages: A list of error messages to address.
            progress_callback: Optional callback function for progress updates

        Returns:
            The fixed MATLAB code.
        """
        if not error_messages:
            logger.info("No errors to fix in the code")
            return self.matlab_code

        logger.info(
            f"Attempting to fix {len(error_messages)} code issues with LLM")
        for error in error_messages:
            logger.debug(f"Error to fix: {error}")

        if self.verbose:
            print("Attempting to fix code with LLM...")

        original_code_length = len(self.matlab_code)
        self.matlab_code = self.llm.fix_code(
            self.matlab_code,
            error_messages,
            progress_callback=progress_callback
        )

        if len(self.matlab_code) != original_code_length:
            logger.success("Code fixing complete with changes")
            logger.debug(
                f"Code length changed from {original_code_length} to {len(self.matlab_code)}")
        else:
            logger.info("Code fixing complete (no changes detected)")

        if self.verbose:
            print("Code fixing complete.")

        return self.matlab_code

    def __del__(self):
        """Clean up resources when the object is destroyed."""
        logger.debug("MatlabAIAgent being destroyed, cleaning up resources")
        if hasattr(self, "matlab"):
            self.matlab.shutdown()
