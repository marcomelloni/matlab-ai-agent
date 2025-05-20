# Matlab AI Agent

A Python-based tool that utilizes AI to generate, validate, and execute MATLAB simulations. Supports both batch and streaming simulation modes.

## Features

- AI-powered MATLAB code generation using GPT-4
- Support for both batch and streaming simulations
- Automatic code validation using MATLAB's mlint
- Real-time streaming simulation with TCP/IP communication
- Interactive CLI interface
- Automatic error correction

## Requirements

### 1. Clone the Repository and Navigate to the Working Directory

```bash
git clone ...
cd matlab-ai
```

### 2. Install Poetry and Create Virtual Environment

Ensure Poetry is installed on your system. If not already installed, execute the following commands:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install poetry
```

Verify the installation:

```bash
poetry --version
```

Activate the virtual environment:

```bash
poetry env activate
```

> **Important:**  
> The command `poetry env activate` provides the activation command which must be executed separately.  
> Copy and run the displayed command, for example:

```bash
source /path/to/virtualenv/bin/activate
```

Verify environment activation:

```bash
which python
```

### 3. Install Project Dependencies

Install all dependencies defined in `pyproject.toml`:

```bash
poetry install
```

### 4. Install the MATLAB Engine API for Python

To integrate MATLAB with Python, install the MATLAB Engine API within your Poetry environment using one of these methods:

#### 4.1 Installation Using In-built Python Package

Using the package included with your MATLAB installation (example for MATLAB R2024b on MacOS):

```bash
cd /Applications/MATLAB_R2024b.app/extern/engines/python
poetry run python -m pip install .
```

> **Note:** Adjust the path according to your MATLAB version and installation location.

#### 4.2 Install via pip

Alternatively, use the version-specific [matlabengine](https://pypi.org/project/matlabengine) pip package:

```bash
pip install matlabengine==24.2.2
```

Select the version compatible with your MATLAB release from the [package history](https://pypi.org/project/matlabengine/#history).

### 5. Verify the MATLAB Engine Installation

Confirm successful installation with:

```bash
poetry run python -c "import matlab.engine; print('MATLAB Engine is installed successfully')"
```

Expected output:

```
MATLAB Engine is installed successfully!
```

### 6. Configure API Key

Create a `.env` file in the project root with your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

## Usage

### Interactive Mode

Launch an AI-guided interactive session for generating, validating, and executing MATLAB code:

```bash
poetry run matlab-ai-agent interactive
```

Options:

- `--matlab / --no-matlab`: Enable/disable MATLAB engine for validation and execution (enabled by default)

Interactive capabilities:

- Generate MATLAB code from natural language descriptions
- Validate code with mlint and automatically correct errors
- Execute simulations and diagnose issues
- Refine code through additional prompts
- Save generated code to .m files
- Exit with option to close the MATLAB engine

### Execution Mode

Execute existing MATLAB files:

```bash
poetry run matlab-ai-agent execute path/to/file.m
```

Parameters:

- `<filepath>`: Path to the .m file to execute

The file is executed via the MATLAB engine, with output and simulation results displayed upon successful execution.
