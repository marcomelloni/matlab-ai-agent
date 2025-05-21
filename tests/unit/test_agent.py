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

        # Patch LLMInterface and MatlabEngine to use mocks
        self.llm_patch = patch(
            'src.agent.LLMInterface',
            return_value=self.mock_llm)
        self.matlab_patch = patch(
            'src.agent.MatlabEngine',
            return_value=self.mock_matlab)

        self.llm_patch.start()
        self.matlab_patch.start()

        # Initialize the agent, which will use the patched mocks
        self.agent = MatlabAIAgent(verbose=False)

        # Configure mock return values
        self.mock_llm.generate_code.return_value = "% Test MATLAB code"
        self.mock_llm.fix_code.return_value = "% Fixed MATLAB code"
        self.mock_matlab.is_available = True
        self.mock_matlab.validate_code.return_value = []
        self.mock_matlab.execute_code.return_value = (
            "Success", {"success": True})

    def tearDown(self):
        """Clean up after each test."""
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
        prompt = "Test prompt"
        code = self.agent.generate_matlab_code(prompt)
        self.assertEqual(code, "% Test MATLAB code")
        self.mock_llm.generate_code.assert_called_once_with(
            prompt,
            conversation_history=self.agent.conversation_history,
            progress_callback=None
        )

    def test_validate_with_mlint_no_errors(self):
        """Test validating MATLAB code with no errors."""
        self.agent.matlab_code = "% Test code"
        self.mock_matlab.validate_code.return_value = []
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
        self.mock_matlab.validate_code.assert_called_with(
            "% Test code with errors")

    def test_execute_simulation_success(self):
        """Test executing a simulation successfully."""
        self.agent.matlab_code = "% Test simulation"
        self.mock_matlab.execute_code.return_value = (
            "Success", {"success": True})
        result = self.agent.execute_simulation()
        self.assertEqual(result, "Success")
        self.assertEqual(self.agent.simulation_results, {"success": True})
        self.mock_matlab.execute_code.assert_called_once_with(
            self.agent.matlab_code, progress_callback=None
        )

    def test_execute_simulation_failure(self):
        """Test executing a simulation with failure."""
        self.agent.matlab_code = "% Test simulation"
        self.mock_matlab.execute_code.return_value = (
            "Failure", {"success": False, "error": "Runtime error"})
        result = self.agent.execute_simulation()
        self.assertEqual(result, "Failure")
        self.assertEqual(self.agent.simulation_results["success"], False)
        self.assertIn("error", self.agent.simulation_results)
        self.mock_matlab.execute_code.assert_called_once_with(
            self.agent.matlab_code, progress_callback=None
        )

    def test_fix_code_with_llm_with_errors(self):
        """Test fixing code with LLM when errors exist."""
        self.agent.matlab_code = "% Code with errors"
        errors = ["Error 1", "Error 2"]
        fixed_code = self.agent.fix_code_with_llm(errors)
        self.assertEqual(fixed_code, "% Fixed MATLAB code")
        self.mock_llm.fix_code.assert_called_once_with(
            "% Code with errors", errors, progress_callback=None
        )
        self.assertEqual(self.agent.matlab_code, "% Fixed MATLAB code")

    def test_fix_code_with_llm_no_errors(self):
        """Test fixing code with LLM when no errors exist."""
        self.agent.matlab_code = "% Code without errors"
        fixed_code = self.agent.fix_code_with_llm([])
        self.assertEqual(fixed_code, "% Code without errors")
        self.mock_llm.fix_code.assert_not_called()


if __name__ == "__main__":
    unittest.main()
