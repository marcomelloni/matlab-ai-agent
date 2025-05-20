"""
Basic example of using the MATLAB AI Agent to generate an ODE simulation.

This example shows how to generate, validate, and execute a simple
mass-spring-damper system simulation using the MATLAB AI Agent.
"""

import os
from dotenv import load_dotenv
from src.agent import MatlabAIAgent

# Load environment variables (make sure OPENAI_API_KEY is set)
load_dotenv()


def main():
    """Run a simple example of the MATLAB AI Agent."""
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Create a .env file with your OpenAI API key or set it as an environment variable.")
        return

    print("Initializing MATLAB AI Agent...")
    agent = MatlabAIAgent()

    # Define the simulation we want to generate
    simulation_prompt = """
    A mass-spring-damper system with the following parameters:
    - Mass (m) = 1 kg
    - Spring constant (k) = 10 N/m
    - Damping coefficient (c) = 2 N⋅s/m
    - Initial displacement = 5 m
    - Initial velocity = 0 m/s

    Simulate for 10 seconds and plot the position versus time.
    """

    print("\nGenerating MATLAB code for the simulation...")
    code = agent.generate_matlab_code(simulation_prompt)

    print("\nGenerated MATLAB code:")
    print("-" * 50)
    print(code)
    print("-" * 50)

    # Validate the generated code if MATLAB is available
    if agent.matlab.is_available:
        print("\nValidating the generated code...")
        validation_results = agent.validate_with_mlint()

        if validation_results:
            print("Validation issues found:")
            for result in validation_results:
                print(f"  {result}")

            print("\nAttempting to fix issues...")
            fixed_code = agent.fix_code_with_llm(validation_results)
            print("Code fixed!")
        else:
            print("✅ Validation passed: No issues found.")

        # Execute the simulation
        print("\nExecuting the simulation...")
        result = agent.execute_simulation()
        print(result)

        if agent.simulation_results.get("success"):
            print("✅ Simulation executed successfully!")
            if agent.simulation_results.get("figure"):
                print(f"Figure saved to: {agent.simulation_results['figure']}")
        else:
            print("❌ Simulation failed.")
    else:
        print("\nMATLAB Engine not available. Skipping validation and execution.")

    # Save the code to a file
    output_file = "mass_spring_damper.m"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"\nMATLAB code saved to {output_file}")


if __name__ == "__main__":
    main()
