# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: MakePV.py
""" Make ATP Transformer and PV Model Call

Public Functions:
    :main: does the work
"""

import math

# assuming wye/wye for now

PVs = [{'Bus':'59', 'Hi':'B51854',      'Lo':'PV1', 'XfKva':300.0, 'PVkW':285.0},
      {'Bus':'3',  'Hi':'5865228330A', 'Lo':'PV2', 'XfKva': 225.0, 'PVkW':190.0},
      {'Bus':'PVXFM',  'Hi':'5890628219',  'Lo':'PV3', 'XfKva':1000.0, 'PVkW':760.0},
      {'Bus':'52', 'Hi':'B4832',       'Lo':'PV4', 'XfKva': 500.0, 'PVkW':475.0}]
kvHigh = 12.47
kvLow = 0.416
xfX = 0.050
xfR = 0.005
ipu = 1.15

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

ap = open ('../ATP/J1Solar.atp', mode='w')
phases = ['A','B','C']

for pv in PVs:
  kv1 = kvHigh
  kv2 = kvLow
  nt = kv1 / kv2
  nph = 3
  nph2 = 3
  atp1 = pv['Bus']
  atp2 = pv['Lo']
  zbase = 1000.0 * kv1 * kv1 / pv['XfKva']
  xfR1 = 0.5 * xfR * zbase
  xfX1 = 0.5 * xfX * zbase
  xfR2 = xfR1 / nt / nt
  xfX2 = xfX1 / nt / nt
  xfN1 = kv1
  xfN2 = kv2
  print ('C =============================================================================', file=ap)
  print ('C {:s} is {:.2f} kW through {:.2f} kVA transformer'.format (pv['Lo'], pv['PVkW'], pv['XfKva']), file=ap)
  print ('C < n 1>< n 2><ref1><ref2><   R><   X><  KV>', file=ap)
  for ph in phases:
    xfBuses1 = AtpNode (atp1, ph)
    xfBuses2 = AtpNode (atp2, ph)
    xfBuses1 += PadBlanks(6)
    xfBuses2 += PadBlanks(6)
    print ('  TRANSFORMER' + PadBlanks (25) + AtpNode ('X' + atp2, ph) + ' 1.0E5', file=ap)
    print ('            9999', file=ap)
    print (' 1' + xfBuses1 + PadBlanks(12) + AtpXfmr (xfR1, xfX1, xfN1), file=ap)
    print (' 2' + xfBuses2 + PadBlanks(12) + AtpXfmr (xfR2, xfX2, xfN2), file=ap)
  print ('94' + AtpNode (atp2, 'A') + PadBlanks(6) + 'PV3FLLNORT' + PadBlanks(55) + '3', file=ap)
  print ('94' + AtpNode (atp2, 'B') + PadBlanks(71) + '3', file=ap)
  print ('94' + AtpNode (atp2, 'C') + PadBlanks(71) + '3', file=ap)
  vbase = 1000.0 * kvLow
  wtotal = 1.0e3 * pv['PVkW']
  kwtotal = round(pv['PVkW'])
  irmsmax = ipu * wtotal / vbase / math.sqrt(3.0)
  print (' >DATA  WC          377.', file=ap)
  print (' >DATA  K          1.414', file=ap)
  print (' >DATA  GAMMA        46.', file=ap)
  print (' >DATA  VBASE     {:6.1f}'.format (vbase), file=ap)
  print (' >DATA  ANG0         0.0', file=ap)
  print (' >DATA  WTOTAL    {:3d}.E3'.format (kwtotal), file=ap)
  print (' >DATA  PFANG        0.0', file=ap)
  print (' >DATA  IRMSMX    {:6.1f}'.format (irmsmax), file=ap)
  print (' >END                   ', file=ap)
  print ('C < n1 >< n2 ><ref1><ref2>< R  >< L  >< C  >', file=ap)
  for ph in phases:
    print (PadBlanks(8) + AtpNode (atp2, ph) + '              50.0      0.250', file=ap)

ap.close()

