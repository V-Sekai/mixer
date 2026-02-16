# Mixer Fuzzing Tests

This directory contains fuzzing tests for the mixer addon using the Hypothesis library. These tests use property-based testing to generate random inputs and stress-test the mixer APIs to find edge cases, crashes, and inconsistencies.

## Overview

The fuzzing tests are organized into several modules:

- `test_proxy_fuzzing.py`: Tests the core proxy system (StructProxy, DatablockProxy) with randomly generated Blender objects
- `test_bpy_data_fuzzing.py`: Tests the BpyDataProxy operations with random datablocks
- `test_codec_fuzzing.py`: Tests the JSON codec and message handling with random data

## Running the Tests

### Prerequisites

The required dependencies (hypothesis, pytest) are already included in the project's `pyproject.toml` and can be installed with uv:

```bash
uv sync
```

### Running All Fuzzing Tests

```bash
# Run all fuzzing tests
pytest tests/unit_tests/fuzzing/ -v

# Run with more verbose output
pytest tests/unit_tests/fuzzing/ -v -s

# Run a specific test module
pytest tests/unit_tests/fuzzing/test_proxy_fuzzing.py -v

# Run a specific test
pytest tests/unit_tests/fuzzing/test_proxy_fuzzing.py::test_object_proxy_roundtrip -v
```

### Running with Custom Hypothesis Settings

```bash
# Run with more examples (slower but more thorough)
pytest tests/unit_tests/fuzzing/ -v --hypothesis-max-examples=100

# Run with a specific seed for reproducible results
pytest tests/unit_tests/fuzzing/ -v --hypothesis-seed=12345

# Run in quiet mode (less output)
pytest tests/unit_tests/fuzzing/ -v --hypothesis-verbosity=quiet
```

### Running in Blender

Since these tests require Blender's bpy module, they must be run within a Blender environment using the project's existing test infrastructure:

```bash
# Set the Blender executable path
export MIXER_BLENDER_EXE_PATH=/path/to/blender/executable

# Run fuzzing tests using the project's test runner
./tools/test.sh --pattern="*fuzzing*" -v

# Or run specific fuzzing test files
./tools/test.sh tests/unit_tests/fuzzing/test_proxy_fuzzing.py -v
```

## Test Strategies

The fuzzing tests use various Hypothesis strategies to generate test data:

### Data Generation Strategies

- **random_vector()**: Generates random 3D vectors with floats in range [-1000, 1000]
- **random_color()**: Generates random RGBA colors in range [0, 1]
- **random_string()**: Generates random strings suitable for Blender names
- **random_mesh_data()**: Generates random mesh geometry with vertices and faces
- **random_object_data()**: Generates random object transform data
- **random_json_like_data()**: Generates nested JSON-like data structures
- **random_binary_data()**: Generates random binary data for codec testing

### State Machine Testing

Some tests use Hypothesis's state machine testing to simulate complex sequences of operations:

- **ProxyFuzzingState**: Tests sequences of create/modify/diff/apply operations on proxies

## Interpreting Results

### Passing Tests

When tests pass, they provide confidence that the mixer APIs handle the tested scenarios correctly.

### Failing Tests

If a test fails, it indicates:

1. **Crashes**: The API crashed with the generated input
2. **Inconsistencies**: Save/load operations don't produce consistent results
3. **Invalid Assumptions**: The code makes assumptions that don't hold for edge cases

### Test Output

Hypothesis will show you the minimal failing example when a test fails:

```
Falsifying example: test_object_proxy_roundtrip(
    name='',
    location=(0.0, 0.0, 0.0),
    rotation=(0.0, 0.0, 0.0),
    scale=(1.0, 1.0, 1.0),
)
```

## Configuration

The tests are configured in `pyproject.toml`:

```toml
[tool.hypothesis]
max_examples = 10
deadline = 1000
suppress_health_check = ["too_slow"]
```

You can override these settings:

- `max_examples`: Number of test cases to generate per test
- `deadline`: Timeout in milliseconds per test case
- `suppress_health_check`: Disable hypothesis health checks

## Adding New Fuzzing Tests

### 1. Create a new test file

```python
# tests/unit_tests/fuzzing/test_new_feature_fuzzing.py

import pytest
from hypothesis import given, strategies as st

@given(input_data=st.your_strategy())
def test_new_feature(input_data):
    # Your fuzzing test here
    pass
```

### 2. Define strategies for your data

```python
@st.composite
def your_strategy(draw):
    # Generate random data for your feature
    return draw(st.some_strategy())
```

### 3. Test the relevant APIs

Focus on APIs that:
- Parse input data
- Transform data
- Serialize/deserialize data
- Handle edge cases

### 4. Handle cleanup

Make sure to clean up any Blender objects created during testing:

```python
def test_example():
    # Create objects
    obj = bpy.data.objects.new("test", None)

    try:
        # Test operations
        pass
    finally:
        # Clean up
        bpy.data.objects.remove(obj)
```

## Best Practices

### Test Coverage

- Test both valid and invalid inputs
- Test edge cases (empty strings, zero values, extreme values)
- Test concurrent operations where applicable
- Test cleanup and error recovery

### Performance

- Use appropriate `max_examples` and `deadline` settings
- Consider using `@settings(suppress_health_check=["too_slow"])` for slow tests
- Profile tests to identify performance bottlenecks

### Debugging

- Use `pytest -v -s --hypothesis-show-statistics` to see test statistics
- Use `pytest --hypothesis-seed=SEED` to reproduce specific failures
- Add logging to understand what data is being generated

## Continuous Integration

These fuzzing tests can be integrated into CI/CD pipelines to:

1. Catch regressions in mixer APIs
2. Test compatibility across Blender versions
3. Validate changes to core synchronization logic

Example CI configuration:

```yaml
fuzzing_tests:
  script:
    - blender --background --python-expr "
import sys
sys.path.append('.')
import pytest
pytest.main(['--hypothesis-max-examples=50', 'tests/unit_tests/fuzzing/'])
"
  artifacts:
    reports:
      junit: fuzzing-results.xml
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're running in a Blender environment with the mixer addon loaded
2. **Memory Issues**: Reduce `max_examples` or add cleanup in test fixtures
3. **Timeout Issues**: Increase `deadline` or optimize test operations
4. **Non-Deterministic Failures**: Use `--hypothesis-seed` to reproduce issues

### Getting Help

- Check the Hypothesis documentation: https://hypothesis.readthedocs.io/
- Review existing test patterns in the codebase
- Run tests with `--hypothesis-verbosity=verbose` for detailed output