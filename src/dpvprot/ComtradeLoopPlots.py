# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: ComtradeLoopPlots.py
""" Makes voltage/current plots from ATP-generated COMTRADE files.

Uses ComtradeCasePlot.py.

Public Functions:
    :main: does the work
"""

import math
import sys
import operator
import subprocess
import os
import shutil
import random
import glob

#caps = [{'fname':'c:/pl4/Capacitors/Cap_Y1015.pl4','PV':'PVONE PVTWO'},
#        {'fname':'c:/pl4/Capacitors/Cap_Y1216.pl4','PV':'PVONE PVTWO'}]#,
#       {'fname':'c:/pl4/Capacitors/Cap_N8537.pl4','PV':'PVPCC'},
#       {'fname':'c:/pl4/Capacitors/Cap_O3779.pl4','PV':'PVPCC'},
#       {'fname':'c:/pl4/Capacitors/Cap_N8509.pl4','PV':'PVPCC'},
#       {'fname':'c:/pl4/Capacitors/Cap_O1604.pl4','PV':'PVPCC'},
#       {'fname':'c:/pl4/Capacitors/Cap_O1591.pl4','PV':'PVPCC'}]

#for cap in caps:
#  fname = cap['fname']
#  cmdline = 'python ComtradeCasePlot.py ' + fname[:-4] + ' ' + cap['PV']
#  print (cmdline)
#  pw0 = subprocess.Popen (cmdline, shell=True)
#  pw0.wait()

#feeders = [{'directory':'c:/pl4/SHE215','PV':'PVONE PVTWO'}]#,
#           {'directory':'c:/pl4/RIV209','PV':'PVPCC'},
#           {'directory':'c:/pl4/Louisa','PV':'PVPCC'}]

feeders = [{'directory':'c:/pl4/J1','PV':'"PV3  "'}]#,

for fdr in feeders:
  pattern = fdr['directory'] + '/*.dat'
  files = glob.glob (pattern)
  for fname in files:
    fpath = fname.replace('\\', '/')
    cmdline = 'python ComtradeCasePlot.py ' + fpath[:-4] + ' ' + fdr['PV']
    print (cmdline)
    pw0 = subprocess.Popen (cmdline, shell=True)
    pw0.wait()

