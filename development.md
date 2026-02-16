# Mixer Development Setup

## Testing

Mixer supports two testing approaches:

### 1. VRM-Style Library Context Testing (Recommended)

This approach runs tests directly inside Blender, allowing direct access to bpy in library code:

```bash
# Install dependencies
uv sync --extra dev

# Set Blender executable path
export MIXER_BLENDER_EXE_PATH=/path/to/blender

# Run tests inside Blender
./tools/test.sh -v
```

### 2. Traditional Integration Testing

For tests requiring multiple Blender instances and network communication:

```bash
# Install dependencies
uv sync --extra dev

# Run specific integration tests
uv run pytest tests/blender/test_proxy.py -v
```

## CI/CD

The CI pipeline automatically:
- Installs Blender 4.5
- Runs basic tests (no Blender required)
- Runs full integration tests inside Blender using the VRM-style approach

## Local Development

1. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Install Python 3.11: `uv python install 3.11`
3. Install dependencies: `uv sync --extra dev`
4. Install Blender 4.5 from https://www.blender.org/download/
5. Set `MIXER_BLENDER_EXE_PATH` to your Blender executable
6. Run tests: `./tools/test.sh -v`
