#!/bin/bash


docker run --rm -v "$(pwd):/src/" cdrx/pyinstaller-linux \
       "pyinstaller --clean -F main.py --hidden-import=secret"
