"""
MATLAB engine interface for the MATLAB AI Agent.

This module provides functionality to interact with MATLAB,
including code validation and execution.
"""

import hashlib
import os
import tempfile
import time
import unicodedata
from typing import Dict, List, Tuple, Union, Optional, Callable

from .utils.logger import logger


class MatlabEngine:
    """
    Interface to MATLAB Engine for code validation and execution.

    This class handles all interactions with the MATLAB engine,
    including starting and stopping the engine, validating code,
    and executing simulations.
    """

    def __init__(self, startup: bool = True):
        """
        Initialize the MATLAB Engine interface.

        Args:
            startup: Whether to start the MATLAB engine during initialization.
        """
        logger.debug("Initializing MatlabEngine")
        self.is_available = False
        self.eng = None

        if startup:
            self._start_engine()

    def _start_engine(self) -> bool:
        """
        Start the MATLAB Engine.

        Returns:
            True if the engine started successfully, False otherwise.
        """
        logger.info("Starting MATLAB Engine")
        try:
            # Import here to avoid requiring matlab as a dependency for the
            # package
            import matlab.engine  # pylint: disable=import-outside-toplevel

            self.eng = matlab.engine.start_matlab()
            self.is_available = True
            logger.debug("MATLAB Engine started successfully")
            return True
        except ImportError:
            logger.warning(
                "MATLAB Engine not available. "
                "Install the MATLAB Engine API for Python to enable execution."
            )
            self.is_available = False
            return False
        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Error starting MATLAB Engine: {e}")
            self.is_available = False
            return False

    def validate_code(self, code: str) -> List[str]:
        """
        Validate MATLAB code using MATLAB's checkcode (mlint).

        Args:
            code: MATLAB code to validate.

        Returns:
            A list of error/warning messages from the validation process.
        """
        logger.info("Validating MATLAB code with checkcode (mlint)")
        if not self.is_available or not self.eng:
            logger.warning("MATLAB Engine not available for validation")
            return ["MATLAB Engine not available."]

        if not code:
            logger.warning("No code provided for validation")
            return ["No code to validate."]

        # Create a unique identifier for the script
        unique_id = hashlib.md5(
            (code + str(time.time())).encode()).hexdigest()[:8]
        script_name = f"validate_script_{unique_id}"
        temp_dir = tempfile.gettempdir()
        script_path = os.path.join(temp_dir, f"{script_name}.m")

        logger.debug(
            f"Creating temporary script for validation: {script_path}")
        try:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(code)

            logger.debug("Running MATLAB checkcode")
            messages = self.eng.checkcode(
                script_path.replace(
                    os.sep, '/'), nargout=1)

            mlint_results = []
            for msg in messages:
                mlint_results.append(f"[Line {msg.line}] {msg.message}")
                logger.debug(f"Validation issue: [Line {msg.line}] {msg.message}")

            if not mlint_results:
                logger.success("No validation issues found")
                return ["No issues found."]

            logger.info(f"Found {len(mlint_results)} validation issues")
            return mlint_results

        except Exception as e:  # pylint: disable=broad-except
            logger.error(f"Error during code validation: {e}")
            return [f"Error during validation: {e}"]
        finally:
            # Clean up
            if os.path.exists(script_path):
                try:
                    logger.debug(f"Removing temporary script: {script_path}")
                    os.unlink(script_path)
                except Exception as e:  # pylint: disable=broad-except
                    logger.debug(f"Failed to remove temporary script: {e}")

    def execute_code(
            self, code: str, progress_callback: Optional[Callable[[int], None]] = None
    ) -> Tuple[str, Dict[str, Union[str, bool, None]]]:
        """
        Execute MATLAB code and capture the results.

        Args:
            code: MATLAB code to execute.
            progress_callback: Optional callback function for progress updates

        Returns:
            A tuple containing:
                - A message describing the execution result
                - A dictionary with detailed execution results
        """
        if progress_callback:
            progress_callback(5)  # Started execution process

        if not self.is_available or not self.eng:
            logger.warning("MATLAB Engine not available for execution")
            if progress_callback:
                progress_callback(100)  # Complete (but with error)
            return "MATLAB Engine not available.", {
                "success": False,
                "error": "MATLAB Engine not available."
            }

        if not code:
            logger.warning("No code provided for execution")
            if progress_callback:
                progress_callback(100)  # Complete (but with error)
            return "No code to execute.", {
                "success": False,
                "error": "No code provided."
            }

        # Clean the code to ensure compatibility
        logger.debug("Cleaning code for execution")
        cleaned_code = self._clean_ascii(code)
        if progress_callback:
            progress_callback(10)  # Code cleaned

        # Create a unique identifier for the script
        unique_id = hashlib.md5(
            (code + str(time.time())).encode()).hexdigest()[:8]
        script_name = f"sim_script_{unique_id}"
        current_dir = os.getcwd()
        results_dir_name = f"matlab_results_{unique_id}"
        results_dir = os.path.join(current_dir, results_dir_name)
        os.makedirs(results_dir, exist_ok=True)
        script_path = os.path.join(results_dir, f"{script_name}.m")

        logger.debug(f"Created execution directory: {results_dir}")
        logger.debug(f"Created script file: {script_path}")

        if progress_callback:
            progress_callback(15)  # Files created

        try:
            with open(script_path, 'w', encoding='utf-8') as script_file:
                script_file.write(cleaned_code)

            logger.debug("Preparing MATLAB execution commands")
            output_path = os.path.join(
                results_dir, 'output.txt').replace(
                os.sep, '/')
            figure_path = os.path.join(
                results_dir, 'figure.png').replace(
                os.sep, '/')
            results_dir_matlab = results_dir.replace(os.sep, '/')

            matlab_commands = [
                f"cd('{results_dir_matlab}')",
                f"addpath('{results_dir_matlab}')",
                "try",
                f"    diary('{output_path}')",
                f"    {script_name}",
                "    diary off",
                "    if ~isempty(findall(0,'Type','Figure'))",
                f"        saveas(gcf, '{figure_path}')",
                "    end",
                "    error_msg = '';",
                "catch ME",
                "    diary off",
                "    error_msg = ME.message;",
                "end",
                f"rmpath('{results_dir_matlab}')"
            ]

            # Join commands and execute
            matlab_script = "; ".join(matlab_commands)
            if progress_callback:
                progress_callback(20)  # Starting execution

            logger.debug("Executing MATLAB script")
            self.eng.eval(matlab_script, nargout=0)

            error_msg = self.eng.eval("error_msg", nargout=1)
            success = not error_msg

            if progress_callback:
                progress_callback(70)  # Execution completed

            # Check for error message
            logger.debug("Checking execution result")

            # Check for output and figure
            output_path = os.path.join(results_dir, "output.txt")
            figure_path = os.path.join(results_dir, "figure.png")

            if progress_callback:
                progress_callback(80)  # Processing results

            # Prepare result
            result = {
                "script_executed": script_name,
                "success": success,
                "output": output_path if os.path.exists(output_path) else None,
                "figure": figure_path if os.path.exists(figure_path) else None,
                "error": error_msg if error_msg else None
            }

            if success:
                message = "Simulation executed successfully."
            else:
                message = f"Simulation failed: {error_msg}"

            if progress_callback:
                progress_callback(100)  # Complete

            return message, result

        except Exception as e:  # pylint: disable=broad-except
            if progress_callback:
                progress_callback(100)
            # Ensure message is always assigned before return
            message = f"Error: {str(e)}"
            return message, {
                "script_executed": script_name,
                "success": False,
                "error": str(e)
            }
        finally:
            # Clean up the script file but leave the results
            if os.path.exists(script_path):
                try:
                    logger.debug(f"Removing script file: {script_path}")
                    os.unlink(script_path)
                except Exception as e:  # pylint: disable=broad-except
                    logger.debug(f"Failed to remove script file: {e}")

    def shutdown(self) -> None:
        """Shutdown the MATLAB Engine."""
        if self.is_available and self.eng:
            try:
                logger.info("Shutting down MATLAB Engine")
                self.eng.quit()
                logger.success("MATLAB Engine shut down successfully")
            except Exception as e:  # pylint: disable=broad-except
                logger.error(f"Error shutting down MATLAB Engine: {e}")
        else:
            logger.debug("MATLAB Engine not available for shutdown")

    @staticmethod
    def _clean_ascii(text: str) -> str:
        """
        Clean text to ASCII to avoid encoding issues with MATLAB.

        Args:
            text: Text to clean.

        Returns:
            ASCII-clean text.
        """
        return unicodedata.normalize("NFKD", text).encode(
            "ascii", "ignore").decode("ascii")
