# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: RunFaults.py
""" Run the OpenDSS event study and tabulates results. The event study
consists of a series of dynamic fault simulations, defined in a local
EventStudy.dss file. This file needs to define the feeder model (typically
full-size, not reduced, with DER and relays. The simulation time should
be long enough to ensure that all relay and fault events have settled out
for each fault. It must also include a monitor for at least the fault current.
Other monitors may exist for plotting, but the script runs faster if they are commented out.

The script reads a local buslist.dat to determine the fault types and locations.
Each line of this file contains comma-separate values as follows:

- busname (str): the OpenDSS to fault
- phase (str): A, B, and/or C for the phases present. Three-phase, single-phase, and line-to-line faults will be applied as appropriate
- Rf (float): the maximum fault resistance, in Ohms, for the SLGF. Bolted faults are also created, currently hard-coded to 0.01 Ohms
- targets (str): a comma-separated list of selective devices that are expected to trip to clear the fault. Typically, this is one utility device and several DER devices.

The script writes scripted_fault.dss for each fault to simulate,
then invokes opendsscmd on EventStudy.dss, which needs to include
scripted_fault.dss.

Writes events.out with summary information.

Appends to dofaults.rpt with summary information, ending with a list of devices 
that didn't behave properly in at least one fault scenario. The user may focus
investigation on these devices.

The summary information for each fault is:

- Bus (str): the faulted bus name
- Nphases (int): the number of faulted phases.
- Rf (float): the fault resistance in Ohms
- If (float): the fault current in kA
- Status (str): the convergence status of the OpenDSS dynamic simulation, should always be SOLVED
- Cleared (boolean): indicate whether the fault was cleared
- Tcleared (float): the fault clearing time, in s
- Nopen (int): the number of devices locked open
- Nreclosed (int): the number of utility devices that tripped and reclosed
- Nfailed (int): the number of utility devices that failed to trip
- Nfalse (int): the number of utility devices that false-tripped, e.g., sympathetic or non-directional
- Npv (int): the number of PV devices that tripped (and locked open)
- Sopen (str): a quoted comma-separated list of utility devices that locked open
- Sreclosed (str): a quoted comma-separated list of utility devices that tripped and reclosed
- Sfailed (str): a quoted comma-separated list of utility devices that failed to trip
- Sfalse (str): a quoted comma-separated list of utility devices that false-tripped
- Spv (str): a quoted comma-separated list of DER devices that tripped (and locked open)

Public Functions:
    :main: does the work

Args:
    cktname (str): the root name (not the file name) of the OpenDSS circuit. The script needs this to find summary and monitor outputs from each fault simulation.

Returns:
    str: writes a progress message as each fault is simulated

"""

import csv
import math
import sys
import subprocess
import os

def getSLGFbus (bus, phases):
  if 'C' in phases:
    return bus + '.3'
  elif 'B' in phases:
    return bus + '.2'
  else:
    return bus + '.1'

def getLLFbus (bus, phases):
  if 'A' in phases:
    if 'B' in phases:
      return bus + '.1.2'
    else:
      return bus + '.1.3'
  else:
    return bus + '.2.3'

def is_tripping_device (dvc):
  if len(dvc) < 3:
    return False
  if dvc.startswith('regulator.'):
    return False
  if dvc.startswith('capacitor.'):
    return False
  if dvc.startswith('swtcontrol.'):
    return False
  return True

def is_pv_device (dvc):
  if 'pv_' in dvc:
    return True
  return False

