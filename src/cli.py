# pragma: no cover

"""
Command-line interface for the MATLAB AI Agent.

This module provides a CLI for interacting with the MATLAB AI Agent,
allowing users to generate, validate, and execute MATLAB code from the command line.
"""

import os
import sys
import time
import click

from .agent import MatlabAIAgent
from .utils.prompt_generator import generate_prompt
from .utils.logger import logger, LogLevel


@click.group(invoke_without_command=True)
@click.option(
    "--matlab/--no-matlab",
    default=True,
    help="Whether to start MATLAB engine for execution."
)
@click.option(
    "--verbose", "-v",
    count=True,
    help="Increase verbosity (can be used multiple times)."
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="Minimize all output except essential information."
)
@click.pass_context
def cli(ctx, matlab, verbose, quiet):
    """MATLAB AI Agent CLI - Generate and execute MATLAB simulations with AI."""
    # Configure logger based on verbosity options
    ctx.ensure_object(dict)
    ctx.obj["start_time"] = time.time()

    # Set logging level
    if quiet:
        logger.set_level(LogLevel.WARNING.value)
    elif verbose >= 2:
        logger.set_level(LogLevel.DEBUG.value)
        logger.debug("Debug mode activated")
    elif verbose == 1:
        logger.set_level(LogLevel.INFO.value)
    else:
        # Default level - mostly success messages and warnings
        logger.set_level(LogLevel.INFO.value)

    logger.debug(
        f"CLI initialized with options: matlab={matlab}, "
        f"verbose={verbose}, quiet={quiet}"
    )

    if ctx.invoked_subcommand is None:
        ctx.invoke(interactive, matlab=matlab)


@cli.command()
def generate_prompt_cmd():
    """Generate a default .matlab_ai_prompt file with base simulation rules."""
    logger.info("Generating .matlab_ai_prompt file...")
    prompt_path = os.path.join(os.getcwd(), ".matlab_ai_prompt")

    if os.path.exists(prompt_path):
        if not click.confirm(f"{prompt_path} already exists. Overwrite?"):
            logger.warning("Prompt generation aborted by user.")
            return

    try:
        generate_prompt(prompt_path)
        logger.success(f".matlab_ai_prompt created at: {prompt_path}")
    except Exception as e:
        logger.error(f"Failed to write prompt file: {e}")


