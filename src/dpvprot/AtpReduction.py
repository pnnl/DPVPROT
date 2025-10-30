# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: AtpReduction.py
""" Writes a reduced-order ATP model, based on the model reduction of a full-size OpenDSS model.
Must be called from RunReduction.py
 
Public Functions:
    :WriteAtp: does the work

Args:
    atpfile (str): the name of the ATP file to write
    pairs (array): link information passed from RunReduction.py
    retained (set): names of retained buses, passed from RunReduction.py
    buses (dict): bus information, passed from RunReduction.py 
    seqz (dict): sequence impedancs of retained branches, passed from RunReduction.py
    foundCapacitors (boolean): indicates whether feeder capacitors are in ReducedCapacitors.dss
    bNoCaps (boolean): indicates to ignore shunt capacitance in line pi-section models

Returns:
    str: writes a message if ATP file not produced
"""

import csv
import math
import sys
import subprocess
import networkx as nx

def GetAtpPhaseList(abc):
  retval = []
  if 'A' in abc:
    retval.append('A')
  if 'B' in abc:
    retval.append('B')
  if 'C' in abc:
    retval.append('C')
  return retval

def AtpNode(bus, phs):
  return '{:5s}{:1s}'.format(bus, phs)

def AtpCapNode(bus, phs):
  return 'C{:4s}{:1s}'.format(bus, phs)

def AtpDeltaLaggingNode(bus, phs):
  nd = 'B'
  if phs == 'B':
    nd = 'C'
  elif phs == 'C':
    nd = 'A'
  return AtpNode(bus, nd)

def AtpDeltaLeadingNode(bus, phs):
  nd = 'C'
  if phs == 'B':
    nd = 'A'
  elif phs == 'C':
    nd = 'B'
  return AtpNode(bus, nd)

def PadBlanks(nb):
  retval = ''
  for i in range(nb):
    retval += ' '
  return retval

def AtpRXC(r, x, c):
  return '{:16e}{:16e}{:16e}'.format(r, x, c)

def AtpFit6(x):
  if x >= 1000:
    xstr = '{:6.1f}'.format(x)
  elif x >= 100:
    xstr = '{:6.2f}'.format(x)
  elif x >= 10:
    xstr = '{:6.3f}'.format(x)
  else:
    xstr = '{:6.4f}'.format(x)
  return xstr

def AtpXfmr(r, x, v):
  return AtpFit6(r) + AtpFit6(x) + AtpFit6(v)

def AtpLoadXfmr(zb, v):
  if zb < 0.001:
    return '{:6.5f}{:6.5f}{:6.2f}'.format(0.01*zb, 0.02*zb, v)
  elif zb < 0.1:
    return '{:6.4f}{:6.4f}{:6.2f}'.format(0.01*zb, 0.02*zb, v)
  elif zb < 1.0:
    return '{:6.3f}{:6.3f}{:6.2f}'.format(0.01*zb, 0.02*zb, v)
  elif zb < 1000.0:
    return '{:6.2f}{:6.2f}{:6.2f}'.format(0.01*zb, 0.02*zb, v)
  elif zb < 100000.0:
    return '{:6.1f}{:6.1f}{:6.2f}'.format(0.01*zb, 0.02*zb, v)
  else:
    return ' 1.0E5 2.0E5{:6.2f}'.format(v)

