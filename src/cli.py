# pragma: no cover
"""
Command-line interface for the MATLAB AI Agent.

This module provides a CLI for interacting with the MATLAB AI Agent,
allowing users to generate, validate, and execute MATLAB code from the command line.
"""

import os
import sys
import click

from .agent import MatlabAIAgent


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """MATLAB AI Agent - Generate and execute MATLAB simulations with AI."""
    pass


@cli.command()
@click.option(
    "--matlab/--no-matlab",
    default=True,
    help="Whether to start MATLAB engine for execution."
)
def interactive(matlab: bool):
    """Run an interactive session with the MATLAB AI Agent."""
    click.echo("\n" + "=" * 50)
    click.echo("🚀 MATLAB AI Agent - Interactive Session")
    click.echo("=" * 50)

    # Initialize the agent
    agent = MatlabAIAgent(matlab_startup=matlab)

    # Get prompt from user
    click.echo("\nDescribe the simulation ODE you would like to generate.")
    click.echo("Example: 'A system mass-spring with damping'")
    user_prompt = click.prompt("\nDescribe the simulation ODE")

    # Add message to conversation
    agent.add_message("user", user_prompt)

    # Generate MATLAB code
    click.echo("\nGenerating MATLAB code...")
    matlab_code = agent.generate_matlab_code(user_prompt)
    agent.add_message(
        "assistant",
        f"Generated MATLAB code:\n\n```matlab\n{matlab_code}\n```")

    # Show the generated code
    click.echo("\n" + "-" * 50)
    click.echo("MATLAB code generated:")
    click.echo("-" * 50)
    click.echo(matlab_code)
    click.echo("-" * 50)

    # Interactive loop
    while True:
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

        if action == 1:
            # Validate with mlint
            if not agent.matlab.is_available:
                click.echo("❌ MATLAB Engine not available for validation.")
                continue

            click.echo("\nValidating with mlint...")
            validation_results = agent.validate_with_mlint()

            if validation_results:
                click.echo("Issues found:")
                for result in validation_results:
                    click.echo(f"  {result}")

                if click.confirm("\nAttempt to fix issues automatically?"):
                    click.echo("\nFixing code...")
                    agent.fix_code_with_llm(validation_results)
                    click.echo("\nUpdated code:")
                    click.echo("-" * 50)
                    click.echo(agent.matlab_code)
                    click.echo("-" * 50)
            else:
                click.echo("✅ No issues found!")

        elif action == 2:
            # Execute simulation
            if not agent.matlab.is_available:
                click.echo("❌ MATLAB Engine not available for execution.")
                continue

            click.echo("\nExecuting simulation...")
            result = agent.execute_simulation()
            click.echo(result)

            if not agent.simulation_results.get("success", False):
                if click.confirm("\nAttempt to fix execution issues?"):
                    error = agent.simulation_results.get(
                        "error", "Unknown error")
                    click.echo("\nFixing code...")
                    agent.fix_code_with_llm([error])
                    click.echo("\nUpdated code:")
                    click.echo("-" * 50)
                    click.echo(agent.matlab_code)
                    click.echo("-" * 50)

        elif action == 3:
            # Modify/improve code
            improvement = click.prompt(
                "\nHow would you like to modify/improve the code?")
            agent.add_message("user", f"Modify the code to: {improvement}")

            click.echo("\nGenerating updated code...")
            agent.generate_matlab_code(improvement)
            agent.add_message(
                "assistant",
                f"Updated MATLAB code:\n\n```matlab\n{agent.matlab_code}\n```")

            click.echo("\nUpdated code:")
            click.echo("-" * 50)
            click.echo(agent.matlab_code)
            click.echo("-" * 50)

        elif action == 4:
            # Save code to file
            filepath = click.prompt(
                "Enter filename to save",
                default="matlab_simulation.m")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(agent.matlab_code)
            click.echo(f"Code saved to {filepath}")

        elif action == 5:
            # Exit
            if matlab and agent.matlab.is_available:
                click.echo("\nShutting down MATLAB Engine...")
                agent.matlab.shutdown()
            click.echo("\nThank you for using MATLAB AI Agent!")
            break

        else:
            click.echo("Invalid choice. Please try again.")


@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
def execute(filepath: str):
    """Execute an existing MATLAB file."""
    # Initialize the agent
    agent = MatlabAIAgent()

    if not agent.matlab.is_available:
        click.echo("❌ MATLAB Engine not available.")
        sys.exit(1)

    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        agent.matlab_code = f.read()

    # Execute the code
    click.echo(f"Executing {filepath}...")
    result = agent.execute_simulation()
    click.echo(result)

    if agent.simulation_results.get("success"):
        click.echo("✅ Execution successful!")
        if agent.simulation_results.get("figure"):
            click.echo(
                f"Figure saved to: {agent.simulation_results['figure']}")
    else:
        click.echo("❌ Execution failed.")


def main():
    """Main entry point for the CLI."""
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        click.echo("Error: OPENAI_API_KEY not found in environment variables.")
        click.echo(
            "Create a .env file with your OpenAI API key or set it as an environment variable.")
        sys.exit(1)

    # Run CLI
    cli()


if __name__ == "__main__":
    main()
