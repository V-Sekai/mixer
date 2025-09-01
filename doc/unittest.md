# UNIT TESTS

## Running unit tests on the developer workstation

Unit tests use modern `pytest` v8.4.1 and are managed exclusively via `uv` package manager. The distributed nature of these tests automatically:

1. **Starts a broadcaster server** for communication
2. **Launches multiple Blender instances** (sender and receiver)
3. **Executes Python commands remotely** in each Blender instance
4. **Synchronizes Blender scenes** automatically through the mixer add-on
5. **Compares synchronization results** between all instances

### Prerequisites

Running the unit tests requires the `MIXER_BLENDER_EXE_PATH` environment variable to be set with the absolute path to the Blender executable:

```bash
export MIXER_BLENDER_EXE_PATH=/path/to/blender-binary
```

### Execution

Run all tests using the uv-exclusive workflow:

```bash
uv run python -m pytest tests/
```

Run specific test files:
```bash
uv run python -m pytest tests/test_specific_file.py
```

Run with more verbosity:
```bash
uv run python -m pytest tests/ -v --tb=short
```

To start the tests from VSCode, make sure that the addon is installed in the Blender instance that will be started, possibly by launching it once via VSCode [Blender development addon](https://github.com/JacquesLucke/blender_vscode)


## CI/CD on unit tests

For a first simple setup, we rely on an interactive gitlab runner setup. Issues related to service-based runners are described below.

The scripts are located in a new `gitlab` folder.

### Skipping automatic tests

You can skip tests by including the string `[skip-tests]` in the commit message.

### Interactive Gitlab runner

Documentation:

- Installation : https://docs.gitlab.com/runner/install/windows.html
- Runner commands : https://docs.gitlab.com/runner/commands/

Installation steps:

1. Install a gitlab runner in a folder of your choice. For this tutorial we'll use `d:\gitlab_runner`.
2. Run a terminal as administrator, create folder `d:\gitlab_runner\working_dir` and place yourself into it in your terminal
3. Register a runner with `gitlab-runner-windows-amd64.exe register`. Use `blender` as tag, `shell` as executor. The token can be found in Settings -> CI/CD page of this repository. This step should create a file `config.toml` in `d:\gitlab_runner\working_dir`.
4. Edit `d:\gitlab_runner\working_dir` and add an entry `cache_dir = "D:/gitlab_runner/cache"` in the `[[runners]]` section, after the `shell` entry.

Then run an interactive : `gitlab-runner-windows-amd64.exe run`. It must run as administrator because the `TSCON` command requires administrator rights to disconnect a session from the remote desktop.

The builds for the runner will be put in the current working directory `d:\gitlab_runner\working_dir` where you started the runner.

### Runner as a Windows service

Using a system service could be difficult because the user profile may not be easy to access and we also need the service to access to the desktop.

Using a service that logons with a user account requires a user account that can logon as a service as described in https://docs.gitlab.com/runner/faq/README.html#the-service-did-not-start-due-to-a-logon-failure-error-when-starting-service.
