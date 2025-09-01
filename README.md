# Mixer

Mixer is a Blender addon for real-time collaboration in Blender. It allows multiple Blender users to work on the same scene simultaneously and is developed by the R&D department of Ubisoft Animation Studio.

> **Important**: Please note that Mixer only works on Blender 3.1 currently.

**Please note that Ubisoft is no longer maintaining this project. The V-Sekai team is now maintaining Mixer.**

![Mixer screenshot](docs/img/home_mixer.png)

**Disclaimer**: Although designed to be used in a production context, it is still an experimental tool. Despite our best efforts to make it reliable, it may, under certain circumstances, corrupt your Blender scenes data. Please note that neither Ubisoft nor Ubisoft employees can be held responsible in such cases. Use it at your own risk.

**However, we will do our best to improve Mixer based on your feedback to provide a memorable creative collaborative experience. Have fun!**

## Development Setup

### Environment Setup

This project uses modern Python dependency management tools. Choose one of the following approaches:

### Using UV (Recommended)

```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create UV environment and install dependencies
cd /path/to/mixer
uv sync --extra dev

# Due to UV's virtual environment isolation, you must set PYTHONPATH to access the local mixer addon
# For most commands:
PYTHONPATH="$(pwd)/addons:$(pwd)" uv run pytest
PYTHONPATH="$(pwd)/addons:$(pwd)" uv run python -c "import mixer; print('success')"

# For long shell sessions:
export PYTHONPATH="$(pwd)/addons:$(pwd)"
uv run bash
```

### Alternative: Direct Python

```bash
# Install Python dependencies (bpy comes from Blender installation)
pip install -r requirements-dev.txt
# Note: bpy is provided by your Blender installation, not pip

# Make mixer importable (may need Blender in PATH)
PYTHONPATH="$(pwd)/addons:$(pwd)" python

# For Blender integration testing, ensure Blender is accessible:
# - Blender should be in your PATH, OR
# - Set BLENDER_PATH environment variable if not in PATH
```

### Running Tests

```bash
# Environment variables needed for all test commands
export PYTHONPATH="$(pwd)/addons:$(pwd)"

# Basic tests (framework validation)
uv run pytest tests/test_test.py -v

# Blender-specific tests (require Blender binary)
uv run pytest tests/blender/ -v

# Networking tests
uv run pytest tests/broadcaster/ -v

# All tests with coverage
uv run pytest --cov=mixer
```

## Support

The active support repository is on the [Mixer Github repository](https://github.com/V-Sekai/mixer).

## Feedback and Contribution

You can also get involved in the development of Mixer. Discover how by reading these [contribution guidelines](doc/README.md).

## Features

Mixer enables collaborative 3D editing across multiple Blender instances and users in real-time.

## Installation

1. Download the addon from releases
2. Install in Blender: Edit > Preferences > Add-ons > Install

## Usage

After installation, the Mixer panel will appear in the 3D View's sidebar allowing you to:

- Join/create collaborative rooms
- Real-time synchronize edits
- Chat with collaborators

## Development

### Running Tests

```bash
# Basic tests (pytest framework validation)
PYTHONPATH="$(pwd)/addons:$(pwd)" uv run pytest tests/test_test.py -v

# Blender tests (require Blender binary)
PYTHONPATH="$(pwd)/addons:$(pwd)" uv run pytest tests/blender/ -v

# Networking tests
PYTHONPATH="$(pwd)/addons:$(pwd)" uv run pytest tests/broadcaster/ -v
```

### Project Structure

```
addons/mixer/           # Main addon package
docs/                   # Sphinx documentation
tests/                  # Comprehensive test suite
  ├── blender/          # Blender-specific tests
  ├── broadcaster/      # Networking server/client tests
  └── conftest.py       # Pytest configuration
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests with: `PYTHONPATH="$(pwd)/addons:$(pwd)" uv run pytest`
4. Ensure all linting passes: `uv run ruff check addons/mixer tests extra`
5. Submit a pull request

## License and Copyright

The original code is Copyright (C) 2020 Ubisoft.

All code of the `mixer` package is under the GPLv3 license except for the code of the `mixer.broadcaster` sub-package, which is under the MIT license.

## Deprecated Ubisoft Resources

Ubisoft resources have been deprecated but are still available for reference:

- [Ubisoft Mixer Documentation](https://ubisoft-mixer.readthedocs.io/)
- [Ubisoft Mixer Github Repository](https://github.com/ubisoft/mixer)

### Documentation and Usage

Documentation is available on the website https://ubisoft-mixer.readthedocs.io/ to:

- [Download and install](https://ubisoft-mixer.readthedocs.io/en/latest/getting-started/install.html)
- [Test](https://ubisoft-mixer.readthedocs.io/en/latest/getting-started/first-steps.html) locally
- Then [get connected](https://ubisoft-mixer.readthedocs.io/en/latest/collaborate/get-connected.html) and [work together](https://ubisoft-mixer.readthedocs.io/en/latest/collaborate/work-together.html)
