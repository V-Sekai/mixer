# Contributing to Mixer

Thank you for your interest in contributing to Mixer! This document provides guidelines and information for contributors.

## Table of Contents

- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Code Style](#code-style)
- [Development Workflow](#development-workflow)
- [Submitting Changes](#submitting-changes)
- [Testing Guidelines](#testing-guidelines)
- [Architecture Overview](#architecture-overview)

## Development Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Installation

1. Clone the repository:

```bash
git clone https://github.com/V-Sekai/mixer.git
cd mixer
```

2. Install dependencies using uv:

```bash
uv sync
```

3. Activate the virtual environment:

```bash
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate     # On Windows
```

### Environment Variables

For clean testing without uv warnings:

```bash
export UV_LINK_MODE=copy
```

## Running Tests

### Test Types and Requirements

Mixer supports multiple testing approaches with different requirements:

#### Option 1: Full Blender Integration Tests
For tests requiring a complete Blender installation:

```bash
export MIXER_BLENDER_EXE_PATH=/path/to/blender/executable
uv run python -m pytest tests/integration_tests/blender/ -k "not test_mixer_uv_bpy"
```

#### Option 2: uv bpy Tests (Limited Compatibility)
Tests using the PyPI `bpy` package - no Blender executable needed, but may have compatibility issues:

```bash
uv run python -m pytest tests/integration_tests/blender/test_mixer_uv_bpy.py -v
```

**Note:** uv bpy tests may fail due to API differences between PyPI bpy and full Blender bpy. Use full Blender integration tests for comprehensive testing.

#### Option 3: Unit Tests
No external dependencies required:

```bash
uv run python -m pytest tests/unit_tests/
```

#### Option 4: Fuzzing Tests (Hypothesis-based)
Property-based testing with random input generation to find edge cases:

```bash
# Run fuzzing tests (requires Blender executable)
export MIXER_BLENDER_EXE_PATH=/path/to/blender/executable
./tools/test.sh --pattern="*fuzzing*" -v

# Run with more examples for thorough testing (set hypothesis options via pytest)
./tools/test.sh --pattern="*fuzzing*" --hypothesis-max-examples=100 -v

# Run specific fuzzing test
./tools/test.sh tests/unit_tests/fuzzing/test_proxy_fuzzing.py -v
```

### All Tests

```bash
# Run all tests (requires Blender executable for integration tests)
export MIXER_BLENDER_EXE_PATH=/path/to/blender/executable
uv run python -m pytest tests/
```

### Specific Test Categories

```bash
# Blender integration tests (requires Blender executable)
uv run python -m pytest tests/integration_tests/blender/

# Broadcaster unit tests (no dependencies)
uv run python -m pytest tests/unit_tests/broadcaster/

# Functional tests (requires Blender executable)
uv run python -m pytest tests/integration_tests/blender/test_mixer_functional.py
```

### Test Coverage

```bash
uv run python -m pytest --cov=mixer --cov-report=html tests/
```

## Code Style

### Linting

```bash
uv run ruff check .
uv run ruff format --check .
```

### Auto-fix

```bash
uv run ruff check --fix .
uv run ruff format .
```

### Type Checking

```bash
uv run mypy .
```

## Development Workflow

### 1. Choose an Issue

- Check the [GitHub Issues](https://github.com/V-Sekai/mixer/issues) for tasks
- Look for issues labeled `good first issue` or `help wanted`

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 3. Make Changes

- Write tests first (TDD approach)
- Follow the existing code patterns
- Keep commits focused and atomic
- Update documentation as needed

### 4. Test Your Changes

```bash
# Run relevant tests
uv run python -m pytest tests/path/to/relevant/tests/

# Run linting
uv run ruff check .

# Run type checking
uv run mypy .
```

### 5. Update Documentation

- Update docstrings for any new or modified functions
- Update this CONTRIBUTING.md if development workflow changes
- Update README.md if user-facing features change

## Submitting Changes

### Pull Request Process

1. **Ensure tests pass** and code is properly formatted
2. **Update CHANGELOG.md** with your changes
3. **Push your branch** to GitHub
4. **Create a Pull Request** with:
   - Clear title describing the change
   - Detailed description of what was changed and why
   - Reference to any related issues
   - Screenshots/videos for UI changes

### Commit Messages

Keep commit messages clear and descriptive. Examples:

```
Add support for uv bpy subprocess testing
Resolve race condition in room joining
Update development setup instructions
```

## Testing Guidelines

### Test Organization

- Unit tests in `tests/unit_tests/` directory
- Integration tests in `tests/integration_tests/` directory
- Test helpers in `tests/test_helpers/` directory
- Blender integration tests in `tests/integration_tests/blender/`
- Broadcaster unit tests in `tests/unit_tests/broadcaster/`
- Fuzzing tests in `tests/unit_tests/fuzzing/` directory
- Functional tests for end-to-end scenarios

### uv bpy Testing

Mixer supports testing with PyPI bpy package instead of full Blender executables:

```python
# Use uv bpy for testing (no Blender executable needed)
blender_app = BlenderApp(port, ptvsd_port, wait_for_debugger, use_uv_bpy=True)
```

### Writing Tests

- Use descriptive test names
- Test one thing per test method
- Use appropriate assertions
- Include docstrings explaining test purpose
- Mock external dependencies when possible

### Fuzzing Tests

For APIs that handle complex data structures or user input, consider adding property-based fuzzing tests:

- Use Hypothesis strategies to generate random valid/invalid inputs
- Test edge cases that traditional unit tests might miss
- Focus on save/load/apply/diff operations that transform data
- Include cleanup to prevent test interference
- Use `@settings(max_examples=N)` to control test thoroughness

Example fuzzing test structure:

```python
@given(input_data=st.your_strategy())
@settings(max_examples=50, deadline=2000)
def test_api_fuzzing(input_data):
    # Test API robustness with random inputs
    pass
```

### Integration Tests

- Use `MixerTestCase` for Blender synchronization tests
- Set `use_uv_bpy=True` for portable testing
- Clean up resources properly in `teardown_method`

## Architecture Overview

### Core Components

- **broadcaster/**: WebSocket server for real-time synchronization
- **addons/mixer/**: Blender addon providing the Mixer UI and functionality
- **mixer/blender_data/**: Data serialization and synchronization logic
- **mixer/blender_client/**: Client-side Blender API wrappers
- **mixer/connection/**: Network connection management

### Key Concepts

- **Rooms**: Synchronization sessions between Blender instances
- **Data Proxies**: Python objects representing Blender data structures
- **Codecs**: Serialization/deserialization of Blender data
- **Handlers**: Event-driven synchronization logic

### Testing Architecture

- **MixerTestCase**: Base class for integration tests
- **BlenderApp**: Wrapper for Blender process management
- **UvBpyServer**: uv-based Blender process alternative
- **Grabber**: Room content capture for test verification

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/V-Sekai/mixer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/V-Sekai/mixer/discussions)
- **Documentation**: See `doc/` directory and [online docs](https://v-sekai.github.io/mixer/)
