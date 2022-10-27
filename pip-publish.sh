#!/bin/bash
rm -r build dist libsocket.egg-info # Remove old build files
python3 setup.py sdist bdist_wheel  # Build the project
python3 -m twine upload dist/*      # Upload to pip