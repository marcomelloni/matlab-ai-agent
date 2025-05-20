import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import click
from click.testing import CliRunner

# Assuming cli.py is in the same package as agent.py under src
from src.cli import cli

class TestCLI(unittest.TestCase):
    """Test suite for the CLI commands of MATLAB AI Agent."""

    def setUp(self):
        self.runner = CliRunner()
        # Patch the MatlabAIAgent used in cli
        self.agent_patch = patch('src.cli.MatlabAIAgent')
        self.mock_agent_class = self.agent_patch.start()
        # Create a mock agent instance
        self.mock_agent = MagicMock()
        self.mock_agent.matlab.is_available = True
        self.mock_agent.matlab_code = "% MATLAB code"
        self.mock_agent.generate_matlab_code.return_value = "% Generated code"
        self.mock_agent.validate_with_mlint.return_value = []
        self.mock_agent.execute_simulation.return_value = "Execution result"
        self.mock_agent.simulation_results = {"success": True, "figure": "/path/fig.png"}
        # Ensure new instance returns our mock
        self.mock_agent_class.return_value = self.mock_agent

    def tearDown(self):
        self.agent_patch.stop()

    def test_version_option(self):
        result = self.runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, 0)
        self.assertRegex(result.output.strip(), r"\d+\.\d+\.\d+")

    def test_interactive_exit_immediately(self):
        inputs = "Prompt text\n5\n"
        result = self.runner.invoke(cli, ['interactive', '--no-matlab'], input=inputs)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Describe the simulation ODE", result.output)
        self.assertIn("Thank you for using MATLAB AI Agent!", result.output)
        self.mock_agent.matlab.shutdown.assert_not_called()

    def test_interactive_validate_no_fix(self):
        # validation returns errors but user declines fix
        self.mock_agent.validate_with_mlint.return_value = ["Err"]
        inputs = "Prompt\n1\nn\n5\n"
        result = self.runner.invoke(cli, ['interactive'], input=inputs)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Issues found:", result.output)
        self.assertIn("Err", result.output)
        self.mock_agent.fix_code_with_llm.assert_not_called()

    def test_interactive_validate_and_fix(self):
        self.mock_agent.validate_with_mlint.return_value = ["Err"]
        inputs = "Prompt\n1\nY\n5\n"
        result = self.runner.invoke(cli, ['interactive'], input=inputs)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Fixing code", result.output)
        self.mock_agent.fix_code_with_llm.assert_called_once_with(["Err"])

    def test_interactive_execute_success(self):
        self.mock_agent.simulation_results = {"success": True}
        inputs = "Prompt\n2\n5\n"
        result = self.runner.invoke(cli, ['interactive'], input=inputs)
        self.assertIn("Executing simulation", result.output)
        self.assertIn("Execution result", result.output)

    def test_interactive_execute_failure_no_fix(self):
        self.mock_agent.simulation_results = {"success": False, "error": "Fail"}
        inputs = "Prompt\n2\nn\n5\n"
        result = self.runner.invoke(cli, ['interactive'], input=inputs)
        self.assertIn("Attempt to fix execution issues?", result.output)
        self.mock_agent.fix_code_with_llm.assert_not_called()

    def test_interactive_execute_failure_and_fix(self):
        self.mock_agent.simulation_results = {"success": False, "error": "Fail"}
        inputs = "Prompt\n2\ny\n5\n"
        result = self.runner.invoke(cli, ['interactive'], input=inputs)
        self.assertIn("Fixing code", result.output)
        self.mock_agent.fix_code_with_llm.assert_called_once_with(["Fail"])

    def test_interactive_modify_improve(self):
        inputs = "Prompt\n3\nAdd comment\n5\n"
        result = self.runner.invoke(cli, ['interactive'], input=inputs)
        self.assertIn("Generating updated code", result.output)
        self.mock_agent.generate_matlab_code.assert_called_with("Add comment")

    def test_interactive_save_code(self):
        with self.runner.isolated_filesystem():
            inputs = "Prompt\n4\nmycode.m\n5\n"
            result = self.runner.invoke(cli, ['interactive'], input=inputs)
            self.assertTrue(os.path.exists('mycode.m'))
            self.assertIn("Code saved to mycode.m", result.output)

    def test_interactive_invalid_choice(self):
        inputs = "Prompt\n9\n5\n"
        result = self.runner.invoke(cli, ['interactive'], input=inputs)
        self.assertIn("Invalid choice", result.output)

    def test_execute_success(self):
        with self.runner.isolated_filesystem():
            filepath = 'test.m'
            with open(filepath, 'w') as f:
                f.write('%')
            result = self.runner.invoke(cli, ['execute', filepath])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("✅ Execution successful!", result.output)
            self.assertIn("Figure saved to: /path/fig.png", result.output)

    def test_execute_no_engine(self):
        self.mock_agent.matlab.is_available = False
        with self.runner.isolated_filesystem():
            filepath = 'f.m'
            with open(filepath, 'w'):
                pass
            result = self.runner.invoke(cli, ['execute', filepath])
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("❌ MATLAB Engine not available.", result.output)

if __name__ == '__main__':
    unittest.main()
