# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: AtpLoopCaps.py
""" Run all ATP capacitor switching cases requested in a file.

Called from ATPLoopCaps.bat, reads ATPLoopCaps.dat.

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

fault_file = sys.argv[1]
atp_base = sys.argv[2]
atp_path = sys.argv[3] # '../../ATP/'
pl4path = sys.argv[4]
atp_file = atp_base + '.atp'
atp_list = atp_path + atp_base + '.lis'
atp_parm = atp_path + atp_base[:3] + 'CAP.prm'
atp_pl4 = atp_path + atp_base + '.pl4'

print (atp_base, pl4path, atp_path, atp_file, atp_list, atp_parm, atp_pl4)
#quit()

capacitors = {}

def run_atp_cap_case(device, fname):
  tclos = random.uniform(0.15, 0.15 + 1/60)
  fp = open (atp_parm, mode='w')
  print ('$PARAMETER', file=fp)
  for key, val in capacitors.items():
    atpbus = val['atp']
    tok = '_TC{:s}CLOS____'.format(atpbus)
    if key == device:
      print ('{:s} ={:.5f}'.format (tok[:10],tclos), file=fp)
    else:
      print ('{:s} =-1.0'.format (tok[:10]), file=fp)
    tok = '_TC{:s}OPEN____'.format(atpbus)
    print ('{:s} =100.0'.format (tok[:10]), file=fp)
  print ('BLANK END PARAMETER', file=fp)
  fp.close()
  cmdline = 'runtp ' + atp_file + ' >nul'
  pw0 = subprocess.Popen (cmdline, cwd=atp_path, shell=True)
  pw0.wait()
  print ('moving {:s} to {:s}'.format (atp_pl4, fname))
  shutil.move (atp_pl4, fname)

with open(fault_file, mode='r') as infile:
  for ln in infile:
    toks = ln.split()
    device = toks[0]
    atpbus = toks[1]
    kvar = toks[2]
    capacitors[device] = {'atp':atpbus, 'kvar': kvar}

print ('{:d} capacitors to switch in {:s}'.format(len(capacitors), atp_parm))

for device in capacitors:
  atpbus = capacitors[device]['atp']
  kvar = capacitors[device]['kvar']
  pl4name = pl4path + '/' + 'Cap_' + device + '.pl4'
  print ('{:s} capacitor energization ({:s} kvar) at {:s}, output to {:s}'.format (device, kvar, atpbus, pl4name))
  run_atp_cap_case (device, fname=pl4name)
#  quit()
