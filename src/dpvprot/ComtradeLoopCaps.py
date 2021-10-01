# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: ComtradeLoopCaps.py
""" Makes the PNGs from ATP-generated COMTRADE files for capacitor switching cases.

Paragraph.

Public Functions:
    :main: does the work
"""

import subprocess

caps = [{'fname':'c:/pl4/Capacitors/Cap_Y1015.pl4','PV':'PVONE PVTWO'},
        {'fname':'c:/pl4/Capacitors/Cap_Y1216.pl4','PV':'PVONE PVTWO'},
        {'fname':'c:/pl4/Capacitors/Cap_N8537.pl4','PV':'PVPCC'},
        {'fname':'c:/pl4/Capacitors/Cap_O3779.pl4','PV':'PVPCC'},
        {'fname':'c:/pl4/Capacitors/Cap_N8509.pl4','PV':'PVPCC'},
        {'fname':'c:/pl4/Capacitors/Cap_O1604.pl4','PV':'PVPCC'},
        {'fname':'c:/pl4/Capacitors/Cap_O1591.pl4','PV':'PVPCC'}]

for cap in caps:
  fname = cap['fname']
  cmdline = 'python ComtradeCasePlot.py ' + fname[:-4] + ' ' + cap['PV']
  print (cmdline)
  pw0 = subprocess.Popen (cmdline, shell=True)
  pw0.wait()

