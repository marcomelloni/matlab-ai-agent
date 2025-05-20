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
from typing import Dict, List, Tuple, Union


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
        try:
            # Import here to avoid requiring matlab as a dependency for the package
            import matlab.engine

            self.eng = matlab.engine.start_matlab()
            self.is_available = True
            return True
        except ImportError:
            print("Warning: MATLAB Engine not available. "
                  "Install the MATLAB Engine API for Python to enable execution.")
            self.is_available = False
            return False
        except Exception as e:
            print(f"Error starting MATLAB Engine: {e}")
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
        if not self.is_available or not self.eng:
            return ["MATLAB Engine not available."]

        if not code:
            return ["No code to validate."]

        # Create a unique identifier for the script
        unique_id = hashlib.md5((code + str(time.time())).encode()).hexdigest()[:8]
        script_name = f"validate_script_{unique_id}"
        temp_dir = tempfile.gettempdir()
        script_path = os.path.join(temp_dir, f"{script_name}.m")

        try:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(code)

            messages = self.eng.checkcode(script_path.replace(os.sep, '/'), nargout=1)

            mlint_results = []
            for msg in messages:
                mlint_results.append(f"[Line {msg.line}] {msg.message}")

            return mlint_results if mlint_results else ["No issues found."]

        except Exception as e:
            return [f"Error during validation: {e}"]
        finally:
            # Clean up
            if os.path.exists(script_path):
                try:
                    os.unlink(script_path)
                except Exception:
                    pass


    def execute_code(self, code: str) -> Tuple[str, Dict[str, Union[str, bool, None]]]:
        """
        Execute MATLAB code and capture the results.

        Args:
            code: MATLAB code to execute.

        Returns:
            A tuple containing:
                - A message describing the execution result
                - A dictionary with detailed execution results
        """
        if not self.is_available or not self.eng:
            return "MATLAB Engine not available.", {
                "success": False,
                "error": "MATLAB Engine not available."
            }

        if not code:
            return "No code to execute.", {
                "success": False,
                "error": "No code provided."
            }

        # Clean the code to ensure compatibility
        cleaned_code = self._clean_ascii(code)

        # Create a unique identifier for the script
        unique_id = hashlib.md5((code + str(time.time())).encode()).hexdigest()[:8]
        script_name = f"sim_script_{unique_id}"
        temp_dir = tempfile.gettempdir()
        script_path = os.path.join(temp_dir, f"{script_name}.m")
        results_dir = os.path.join(temp_dir, f"results_{unique_id}")

        try:
            # Create results directory
            os.makedirs(results_dir, exist_ok=True)

            # Write the code to a file
            with open(script_path, 'w', encoding='utf-8') as script_file:
                script_file.write(cleaned_code)

            # Create MATLAB commands for execution
            matlab_commands = [
                f"cd('{temp_dir.replace(os.sep, '/')}')",
                f"addpath('{temp_dir.replace(os.sep, '/')}')",
                f"try",
                f"    diary('{results_dir.replace(os.sep, '/')}/output.txt')",
                f"    {script_name}",
                f"    diary off",
                f"    if ~isempty(findall(0,'Type','Figure'))",
                f"        saveas(gcf, '{results_dir.replace(os.sep, '/')}/figure.png')",
                f"    end",
                f"    error_msg = '';",
                f"catch ME",
                f"    diary off",
                f"    error_msg = ME.message;",
                f"end",
                f"rmpath('{temp_dir.replace(os.sep, '/')}')"
            ]

            # Join commands and execute
            matlab_script = "; ".join(matlab_commands)
            self.eng.eval(matlab_script, nargout=0)

            # Check for error message
            error_msg = self.eng.eval("error_msg", nargout=1)

            # Check if execution was successful
            success = not error_msg

            # Check for output and figure
            output_path = os.path.join(results_dir, "output.txt")
            figure_path = os.path.join(results_dir, "figure.png")

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
                message = f"Execution failed: {error_msg}"

            return message, result

        except Exception as e:
            return f"Error: {str(e)}", {
                "script_executed": script_name,
                "success": False,
                "error": str(e)
            }
        finally:
            # Clean up the script file but leave the results
            if os.path.exists(script_path):
                try:
                    os.unlink(script_path)
                except Exception:
                    pass

    def shutdown(self) -> None:
        """Shutdown the MATLAB Engine."""
        if self.is_available and self.eng:
            try:
                self.eng.quit()
                print("MATLAB Engine shut down.")
            except Exception as e:
                print(f"Error shutting down MATLAB Engine: {e}")

    @staticmethod
    def _clean_ascii(text: str) -> str:
        """
        Clean text to ASCII to avoid encoding issues with MATLAB.

        Args:
            text: Text to clean.

        Returns:
            ASCII-clean text.
        """
        return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")