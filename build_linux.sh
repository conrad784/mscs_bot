#!/bin/bash

docker run --rm -v "$(pwd):/src/" cdrx/pyinstaller-linux \
       "PYTHONOPTIMIZE=1 pyinstaller --clean main.spec"

# generation of *.spec
# "pyinstaller --clean -F main.py --hidden-import=secret"
