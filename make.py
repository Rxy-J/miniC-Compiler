#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：miniCC
@File ：make.py
@Author ：OrangeJ
@Date ：2022/5/6 14:31
"""

import sys
import subprocess

PY_MAIN_SCRIPT = ["miniC.py"]
EXEC_FILE = "minic.exe" if "win" in sys.platform else "minic"
DIST_PATH = "./"
EXEC_TYPE = "-F"  # F for single file, D for a folder which contains all files
PC = "pyinstaller"
CFLAGS = [EXEC_TYPE, "--distpath", DIST_PATH,  "-n", EXEC_FILE]

command = [PC]
command.extend(CFLAGS)
command.extend(PY_MAIN_SCRIPT)

subprocess.Popen(command)
