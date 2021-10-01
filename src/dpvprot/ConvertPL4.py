# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: ConvertPL4.py
""" Converts ATP PL4 files to COMTRADE.

Uses the gtppl32 program from ATP distribution.

Public Functions:
    :main: does the work
"""

import sys
import operator
import subprocess
import os
import shutil
import glob

cmdline = 'c:\\atp\\gtppl32\\gtppl32 @@commands.script > nul'
file_path = sys.argv[1]
os.chdir (file_path)
files = glob.glob ('*.pl4')
for fname in files:
  fp = open ('commands.script', mode='w')
  print ('file', fname, file=fp)
  print ('comtrade all', file=fp)
  print ('', file=fp)
  print ('stop', file=fp)
  fp.close()
  pw0 = subprocess.Popen (cmdline, cwd=file_path, shell=True)
  pw0.wait()