@cli.command()
@click.option(
    "--matlab/--no-matlab",
    default=True,
    help="Whether to start MATLAB engine for execution."
)
def interactive(matlab: bool):
    """Run an interactive session with the MATLAB AI Agent."""
    # Display header in normal/verbose mode
    if logger.logger.level <= LogLevel.INFO.value:
        click.echo("\n" + "=" * 50)
        click.echo(" 🚀 MATLAB AI Agent")
        click.echo("=" * 50)

    # Initialize the agent
    try:
        logger.debug("Initializing MatlabAIAgent")
        agent = MatlabAIAgent(matlab_startup=matlab)
        if matlab:
            if agent.matlab.is_available:
                logger.debug("MATLAB Engine successfully initialized")
            else:
                logger.warning(
                    "MATLAB Engine initialization failed - "
                    "running in code generation mode only"
                )
    except Exception as e:
        logger.critical(f"Failed to initialize MatlabAIAgent: {e}")
        sys.exit(1)

    # Get prompt from user
    click.echo("\nDescribe the simulation ODE you would like to generate.")
    click.echo("Example: 'A system mass-spring with damping'")
    user_prompt = click.prompt("\nDescribe the simulation ODE")
    logger.debug(f"User prompt: {user_prompt}")

    # Add message to conversation
    agent.add_message("user", user_prompt)

    logger.info("Generating MATLAB code...")
    matlab_code = agent.generate_matlab_code(user_prompt)
    logger.success("MATLAB code generation completed")

    agent.add_message(
        "assistant",
        f"Generated MATLAB code:\n\n```matlab\n{matlab_code}\n```"
    )

    # Show the generated code
    click.echo("\n" + "-" * 50)
    click.echo("MATLAB code generated:")
    click.echo("-" * 50)
    click.echo(matlab_code)
    click.echo("-" * 50)

    # Interactive loop
    while True:
        logger.debug("Entering interactive loop iteration")
        click.echo("\nWhat would you like to do?")
        choices = [
            "1. Validate code with mlint",
            "2. Execute simulation",
            "3. Modify/improve the code",
            "4. Save code to file",
            "5. Exit"
        ]
        for choice in choices:
            click.echo(choice)
        action = click.prompt("Choose an option", type=int, default=5)
        logger.debug(f"User selected action: {action}")

        if action == 1:
            # Validate with mlint
            if not agent.matlab.is_available:
                logger.warning("MATLAB Engine not available for validation")
                click.echo("\n❌ MATLAB Engine not available for validation.")
                continue

            logger.info("Validating code with mlint...")
            validation_results = agent.validate_with_mlint()

            if validation_results:
                logger.warning(
                    f"Found {len(validation_results)} issues with mlint"
                )
                click.echo("\nIssues found:")
                for result in validation_results:
                    click.echo(f"\nResult:\n{result}")

                if click.confirm("\nAttempt to fix issues automatically?"):
                    logger.info("Attempting to fix validation issues")
                    agent.fix_code_with_llm(validation_results)
                    logger.success("Code fixing completed")

                    click.echo("\nUpdated code:")
                    click.echo("-" * 50)
                    click.echo(agent.matlab_code)
                    click.echo("-" * 50)
            else:
                logger.success("No issues found with mlint validation")
                click.echo("\n✅ No issues found!")

        elif action == 2:
            # Execute simulation
            if not agent.matlab.is_available:
                logger.warning("MATLAB Engine not available for execution")
                click.echo("\n❌ MATLAB Engine not available for execution.")
                continue

            logger.info("Executing MATLAB simulation...")
            result = agent.execute_simulation()
            logger.success("Simulation execution completed")

            click.echo()
            click.echo(result)
            click.echo()

            if agent.simulation_results.get("success", False):
                logger.success("Simulation executed successfully")
                if agent.simulation_results.get("figure"):
                    figure_path = agent.simulation_results.get("figure")
                    logger.info(f"Figure saved to: {figure_path}")
            else:
                error_msg = agent.simulation_results.get(
                    "error", "Unknown error"
                )
                logger.error(f"Simulation error: {error_msg}")

                if click.confirm("\nAttempt to fix execution issues?"):
                    logger.info("Attempting to fix execution issues")
                    agent.fix_code_with_llm([error_msg])
                    logger.success("Code fixing completed")

                    click.echo("\nUpdated code:")
                    click.echo("-" * 50)
                    click.echo(agent.matlab_code)
                    click.echo("-" * 50)

        elif action == 3:
            # Modify/improve code
            improvement = click.prompt(
                "\nHow would you like to modify/improve the code?"
            )
            logger.debug(f"User requested modification: {improvement}")
            agent.add_message("user", f"Modify the code to: {improvement}")

            logger.info("Generating updated code based on user feedback")
            agent.generate_matlab_code(improvement)
            logger.success("Code updated successfully")

            agent.add_message(
                "assistant",
                f"Updated MATLAB code:\n\n```matlab\n{agent.matlab_code}\n```"
            )

            click.echo("\nUpdated code:")
            click.echo("-" * 50)
            click.echo(agent.matlab_code)
            click.echo("-" * 50)

        elif action == 4:
            # Save code to file
            filepath = click.prompt(
                "Enter filename to save",
                default="matlab_simulation.m"
            )
            logger.info(f"Saving code to file: {filepath}")
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(agent.matlab_code)
                logger.success(f"Code saved to {filepath}")
                click.echo(f"\nCode saved to {filepath}")
            except Exception as e:
                logger.error(f"Failed to save code to file: {e}")
                click.echo(f"❌ Failed to save: {e}")

        elif action == 5:
            # Exit
            logger.info("Exiting interactive session")
            if matlab and agent.matlab.is_available:
                logger.debug("Shutting down MATLAB Engine")
                click.echo("\nShutting down MATLAB Engine...")
                agent.matlab.shutdown()

            elapsed_time = time.time() - \
                click.get_current_context().obj["start_time"]
            logger.info(f"Session completed in {elapsed_time:.2f} seconds")
            click.echo("\nThank you for using MATLAB AI Agent!")
            break

        else:
            logger.warning(f"Invalid choice selected: {action}")
            click.echo("\nInvalid choice. Please try again.")


@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
def execute(filepath: str):
    """Execute an existing MATLAB file."""
    logger.info(f"Executing existing MATLAB file: {filepath}")

    # Initialize the agent
    try:
        agent = MatlabAIAgent()
        logger.debug("MatlabAIAgent initialized")
    except Exception as e:
        logger.critical(f"Failed to initialize MatlabAIAgent: {e}")
        sys.exit(1)

    if not agent.matlab.is_available:
        logger.error("MATLAB Engine not available for execution")
        click.echo("\n❌ MATLAB Engine not available.")
        sys.exit(1)

    # Read the file
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            agent.matlab_code = f.read()
        logger.debug(f"Loaded MATLAB code from {filepath}")
    except Exception as e:
        logger.error(f"Failed to read MATLAB file: {e}")
        click.echo(f"\n❌ Failed to read file: {e}")
        sys.exit(1)

    # Execute the code
    logger.info("Executing MATLAB file")
    click.echo(f"\nExecuting {filepath}...")

    result = agent.execute_simulation()
    logger.success("Execution completed")

    print()
    click.echo(result)


def main():
    """Main entry point for the CLI."""
    logger.debug("Starting MATLAB AI Agent CLI")

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        logger.critical("OPENAI_API_KEY not found in environment variables")
        click.echo("\nError: OPENAI_API_KEY not found in environment variables.")
        click.echo(
            "\nCreate a .env file with your OpenAI API key "
            "or set it as an environment variable."
        )
        sys.exit(1)

    # Create context for timing information
    ctx_obj = {"start_time": time.time()}

    try:
        # Run CLI with timing context
        cli(obj=ctx_obj)
        elapsed_time = time.time() - ctx_obj["start_time"]
        logger.debug(f"CLI completed in {elapsed_time:.2f} seconds")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        click.echo(f"\n❌ An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
