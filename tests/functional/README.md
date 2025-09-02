# Mixer Functional Test Suite

This directory contains comprehensive functional tests for the Blender Mixer add-on, focusing on real user workflows and end-to-end functionality verification.

## 🏗️ Test Structure

```
tests/functional/
├── __init__.py              # Package initialization
├── utils.py                 # Shared test utilities and fixtures
├── README.md               # This documentation
├── test_room_management.py # Room creation, joining, and management
├── test_object_sync.py     # Object creation, deletion, and synchronization
├── test_collaboration.py   # Multi-user collaborative workflows
├── test_scene_collection.py # Scene and collection synchronization
├── test_error_recovery.py  # Error handling and recovery scenarios
├── test_performance.py     # Performance benchmarking and measurement
└── conftest.py             # Shared pytest configuration
```

## 🎯 Test Categories

### **Room Management Tests** (`test_room_management.py`)
- Room creation (Generic vs VRtist protocols)
- Multi-user room joining and synchronization
- Room cleanup and resource management
- Scaling tests (2-4+ instances)

### **Object Synchronization Tests** (`test_object_sync.py`)
- Object CRUD operations (Create, Read, Update, Delete)
- Real-time object property synchronization
- Material assignment and updates
- Transform and position synchronization

### **Collaboration Tests** (`test_collaboration.py`)
- Multi-user editing scenarios
- Conflict resolution
- Turn-taking workflows
- Concurrent modifications

### **Scene & Collection Tests** (`test_scene_collection.py`)
- Scene creation and switching
- Collection hierarchy management
- Linking and unlinking operations
- Scene-to-scene transitions

### **Performance Tests** (`test_performance.py`)
- Synchronization speed measurements
- Memory usage tracking
- Load testing with multiple instances
- Latency benchmarking

### **Recovery Tests** (`test_error_recovery.py`)
- Network disconnection/reconnection
- Server crash recovery
- Instance failure handling
- Data consistency verification

## 🚀 Quick Start

### **Run All Functional Tests**
```bash
pytest tests/functional/ -v --tb=short
```

### **Run Specific Test Categories**
```bash
# Room management tests
pytest tests/functional/test_room_management.py -v

# Object synchronization tests
pytest tests/functional/test_object_sync.py -v

# With detailed logging
pytest tests/functional/test_room_management.py -v -s --log-cli-level=INFO
```

### **Performance Testing**
```bash
# Run with performance profiling
pytest tests/functional/test_performance.py -v --durations=10

# Run with parallel execution (if pytest-xdist is available)
pytest tests/functional/ -n auto
```

## 🔧 Configuration

### **Test Fixtures**
The test suite uses standardized fixtures for consistent testing:

```bash
# Single instance (Generic protocol)
@pytest.fixture(scope="function")
def single_blender_generic()

# 2-instance setup (Generic protocol)
@pytest.fixture(scope="function")
def multi_blender_generic()

# 2-instance setup (VRtist protocol)
@pytest.fixture(scope="function")
def multi_blender_vrtist()
```

### **Environment Variables**
```bash
# Override default ports
export BLENDER_TEST_PORT_OFFSET=14000

# Enable verbose logging
export PYTEST_LOG_LEVEL=DEBUG

# Disable cleanup (for debugging)
export PYTEST_DISABLE_CLEANUP=1
```

## 📊 Test Metrics

Tests include built-in measurement for:

- **Synchronization Latency**: Time for changes to sync between instances
- **Memory Usage**: Peak memory consumption during tests
- **Network Traffic**: Message counts and payload sizes
- **Error Rates**: Success/failure ratios across test runs

## 🐛 Debugging

### **Verbose Output**
```bash
# See all print statements
pytest tests/functional/test_room_management.py -v -s

# See timing information
pytest tests/functional/ --durations=5

# Generate HTML report
pytest tests/functional/ --html=report.html
```

### **Debugging Failed Tests**
```bash
# Stop on first failure
pytest tests/functional/ -x

# Show full stack traces
pytest tests/functional/ --tb=long

# Interactive debugging
pytest tests/functional/test_room_management.py --pdb
```

## 🔄 Protocol Support

All tests support both Blender protocols:

- **Generic Protocol**: Full Blender data proxy synchronization
- **VRtist Protocol**: Direct Blender-to-Blender communication

Tests automatically validate both protocols when applicable.

## 🚨 Known Issues

### **Setup Requirements**
- Blender must be installed and accessible
- Python environment with bpy installed
- Sufficient port range available for multi-instance testing

### **Performance Considerations**
- Tests require Blender subprocess spawning
- Multi-instance tests consume significant resources
- Parallel execution limited by available ports

## 📈 Continuous Integration

### **CI Configuration**
```yaml
# Example GitHub Actions configuration
functional_tests:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Setup Blender
      run: |
        curl -L https://builder.blender.org/download/daily/blender-4.0.0-alpha+2023-12-15.81ec40e8c1d2-linux.x86_64-release.tar.xz | tar xf -
    - name: Run Functional Tests
      run: |
        cd tests/functional
        pytest -v --tb=short
```

## 🤝 Contributing

### **Adding New Tests**
1. Create test file following naming convention: `test_<feature>.py`
2. Use shared utilities from `utils.py`
3. Include both Generic and VRtist protocol testing
4. Add performance measurements where appropriate
5. Update this README with test descriptions

### **Test Guidelines**
- Use descriptive test names: `test_<action>_<protocol>_<scenario>`
- Include docstrings describing what the test validates
- Handle cleanup in fixtures to avoid resource leaks
- Measure performance in benchmark-worthy tests
- Support both protocols automatically

## 📚 API Documentation

### **Shared Utilities** (`utils.py`)

#### `setup_multi_blender_instances(num_instances, protocols, shared_folders, port_offset)`
Creates multiple Blender instances for testing with specified protocols and configuration.

#### `cleanup_blender_instances(blenders, server)`
Cleans up Blender instances and server processes safely.

#### `wait_for_sync(blenders, timeout)`
Waits for synchronization to complete across Blender instances.

#### `measure_performance(action_func, *args, **kwargs)`
Measures execution time and resource usage of test actions.

### **Test Fixtures**
- `multi_blender_generic()`: 2 Generic protocol instances
- `multi_blender_vrtist()`: 2 VRtist protocol instances
- `single_blender_generic()`: 1 Generic protocol instance
- `single_blender_vrtist()`: 1 VRtist protocol instance

This test suite provides comprehensive validation of Blender Mixer functionality, ensuring reliable collaboration and synchronization across real-world usage scenarios.
