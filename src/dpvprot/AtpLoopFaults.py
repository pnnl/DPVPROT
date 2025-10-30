# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: AtpLoopFaults.py
""" Run all ATP fault cases requested in a file.

Called from ATPLoopFaults.bat, reads ATPLoopFaults.dat.

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
source_vbase = float(sys.argv[5])
atp_vpu = float(sys.argv[6])
atp_dt = sys.argv[7]  # should be formatted to exactly fill 8 columns

atp_file = atp_base + '.atp'
atp_list = atp_path + atp_base + '.lis'
atp_parm = atp_path + atp_base + '.prm'
atp_pl4 = atp_path + atp_base + '.pl4'

def run_atp_fault_case(bus, phs, slgf, fname):
  tfault = random.uniform(0.15, 0.15 + 1/60)
  vsrc = '{:.2f}'.format (atp_vpu * source_vbase)
  fp = open (atp_parm, mode='w')
  print ('$PARAMETER', file=fp)
  print ('_FLT_=\'' + bus.ljust(5) + '\'', file=fp)
  print ('__DELTAT   ={:s}'.format (atp_dt), file=fp)
  print ('____TMAX   =0.40', file=fp)
  print ('_VSOURCE__ =' + vsrc, file=fp)
  if slgf == True:
    if phs == 'A':
      print ('_TFAULTA__ ={:.5f}'.format (tfault), file=fp)
      print ('_TFAULTB__ =9.15', file=fp)
      print ('_TFAULTC__ =9.15', file=fp)
    elif phs == 'B':
      print ('_TFAULTA__ =9.15', file=fp)
      print ('_TFAULTB__ ={:.5f}'.format (tfault), file=fp)
      print ('_TFAULTC__ =9.15', file=fp)
    else:
      print ('_TFAULTA__ =9.15', file=fp)
      print ('_TFAULTB__ =9.15', file=fp)
      print ('_TFAULTC__ ={:.5f}'.format (tfault), file=fp)
  else:
    print ('_TFAULTA__ ={:.5f}'.format (tfault), file=fp)
    print ('_TFAULTB__ ={:.5f}'.format (tfault), file=fp)
    print ('_TFAULTC__ ={:.5f}'.format (tfault), file=fp)
  print ('BLANK END PARAMETER', file=fp)
  fp.close()
  cmdline = 'runtp ' + atp_file + ' >nul'
  pw0 = subprocess.Popen (cmdline, cwd=atp_path, shell=True)
  pw0.wait()
  # move the pl4 file
  print ('moving {:s} to {:s}'.format (atp_pl4, fname))
  shutil.move (atp_pl4, fname)

with open(fault_file, mode='r') as infile:
  for ln in infile:
    toks = ln.split()
    bus = toks[0]
    if '//' in bus:
        continue
    atpbus = toks[1]
    phs = toks[2][0]
    nph = len(toks[2])
    pl4name = pl4path + '/' + 'I1_' + atpbus + '.pl4'
    print ('running SLGF on {:s} at {:s} ({:s}), output to {:s}'.format (phs, atpbus, bus, pl4name))
    run_atp_fault_case (atpbus, phs, slgf=True, fname=pl4name)
    if nph == 3:
      pl4name = pl4path + '/' + 'I3_' + atpbus + '.pl4'
      print ('running three-phase fault at {:s} ({:s}), output to {:s}'.format (atpbus, bus, pl4name))
      run_atp_fault_case (atpbus, phs, slgf=False, fname=pl4name)
