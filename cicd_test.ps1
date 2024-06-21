# Set the path to the blender directory
$BLENDER_DIR = "blender-3.3.19-windows-x64"

# Install required python packages
& "$BLENDER_DIR/3.3/python/bin/python.exe" -m pip install unittest-xml-reporting parameterized unittest2 xmlrunner pytest pytest-timeout

# Run the installation script
& "$BLENDER_DIR/blender.exe" --background --python-exit-code 1 --python gitlab/install_mixer.py

# Run the test script
& "$BLENDER_DIR/blender.exe" --background --python-exit-code 1 --python mixer/blender_data/tests/ci.py

# Run the tests and generate XML reports
# & "$BLENDER_DIR/3.3/python/bin/python.exe" -m xmlrunner discover --verbose tests.vrtist -o logs/tests
& "$BLENDER_DIR/3.3/python/bin/python.exe" -m xmlrunner discover --verbose tests.broadcaster -o logs/tests
# & "$BLENDER_DIR/3.3/python/bin/python.exe" -m xmlrunner discover --verbose tests.blender -o logs/tests