def WriteAtp(atpfile, pairs, retained, buses, seqz, foundCapacitors, bNoCaps):
  atp_buses = {}
  atp_loads = {}
  idx = 1
  for bus in sorted(retained):
    atp_buses[bus] = str(idx)
    atp_loads[bus] = {'p':0.0,'q':0.0}
    idx += 1

  atp_capacitors = {}
  if foundCapacitors == True:
    with open('ReducedCapacitors.dss', mode='r') as infile:
      for ln in infile:
        row = ln.upper().split()
        print (row)
        if len(row) < 1:
          break
        if row[0] == 'NEW':
          kv = 0
          kvar = 0
          bus1 = ''
          cap = ''
          phases = 'ABC'
          for tok in row:
            if tok.startswith('BUS1='):
              bus1 = tok[5:]
            elif tok.startswith('BUS='):
              bus1 = tok[4:]
            elif tok.startswith('KV='):
              kv = float(tok[3:])
            elif tok.startswith('KVAR='):
              kvar = float(tok[5:])
            elif tok.startswith('CAPACITOR.'):
              cap = tok[10:]
          atp_capacitors[bus1] = {'capacitor':cap,'atpbus':atp_buses[bus1],'kvar':kvar,'kv':kv,'phases':phases}

  p_atp = 0.0
  q_atp = 0.0
  ap = open (atpfile, mode='w')
  for pair in pairs:
    idx += 1
    bus1 = pair['bus1']
    bus2 = pair['bus2']
    kv1 = buses[bus1]['kV']
    kv2 = buses[bus2]['kV']
    nt = kv1 / kv2
    seqz1 = seqz[pair['bus1']]
    seqz2 = seqz[pair['bus2']]
    r1 = abs(seqz1[1] - seqz2[1]*nt*nt) # refer to side 1
    x1 = abs(seqz1[2] - seqz2[2]*nt*nt)
    r0 = abs(seqz1[3] - seqz2[3]*nt*nt)
    x0 = abs(seqz1[4] - seqz2[4]*nt*nt)
    rslgf = abs(((2*seqz1[1]+seqz1[3]) - (2*seqz2[1]+seqz2[3])*nt*nt) / 3.0) 
    xslgf = abs(((2*seqz1[2]+seqz1[4]) - (2*seqz2[2]+seqz2[4])*nt*nt) / 3.0) 
    km = pair['len']
    nph = buses[bus1]['nph']
    nph2 = buses[bus2]['nph']
    phases = GetAtpPhaseList (buses[bus1]['phases'])
    phases2 = GetAtpPhaseList (buses[bus2]['phases'])
    atp1 = atp_buses[bus1]
    atp2 = atp_buses[bus2]
    if nph2 < nph:
      nph = nph2
      phases = phases2
    if abs(kv1 - kv2) < 0.2:
      if x0 >= 2.0 * x1: #overhead
        z0 = 800.0
        z1 = 450.0
        v0 = 2.0e5  # km/s
        v1 = 3.0e5
        linetype = 'OH'
      else: #underground
        z0 = 30.0
        z1 = 30.0
        v0 = 1.0e5
        v1 = 1.0e5
        linetype = 'UG'
      c0 = 1.0e6 / z0 / v0 / 377.0  # uF
      c1 = 1.0e6 / z1 / v1 / 377.0
      xs = (x0 + x1 + x1) / 3.0
      xm = (x0 - x1) / 3.0
      rs = (r0 + r1 + r1) / 3.0
      rm = (r0 - r1) / 3.0
      cs = (c0 + c1 + c1) / 3.0
      cm = (c0 - c1) / 3.0
      if nph == 1:
        xs = xslgf
        rs = rslgf
        cs = c1
      if bNoCaps:
        cs = 0.0
        cm = 0.0
      print ('C =============================================================================', file=ap)
      print ('C lumped line ({:s}) from {:s} to {:s}'.format (linetype, bus1, bus2), file=ap)
      print ('C < n 1>< n 2><ref1><ref2><       R      ><      L       ><      C       ><   >', file=ap)
  #    print ('C < n 1>< n 2><ref1><ref2><     R    ><    A     ><    B     ><  Length  ><><>0', file=ap)
      print ('$VINTAGE,1', file=ap)
      print ('1 ' + AtpNode (atp1, phases[0]) + AtpNode (atp2, phases[0]) + PadBlanks (12) + AtpRXC (rs, xs, cs), file=ap)
      if nph > 1:
        print ('2 ' + AtpNode (atp1, phases[1]) + AtpNode (atp2, phases[1]) + PadBlanks (12) + AtpRXC (rm, xm, cm), file=ap)
        print ('  ' + PadBlanks (24) + AtpRXC (rs, xs, cs), file=ap)
      if nph > 2:
        print ('3 ' + AtpNode (atp1, phases[2]) + AtpNode (atp2, phases[2]) + PadBlanks (12) + AtpRXC (rm, xm, cm), file=ap)
        print ('  ' + PadBlanks (24) + AtpRXC (rm, xm, cm), file=ap)
        print ('  ' + PadBlanks (24) + AtpRXC (rs, xs, cs), file=ap)
      print ('$VINTAGE,0', file=ap)
    else:
      conn = 'Wye-Wye'
      xfR1 = 0.5 * r1
      xfX1 = 0.5 * x1
      xfR2 = xfR1 * kv2 * kv2 / kv1 / kv1
      xfX2 = xfX1 * kv2 * kv2 / kv1 / kv1
      xfN1 = kv1
      xfN2 = kv2
      if x0 < 0.8 * x1:
        if kv1 > kv2:
          conn = 'Delta-Wye'
          xfN2 /= math.sqrt(3.0)
          xfR1 *= 3.0
          xfX1 *= 3.0
        else:
          conn = 'Wye-Delta'
          xfN1 /= math.sqrt(3.0)
          xfR2 *= 3.0
          xfX2 *= 3.0
      print ('C =============================================================================', file=ap)
      print ('C transformer from {:s} to {:s} is {:s}'.format (bus1, bus2, conn), file=ap)
      print ('C < n 1>< n 2><ref1><ref2><   R><   X><  KV>', file=ap)
      for ph in phases:
        xfBuses1 = AtpNode (atp1, ph)
        xfBuses2 = AtpNode (atp2, ph)
        if conn == 'Wye-Wye':
          xfBuses1 += PadBlanks(6)
          xfBuses2 += PadBlanks(6)
        elif conn == 'Delta-Wye':
          xfBuses1 += AtpDeltaLeadingNode (atp1, ph)
          xfBuses2 += PadBlanks(6)
        elif conn == 'Wye-Delta':
          xfBuses1 += PadBlanks(6)
          xfBuses2 += AtpDeltaLaggingNode (atp2, ph)
        print ('  TRANSFORMER' + PadBlanks (25) + AtpNode ('X' + atp2, ph) + ' 1.0E6', file=ap)
        print ('            9999', file=ap)
        print (' 1' + xfBuses1 + PadBlanks(12) + AtpXfmr (xfR1, xfX1, xfN1), file=ap)
        print (' 2' + xfBuses2 + PadBlanks(12) + AtpXfmr (xfR2, xfX2, xfN2), file=ap)
    pload = sum(pair['pload'])
    if pload > 0.0:
      qload = sum(pair['qload'])
      p_atp += pload
      q_atp += qload
      atp_loads[bus1]['p'] += 0.5 * pload
      atp_loads[bus2]['p'] += 0.5 * pload
      atp_loads[bus1]['q'] += 0.5 * qload
      atp_loads[bus2]['q'] += 0.5 * qload

  print ('total ATP load is {:.2f} + j {:.2f} kVA'.format (p_atp, q_atp))

  kvld = 0.12  # this is line-neutral
  atpLoadPhase = {'A':'X','B':'Y','C':'Z'}
  nLoadXfmr = 0
  for bus, load in atp_loads.items():
    pload = load['p']
    if pload > 0.0:
      qload = load['q']
      atp1 = atp_buses[bus]
      kv1 = buses[bus]['kV']
      nph = buses[bus]['nph']
      phases = GetAtpPhaseList (buses[bus]['phases'])
      print ('C =============================================================================', file=ap)
      print ('C parallel load at {:s} is {:.3f} + j{:.3f} kVA'.format (bus, pload, qload), file=ap)
      print ('C < n 1>< n 2><ref1><ref2><       R      ><      L       ><      C       ><   >', file=ap)
      print ('$VINTAGE,1', file=ap)
      pload *= 0.001 # converting kW to MW
      qload *= 0.001 # converting kVAR to MVAR
      rload = nph * kvld * kvld / pload
      for ph in phases:
        print ('  ' + AtpNode (atp1, atpLoadPhase[ph]) + PadBlanks(18) + '{:16e}'.format(rload), file=ap)
      if qload > 0.0:
        xload = nph * kvld * kvld / qload
        for ph in phases:
          print ('  ' + AtpNode (atp1, atpLoadPhase[ph]) + PadBlanks(34) + '{:16e}'.format(xload), file=ap)
      sload = math.sqrt (pload * pload + qload * qload) / nph # MVA per phase
      if bNoCaps == False:
        cuf = 20.0 * sload * 0.001  # 1 nF per 50 kVA transformer
        for ph in phases:
          print ('  ' + AtpNode (atp1, ph) + PadBlanks(50) + '{:16e}'.format(cuf), file=ap)
      print ('$VINTAGE,0', file=ap)
      if nph > 1:
        kv1 /= math.sqrt(3.0)
      zbase1 = 0.5 * kv1 * kv1 / sload  # half of each transformer impedance on each winding
      zbld = 0.5 * kvld * kvld / sload
      nLoadXfmr += 1
      print ('C < n 1>< n 2><ref1><ref2><   R><   X><  KV>', file=ap)
      for ph in phases:
        print ('  TRANSFORMER' + PadBlanks (25) + AtpNode ('Y' + str(nLoadXfmr), ph) + ' 1.0E6', file=ap)
        print ('            9999', file=ap)
        print (' 1' + AtpNode (atp1, ph) + PadBlanks(18) + AtpLoadXfmr (zbase1, kv1), file=ap)
        print (' 2' + AtpNode (atp1, atpLoadPhase[ph]) + PadBlanks(18) + AtpLoadXfmr (zbld, kvld), file=ap)

  for bus in atp_capacitors:
    atp1 = atp_capacitors[bus]['atpbus']
    cap = atp_capacitors[bus]['capacitor']
    kv = atp_capacitors[bus]['kv']
    kvar = atp_capacitors[bus]['kvar']
    cuf = 1000.0 * kvar / kv / kv / 377.0
    print ('C =============================================================================', file=ap)
    print ('C capacitor {:s} at {:s} is {:.2f} kVAR'.format (cap, bus, kvar), file=ap)
    print ('C < n 1>< n 2><ref1><ref2><       R      ><      L       ><      C       ><   >', file=ap)
    print ('$VINTAGE,1', file=ap)
    for ph in ['A','B','C']:
      print ('  ' + AtpCapNode (atp1, ph) + PadBlanks(50) + '{:16e}'.format(cuf), file=ap)
    print ('$VINTAGE,0', file=ap)
  ap.close()

  ab = open ('ReducedNetwork.atpmap', mode='w')
  for key in atp_buses:
    print (key, atp_buses[key], buses[key]['phases'], file=ab)
  ab.close()

