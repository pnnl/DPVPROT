# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: CheckReducedFaults.py
""" Run and tabulate ATP phasor fault solutions.

Checks 3-phase and single-line-to-ground fault currents,
at full and reduced feeder load, with and without PV.

Public Functions:
    :main: does the work
"""

import csv
import math
import sys
import operator
import subprocess

full_faults = {}
reduced_faults = {}
atp_buses = {}
atp_phases = {}

atp_base = sys.argv[1]
atp_path = '../../ATP/'
atp_file = atp_base + '.atp'
atp_list = atp_path + atp_base + '.lis'
atp_parm = atp_path + atp_base + '.prm'
source_vbase = float(sys.argv[2])
dss_vpu = float(sys.argv[3])
atp_vpu = float(sys.argv[4])

# remember ATP outputs are peak line-to-ground, not RMS
def parse_atp_fault_current(fname, phs):
  amps = 0.0
  foundCurrents = False
  fp = open (fname, mode='r')
  match = 'FAULT' + phs
  for ln in fp:
    if foundCurrents:
      if match in ln:
        vals = ln.split(match)
#        print (vals)
        toks = vals[1].split()
#        print (toks)
        amps = float(toks[2])
        break
    elif 'Output for steady-state phasor switch currents' in ln:
      foundCurrents = True
  fp.close()
  return amps / math.sqrt(2.0)

def get_atp_fault_current(bus, phs, slgf):
  amps = 0.0
  vsrc = '{:.2f}'.format (atp_vpu * source_vbase)
  fp = open (atp_parm, mode='w')
  print ('$PARAMETER', file=fp)
  print ('_FLT_=\'' + bus.ljust(5) + '\'', file=fp)
  print ('____TMAX   =-1.0', file=fp)
  print ('_VSOURCE__ =' + vsrc, file=fp)
  if slgf == True:
    if phs == 'A':
      print ('_TFAULTA__ =-0.10', file=fp)
      print ('_TFAULTB__ =9.05', file=fp)
      print ('_TFAULTC__ =9.05', file=fp)
    elif phs == 'B':
      print ('_TFAULTA__ =9.05', file=fp)
      print ('_TFAULTB__ =-0.10', file=fp)
      print ('_TFAULTC__ =9.05', file=fp)
    else:
      print ('_TFAULTA__ =9.05', file=fp)
      print ('_TFAULTB__ =9.05', file=fp)
      print ('_TFAULTC__ =-0.10', file=fp)
  else:
    print ('_TFAULTA__ =-0.10', file=fp)
    print ('_TFAULTB__ =-0.10', file=fp)
    print ('_TFAULTC__ =-0.10', file=fp)
  print ('BLANK END PARAMETER', file=fp)
  fp.close()
  cmdline = 'runtp ' + atp_file + ' >nul'
  pw0 = subprocess.Popen (cmdline, cwd=atp_path, shell=True)
  pw0.wait()
  amps = parse_atp_fault_current(atp_list, phs)
  return amps

with open('ReducedNetwork.atpmap', mode='r') as infile:
  for ln in infile:
    toks = ln.split()
    atp_buses[toks[0]] = toks[1]
    atp_phases[toks[0]] = toks[2]

# arrays [I3phase, Islgf, Illf]
with open('faults.csv', mode='r') as infile:
  reader = csv.reader(infile)
  next (reader, None)
  for row in reader:
    bus = row[0]
    full_faults[bus] = [float(row[1]), float(row[2]), float(row[3])]

with open('reduced_faults.csv', mode='r') as infile:
  reader = csv.reader(infile)
  next (reader, None)
  for row in reader:
    bus = row[0]
    reduced_faults[bus] = [float(row[1]), float(row[2]), float(row[3])]

#print (reduced_faults)
sorted_faults = sorted(reduced_faults.items(), key=lambda kv: kv[1], reverse=True)
print ('Bus            I3 [reduced/full/ratio]       Islgf [reduced/full/ratio]        ATP [bus/I3/rat3/I1/rat1]')
counter = 0
for flt in sorted_faults:
  bus = flt[0]
  if bus in full_faults:
    row = full_faults[bus]
    fullI3 = row[0]
    fullI1 = row[1]
    redI3 = flt[1][0]
    redI1 = flt[1][1]
    ratI3 = redI3 / fullI3
    ratI1 = redI1 / fullI1

    match = bus.strip()
    if match in atp_buses:
      atpbus = atp_buses[match]
      phs = atp_phases[match][0]
      atpI3 = 0.0
      atpI1 = 0.0
      atpI3 = get_atp_fault_current (atpbus, phs, slgf=False)
      atpI1 = get_atp_fault_current (atpbus, phs, slgf=True)
      atpRatI3 = atpI3 / fullI3
      atpRatI1 = atpI1 / fullI1
    else:
      atpbus = 'NONE'
      atpI3 = -1.0
      atpI1 = -1.0
      atpRatI3 = -1.0
      atpRatI1 = -1.0

    print ('{0:14s} {1:8.1f} {2:8.1f} {3:6.3f}  {4:14.1f} {5:8.1f} {6:6.3f}      {7:5s} {8:8.1f} {9:6.3f} {10:8.1f} {11:6.3f}'.format 
           (bus, redI3, fullI3, ratI3, redI1, fullI1, ratI1, atpbus, atpI3, atpRatI3, atpI1, atpRatI1))
    counter += 1
#  if counter > 1:
#    break

print ('compared', counter, 'buses')