if __name__ == '__main__':
  bus_targets = {}
  bus_phases = {}
  max_rf = {}
  false_trip_faults = {}
  failed_trip_faults = {}
  uncleared_faults = []
  rf_bolt = 0.01
  vary_slgf_rf = False
  ckt_name = sys.argv[1]

  with open('buslist.dat', mode='r') as infile:
    reader = csv.reader(infile)
    for row in reader:
      bus = row[0]
      bus_phases[bus] = row[1]
      max_rf[bus] = float(row[2])
      targets = []
      for i in range (3, len(row)):
        targets.append (row[i].lower())  # the input target name should be fully qualified
      bus_targets[bus] = targets

  faults = []
  ontime = 0.1
  for bus, phases in bus_phases.items():
    if len(phases) > 2: # three-phase fault
      faults.append ({'bus': bus, 'phases': 3, 'rf': rf_bolt, 'targets': bus_targets[bus], 'temporary': True, 'ontime': ontime})
    if len(phases) > 1: # two-phase fault
      fltbus = getLLFbus (bus, phases)
      faults.append ({'bus': fltbus, 'phases': 2, 'rf': rf_bolt, 'targets': bus_targets[bus], 'temporary': True, 'ontime': ontime})
    # single-phase faults
    fltbus = getSLGFbus (bus, phases)
    rgf_max = max_rf[bus]
    faults.append ({'bus': fltbus, 'phases': 1, 'rf': rf_bolt, 'targets': bus_targets[bus], 'temporary': True, 'ontime': ontime})
    if vary_slgf_rf:
      faults.append ({'bus': fltbus, 'phases': 1, 'rf': rgf_max / 3.0, 'targets': bus_targets[bus], 'temporary': True, 'ontime': ontime})
      faults.append ({'bus': fltbus, 'phases': 1, 'rf': rgf_max / 1.5, 'targets': bus_targets[bus], 'temporary': True, 'ontime': ontime})
      faults.append ({'bus': fltbus, 'phases': 1, 'rf': rgf_max, 'targets': bus_targets[bus], 'temporary': True, 'ontime': ontime})

  nflt = len(faults)
  idx = 0

  op = open ('events.out', 'w')
  rp = open ('dofaults.rpt', 'a+')
  print ('Bus,Nphases,Rf,If,Status,Cleared?,Tcleared,Nopen,Nreclosed,Nfailed,Nfalse,Npv,Sopen,Sreclosed,Sfailed,Sfalse,Spv', file=op)
  print ('Bus,Nphases,Rf,If,Status,Cleared?,Tcleared,Nopen,Nreclosed,Nfailed,Nfalse,Npv,Sopen,Sreclosed,Sfailed,Sfalse,Spv', file=rp)

  for flt in faults:
    idx += 1
    targets = flt['targets']
    bus = flt['bus']
    nph = flt['phases']
    ontime = flt['ontime']
    if flt['temporary']:
      temporary = 'yes'
    else:
      temporary = 'no'
    rf = flt['rf']

    print ('{:d} of {:d} faults at {:s}, {:d} phases, rf={:.3f}, ontime={:.3f}, temporary={:s}'.format(idx, nflt, bus, nph, rf, ontime, temporary), file=rp)
    print ('  target devices are ', targets, file=rp)
    print ('{:d} of {:d} faults'.format (idx, nflt))

    fp = open ('scripted_fault.dss', 'w')
    print ('new fault.flt bus1={:s} phases={:d} ontime={:.3f} r={:.3f} temporary={:s}'.format (bus, nph, ontime, rf, temporary), file=fp)
    fp.close()

    subprocess.run (['opendsscmd', 'EventStudy.dss'])

    states = {}
    events = {}
    tcleared = -1.0
    bcleared = False
    tapplied = -1.0
    operated = set()
    lockopen = set()
    failtrips = set()
    falsetrips = set()
    pvtrips = set()
    solveStatus = '?'

    sname = ckt_name + '_EXP_Summary.CSV'
    if os.path.exists(sname):
      with open(sname, mode='r') as infile:
        reader = csv.reader(infile)
        next(reader)
        for row in reader:
          solveStatus = (row[2]).strip()
      os.remove(sname)
    
    ifault = 0.0
    with open(ckt_name + '_Mon_flt.csv', mode='r') as infile:
      i1 = 2 + nph
      i2 = i1 + nph
      reader = csv.reader(infile)
      next(reader)
      for row in reader:
        for i in range (i1, i2):
          ival = float (row[i])
          if ival > ifault:
            ifault = ival

    with open('events.csv', mode='r') as infile:
      reader = csv.reader(infile)
      for row in reader:
        sec = row[1].split('=')[1]
        dvc = row[3].split('=')[1]
        act = row[4].split('=')[1]
        if len(dvc) > 0:
          dvc = dvc.lower()
        if is_tripping_device (dvc):
          if dvc == 'fault.flt':
            if act == '**APPLIED**':
              tapplied = float (sec)
            if act == '**CLEARED**':
              tcleared = float (sec)
          else:
            operated.add (dvc)
          states[dvc] = act
          events[sec, dvc] = act
    if tcleared > 0.0:
      tcleared -= tapplied
      bcleared = True
    else:
      uncleared_faults.append(bus)
    for dvc in operated:
      if is_pv_device (dvc):
        if dvc not in pvtrips:
          pvtrips.add(dvc)
      elif dvc not in targets:
        falsetrips.add(dvc)
        if dvc not in false_trip_faults:
          false_trip_faults[dvc] = []
        false_trip_faults[dvc].append(bus)
      if states[dvc] != 'CLOSED':
        lockopen.add(dvc)
    momentary = operated - lockopen
    for dvc in targets:
      if dvc not in operated:
        if is_pv_device (dvc) and bcleared:
          pass
        else:
          failtrips.add(dvc)
          if dvc not in failed_trip_faults:
            failed_trip_faults[dvc] = []
          failed_trip_faults[dvc].append(bus)
    event_line = '"{:s}",{:d},{:.3f},{:.1f},{:s},{:s},{:.4f},{:d},{:d},{:d},{:d},{:d},"{:s}","{:s}","{:s}","{:s}","{:s}"'.format (bus,nph,rf,ifault,solveStatus,str(bcleared),tcleared,
      len(lockopen), len(momentary), len (failtrips), len (falsetrips), len (pvtrips),
      ','.join(lockopen), ','.join(momentary), ','.join(failtrips), ','.join(falsetrips), ','.join(pvtrips))
    print (event_line, file=op)
    print (event_line, file=rp)

  # op.close()
  # rp.close()
  # quit()

  op.close()
  print ('Uncleared Faults: ', ','.join(uncleared_faults), file=rp)
  print ('Failed Trip Devices/Faults:', file=rp)
  for key, vals in failed_trip_faults.items():
      print ('  {:s},{:s}'.format (key, ','.join(vals)), file=rp)
  print ('False Trip Devices/Faults:', file=rp)
  for key, vals in false_trip_faults.items():
      print ('  {:s},{:s}'.format (key, ','.join(vals)), file=rp)
  rp.close()
