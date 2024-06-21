blender-3.3.19-windows-x64/3.3/python/bin/python.exe -m pip install unittest-xml-reporting parameterized unittest2 xmlrunner
blender-3.3.19-windows-x64/blender.exe --background --python-exit-code 1 --python gitlab/install_mixer.py
blender-3.3.19-windows-x64/blender.exe --background --python-exit-code 1 --python mixer/blender_data/tests/ci.py
blender-3.3.19-windows-x64/3.3/python/bin/python.exe -m xmlrunner discover --verbose tests.broadcaster -o logs/tests
blender-3.3.19-windows-x64/3.3/python/bin/python.exe -m xmlrunner discover --verbose tests.blender -o logs/tests
blender-3.3.19-windows-x64/3.3/python/bin/python.exe -m xmlrunner discover --verbose tests.vrtist -o logs/tests
