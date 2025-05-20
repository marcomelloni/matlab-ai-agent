"""
Tests for the MatlabAIAgent class.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.agent import MatlabAIAgent


class TestMatlabAIAgent(unittest.TestCase):
    """Test suite for the MatlabAIAgent class."""

    def setUp(self):
        """Set up the test environment before each test."""
        # Create mock objects for the agent's dependencies
        self.mock_llm = MagicMock()
        self.mock_matlab = MagicMock()

        # Create patches
        self.llm_patch = patch(
            'src.agent.LLMInterface',
            return_value=self.mock_llm)
        self.matlab_patch = patch(
            'src.agent.MatlabEngine',
            return_value=self.mock_matlab)

        # Start patches
        self.llm_patch.start()
        self.matlab_patch.start()

        # Set up the agent with mocked dependencies
        self.agent = MatlabAIAgent(verbose=False)

        # Configure mocks
        self.mock_llm.generate_code.return_value = "% Test MATLAB code"
        self.mock_llm.fix_code.return_value = "% Fixed MATLAB code"
        self.mock_matlab.is_available = True
        self.mock_matlab.validate_code.return_value = []
        self.mock_matlab.execute_code.return_value = (
            "Success", {"success": True})

    def tearDown(self):
        """Clean up after each test."""
        # Stop patches
        self.llm_patch.stop()
        self.matlab_patch.stop()

    def test_add_message(self):
        """Test adding messages to conversation history."""
        self.agent.add_message("user", "Test message")
        self.assertEqual(len(self.agent.conversation_history), 1)
        self.assertEqual(self.agent.conversation_history[0]["role"], "user")
        self.assertEqual(
            self.agent.conversation_history[0]["content"],
            "Test message")

    def test_generate_matlab_code(self):
        """Test generating MATLAB code."""
        code = self.agent.generate_matlab_code("Test prompt")
        self.assertEqual(code, "% Test MATLAB code")
        self.mock_llm.generate_code.assert_called_once()

    def test_validate_with_mlint_no_errors(self):
        """Test validating MATLAB code with no errors."""
        self.agent.matlab_code = "% Test code"
        results = self.agent.validate_with_mlint()
        self.assertEqual(results, [])
        self.mock_matlab.validate_code.assert_called_once_with("% Test code")

    def test_validate_with_mlint_with_errors(self):
        """Test validating MATLAB code with errors."""
        self.agent.matlab_code = "% Test code with errors"
        self.mock_matlab.validate_code.return_value = ["Error 1", "Error 2"]
        results = self.agent.validate_with_mlint()
        self.assertEqual(results, ["Error 1", "Error 2"])
        self.assertEqual(self.agent.mlint_results, ["Error 1", "Error 2"])

    def test_execute_simulation_success(self):
        """Test executing a simulation successfully."""
        self.agent.matlab_code = "% Test simulation"
        result = self.agent.execute_simulation()
        self.assertEqual(result, "Success")
        self.assertEqual(self.agent.simulation_results, {"success": True})
        self.mock_matlab.execute_code.assert_called_once_with(
            "% Test simulation")

    def test_fix_code_with_llm(self):
        """Test fixing code with LLM."""
        self.agent.matlab_code = "% Code with errors"
        fixed_code = self.agent.fix_code_with_llm(["Error 1", "Error 2"])
        self.assertEqual(fixed_code, "% Fixed MATLAB code")
        self.mock_llm.fix_code.assert_called_once_with(
            "% Code with errors", ["Error 1", "Error 2"])
        self.assertEqual(self.agent.matlab_code, "% Fixed MATLAB code")


if __name__ == "__main__":
    unittest.main()
