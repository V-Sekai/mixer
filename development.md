blender-3.3.19-windows-x64/blender.exe --background --python-exit-code 1 --python mixer/blender_data/tests/ci.py
blender-3.3.19-windows-x64/3.3/python/bin/python.exe -m xmlrunner discover --verbose tests.vrtist -o $MIXER_TEST_OUTPUT
blender-3.3.19-windows-x64/3.3/python/bin/python.exe -m xmlrunner discover --verbose tests.broadcaster -o $MIXER_TEST_OUTPUT
blender-3.3.19-windows-x64/3.3/python/bin/python.exe -m xmlrunner discover --verbose tests.blender -o $MIXER_TEST_OUTPUT
