import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
from click.testing import CliRunner
from src.cli import cli, main

# Fixtures and setup


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.matlab.is_available = True
    agent.simulation_results = {"success": True, "figure": "figure.png"}
    agent.matlab_code = "disp('Hello World');"
    agent.generate_matlab_code.return_value = "disp('Hello World');"
    return agent

# CLI entrypoint test


@patch.dict(os.environ, {"OPENAI_API_KEY": "test"})
@patch("src.cli.cli")
def test_main_cli(mock_cli):
    main()
    mock_cli.assert_called()


@patch.dict(os.environ, {}, clear=True)
def test_main_no_api_key():
    with patch("builtins.print") as mock_print:
        with pytest.raises(SystemExit):
            main()
        mock_print.assert_not_called()


# execute command with valid file
@patch("src.cli.open", new_callable=mock_open, read_data="disp('run');")
@patch("src.cli.MatlabAIAgent")
def test_execute_command(mock_agent_class, mock_file, runner):
    agent = MagicMock()
    agent.matlab.is_available = True
    agent.execute_simulation.return_value = "Executed"
    mock_agent_class.return_value = agent

    with runner.isolated_filesystem():
        filepath = "test.m"
        with open(filepath, "w") as f:
            f.write("disp('test');")
        result = runner.invoke(cli, ["execute", filepath])
        assert result.exit_code == 0
        assert "Executed" in result.output

# Invalid file path


def test_execute_missing_file(runner):
    result = runner.invoke(cli, ["execute", "missing.m"])
    assert result.exit_code != 0
    assert "Error" in result.output or "❌" in result.output

# Test CLI with --quiet and --verbose


@patch("src.cli.logger")
@patch("src.cli.interactive")
def test_cli_options_log_levels(mock_interactive, logger_mock, runner):
    runner.invoke(cli, ["--quiet"])
    logger_mock.set_level.assert_called()

    runner.invoke(cli, ["-v"])
    logger_mock.set_level.assert_called()

    runner.invoke(cli, ["-vv"])
    logger_mock.set_level.assert_called()

# Validate and fix flow


@patch("src.cli.click.prompt", side_effect=[
    "mass-spring system",  # user prompt
    1,  # Validate
    5   # Exit
])
@patch("src.cli.click.confirm", return_value=True)
@patch("src.cli.MatlabAIAgent")
def test_validate_code_fix_flow(
        mock_agent_class, confirm_mock, prompt_mock, runner):
    agent = MagicMock()
    agent.matlab.is_available = True
    agent.generate_matlab_code.return_value = "code"
    agent.validate_with_mlint.return_value = ["error: something wrong"]
    agent.matlab_code = "fixed code"
    mock_agent_class.return_value = agent

    result = runner.invoke(cli, ["interactive"])
    assert result.exit_code == 0
    agent.fix_code_with_llm.assert_called()

# Modify code flow


@patch("src.cli.click.prompt", side_effect=[
    "mass-spring system",  # user prompt
    3,  # modify option
    "add damping",  # how to modify
    5   # exit
])
@patch("src.cli.MatlabAIAgent")
def test_modify_code_flow(mock_agent_class, prompt_mock, runner):
    agent = MagicMock()
    agent.matlab.is_available = True
    agent.generate_matlab_code.return_value = "new code"
    agent.matlab_code = "new code"
    mock_agent_class.return_value = agent

    result = runner.invoke(cli, ["interactive"])
    assert result.exit_code == 0
    assert "new code" in result.output

# Save to file


@patch("src.cli.click.prompt", side_effect=[
    "mass-spring system",  # user prompt
    4,  # Save
    "saved_code.m",  # filename
    5   # exit
])
@patch("src.cli.MatlabAIAgent")
def test_save_code(mock_agent_class, prompt_mock, runner):
    agent = MagicMock()
    agent.matlab.is_available = True
    agent.generate_matlab_code.return_value = "disp('save');"
    agent.matlab_code = "disp('save');"
    mock_agent_class.return_value = agent

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["interactive"])
        assert os.path.exists("saved_code.m")
        with open("saved_code.m") as f:
            assert "disp" in f.read()
