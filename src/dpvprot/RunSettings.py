# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: RunSettings.py
""" Finds the load current and source impedances at OpenDSS reclosers, then
applies heuristics to recommend distance and incremental distance relay settings.

Do 'opendsscmd SettingStudy.dss' first. The local SettingStudy.dss file needs to
define the OpenDSS model and run a power flow solution at nominal load, with no DER.
Then it runs a faultstudy solution at no-load, with controls, protection and DER
all disabled. Output files from both solutions are used to determine the loads,
source impedance, and recommended settings for each utility device.

Reads a local recloser_buses.dat file. Each line contains a comma-separated
OpenDSS bus name, and the name of an OpenDSS recloser at the bus. The script uses
the source impedance at the bus, the load current through the recloser, and network
topology information to recommend settings. The reclosers to coordinate are based
on a networkx topology constructed from the OpenDSS energymeter zone.

The OpenDSS solution files read are the same as in RunReduction.py:
    bus data from cktname + '_Buses.Txt'
    element data from cktname + '_Elements.Txt'
    bus voltage and distance profile from cktname + '_EXP_Profile.CSV'
    short-circuit impedances from cktname + '_EXP_SEQZ.CSV'
    power flow solution from cktname + '_Power_elem_kVA.txt'
    feeder meter zone from cktname + '_ZoneOut_feeder.txt'

The analysis method is to build a networkx topology graph, with links to the power flow
solution and faultstudy impedances from OpenDSS. Each recloser can determine the next upstream 
device by tracing back to the source. Furthermore, each faultable bus can find its closest 
upstream recloser, which is expected to clear the fault, by tracing back to the source. When this
fault-bus trace encounters a recloser, that recloser keeps the faultable bus with highest X1 value
as the remote bus, which the recloser should see for backup purposes. These
graph traces only consider devices at the same voltage level, so they don't try to coordinate
through transformers. When all these traces finish, each recloser has its expected load current, and
the necessary equivalent source impedances for coordination.

The output report begins with a summary of each recloser from recloser_buses.dat:
    The bus name
    The recloser name
    The full-load current [kA] and nominal voltage [kV] at the bus
    The positive and zero-sequence equivalent source impedances [Ohms] at this recloser, called Zs1 and Zs0
    The positive and zero-sequence equivalent source impedances [Ohms] at the next downstream recloser, called Zn1 and Zn0
    The positive and zero-sequence equivalent source impedances [Ohms] at a remote downstream bus, called Zr1 and Zr0
    Nzone, the number of faultable buses in this recloser's primary protection zone. May include first bus in the next zone.
    NextRec, the name of the nearest downstream recloser considered for coordination. There may be other downstream reclosers, farther away electrically.
    RemoteBus, the name of the remote bus considered in reach setting

The next two output tables contain Zone 1 and Zone 2 impedance settings, positive and negative sequence,
recommended for each recloser. The first of these tables is in rectangular coordinates,
the second in polar coordinates. Zone 1 is the impedance difference between this recloser and the next downstream.
Zone 2 is the impedance difference between this recloser and the remote bus. However, these are full-reach settings.
To use them, Zone 1 should be used with a multiplier of 0.8 to 0.9, while Zone 2 should be increased with a multiplier
of at least 1.25 to ensure full coverage. Furthermore, in OpenDSS each Zone would be implemented with a separate
recloser device, attached at the same location.

The last output table contains the settings used in this project. It is based on a single Zone, full reach to the 
remote bus or nearest downstream recloser, whichever is farthest, and a minimum pickup of 1.2 times full load current. 
The settings are formatted in the syntax for OpenDSS relay parameters.
To use these settings, coordination should be achieved with define time delays, where the time delays decrease with 
the recloser's distance from the substation.

Public Functions:
    :main: does the work

Args:
    cktname (str): the root name (not the file name) of the OpenDSS circuit, used to find outputs from SettingStudy.dss

Returns:
    str: writes progress messages to console, ending with the settings report
"""

import csv
import math
import sys
import networkx as nx

cktname = sys.argv[1]
fname_bus = cktname + '_Buses.Txt'
fname_profile = cktname + '_EXP_Profile.CSV'
fname_seqz = cktname + '_EXP_SEQZ.CSV'
fname_elements = cktname + '_Elements.Txt'
fname_power = cktname + '_Power_elem_kVA.txt'
fname_zone = cktname + '_ZoneOut_feeder.txt'

seqz = {}
with open(fname_seqz, mode='r') as infile:
  reader = csv.reader(infile)
  next (reader, None)
  for row in reader:
    bus = row[0].upper()
    nph = int(row[1])
    r1 = float(row[2])
    x1 = float(row[3])
    r0 = float(row[4])
    x0 = float(row[5])
    seqz[bus] = [nph,r1,x1,r0,x0]

buses = {}
with open(fname_bus, mode='r') as infile:
  for i in range(6):
    next (infile)
  for line in infile:
#    print (line)
    row = line.split()
    bus = row[0].strip('"').upper()
    kV = float(row[1])
    nph_col = 8
    try:
        x = float(row[3])
    except:
        x = 0.0
        nph_col = 7 # because the NA, appears as one token, not NA ,
    try:
        y = float(row[5])
    except:
        y = 0.0
    nph = int(row[nph_col])
    phA = False
    phB = False
    phC = False
    for i in range(nph):
        phs = int(row[nph_col+1+i])
        if phs == 1:
            phA = True
        elif phs == 2:
            phB = True
        elif phs == 3:
            phC = True
    phases = ''
    if phA:
        phases = phases + 'A'
    if phB:
        phases = phases + 'B'
    if phC:
        phases = phases + 'C'
    buses[bus] = {'kV':kV, 'x':x, 'y':y, 'nph': nph, 'phases': phases, 'dist': 0}

lines = {}
transformers = {}
elements = {}
with open(fname_elements, mode='r') as infile:
  for i in range(7):
    next (infile)
  for line in infile:
    row = line.split()
    if len(row) < 1:
      break  # one-bus power conversion elements are up next
    key = row[0].strip('"').upper()
    bus1 = row[1].upper()
    bus2 = row[2].upper()
    toks = key.split('.')
    elements[key] = {'class':toks[0],'name':toks[1],'bus1':bus1,'bus2':bus2}
    if toks[0] == 'LINE':
      lines[toks[1]] = {'bus1':bus1,'bus2':bus2}
    elif toks[0] == 'TRANSFORMER':
      transformers[toks[1]] = {'bus1':bus1,'bus2':bus2}

dist = {}
with open(fname_profile, mode='r') as infile:
    reader = csv.reader(infile)
    next (reader, None)
    for row in reader:
        branch = row[0].upper()
        d1 = float(row[1])
        d2 = float(row[3])
        dist[branch] = [d1,d2]
        if branch in lines:
            buses[lines[branch]['bus1']]['dist'] = d1
            buses[lines[branch]['bus2']]['dist'] = d2

reclosers = {}
retained = []
with open('recloser_buses.dat', mode='r') as infile:
    reader = csv.reader(infile)
    next (reader, None)
    for row in reader:
        bus = row[0].upper()
        tag = row[1]
        retained.append (bus)
        zs = seqz[bus]
        reclosers[bus] = {'tag': tag, 'Iload': 0.0, 'kV': buses[bus]['kV'], 
            'Nzone':0, 'NearestDownstream': '', 'RemoteBus': '',
            'Zs1.re':zs[1], 'Zs1.im':zs[2], 'Zs0.re':zs[3], 'Zs0.im':zs[4], # source impedance
            'Zn1.re':1000.0, 'Zn1.im':1000.0, 'Zn0.re':1000.0, 'Zn0.im':1000.0, # min impedance to next device
            'Zr1.re':0.0, 'Zr1.im':0.0, 'Zr0.re':0.0, 'Zr0.im':0.0} # max impedance in my zone

# print ('retained {:d} recloser buses'.format(len(retained)), retained)

# read the snapshot power flows at recloser buses
bInElement = False
bus1 = ''
bus2 = ''
bus_phs_p = [[0.0, 0.0, 0.0],[0.0, 0.0, 0.0]]
bus_phs_q = [[0.0, 0.0, 0.0],[0.0, 0.0, 0.0]]
powers = {}
branch_buses = {}
with open(fname_power, mode='r') as infile:
  for ln in infile:
    line = ln.strip()
    if len(line) < 1:
      continue
    if 'ELEMENT =' in line:
      row = line.split()
      key = row[2].strip('"').upper()
      toks = key.split('.')
      bclass = toks[0]
      bname = toks[1]
      bInElement = False
      if bclass == 'LINE':
        bus1 = lines[bname]['bus1']
        bus2 = lines[bname]['bus2']
        bInElement = True
      elif bclass == 'TRANSFORMER':
        bus1 = transformers[bname]['bus1']
        bus2 = transformers[bname]['bus2']
        bInElement = True
      if bInElement:
        bus_phs_p = [[0.0, 0.0, 0.0],[0.0, 0.0, 0.0]]
        bus_phs_q = [[0.0, 0.0, 0.0],[0.0, 0.0, 0.0]]
        branch_buses[bclass + '.' + bname] = [bus1, bus2]
        if bus1 in retained or bus2 in retained:
          powers[key] = {'class':bclass,'name':bname,'bus1':bus1,'bus2':bus2,'p':bus_phs_p,'q':bus_phs_q}
    elif 'TERMINAL TOTAL' in line:
      continue
    elif 'Power Conversion Elements' in line:
      break
    elif '= = = = = = =' in line:
      break
    elif bInElement == True:
#      print (line)
      row = line.split()
      bus = row[0].strip('"').upper()
      phs = int(row[1])
      p = float(row[2])
      q = float(row[4])
      if phs > 0:
        if bus == bus1:
          bus_phs_p[0][phs-1] = p
          bus_phs_q[0][phs-1] = q
        elif bus == bus2:
          bus_phs_p[1][phs-1] = p
          bus_phs_q[1][phs-1] = q

print (len(powers),'branch power flows at retained buses')
for rec, recval in reclosers.items():
#  print ('Recloser {:s} at {:s} power flows:'.format (recval['tag'], rec))
  SphIn = 0.0  # keep track of the maximum kVA into the bus, total and by phase
  StotIn = 0.0
  SphOut = 0.0 # keep track of the maximum kVA out of the bus, total and by phase
  StotOut = 0.0
  for key, val in powers.items():
    if (rec == val['bus1']) or (rec == val['bus2']):
#      print ('  {:22s} {:10s} {:10s}'.format (key, val['bus1'], val['bus2']), val['p'], val['q'])
      Sph = 0.0
      Stot = 0.0
      Ptot = 0.0
      if rec == val['bus1']:
        end = 0
      else:
        end = 1
      for i in range(3):
        p = val['p'][end][i]
        q = val['q'][end][i]
        s = math.sqrt(p*p+q*q)
        Ptot += p
        Stot += s
        if s > Sph:
          Sph = s
      if Ptot < 0.0:
        StotOut += Stot
        if Sph > SphOut:
          SphOut = Sph
      else:
        StotIn += Stot
        if Sph > SphIn:
          SphIn = Sph
  Sph = max(SphIn, SphOut)
  Stot = max(StotIn, StotOut)
  Itot = Stot / math.sqrt(3) / recval['kV']
  Iph = Sph * math.sqrt(3) / recval['kV']
  recval['Iload'] = max (Itot, Iph)
#  print ('  StotIn={:.2f} StotOut={:.2f} SphIn={:.2f} SphOut={:.2f} Itot={:.2f} Iph={:.2f}'.format (StotIn, StotOut,
#    SphIn, SphOut, Itot, Iph))

# read the full-model meter zones
G = nx.Graph()
nAdded = 0
nNotAdded = 0
source_bus = None
with open(fname_zone, mode='r') as infile:
  for ln in infile:
    line = ln.strip().upper()
    if ('LINE.' in line) or ('TRANSFORMER.' in line):
      level = ln.count('\t')
      idx = line.find('(')
      idxb = line.find(' ')
      if idxb >= 0 and idxb < idx:
        idx = idxb
      branch = line[:idx]
      if branch in branch_buses:
          bus1 = branch_buses[branch][0]
          if source_bus is None:
              source_bus = bus1
          bus2 = branch_buses[branch][1]
          G.add_edge (bus1, bus2)
          G[bus1][bus2]['name'] = branch
          nAdded += 1
      else:
          nNotAdded += 1
#      print (level, branch, bus1, bus2)
print ('Added {:d} branches to graph, {:d} not added, source bus is {:s}'.format (nAdded, nNotAdded, source_bus))

# Now check all the faultable buses; trace back to source; stop at the first recloser.
#   If that first recloser and faultable bus are at the same voltage level, update Z values for that recloser.
#   Otherwise, continue to the next faultable bus. (At least for now, we are not attempting to coordinate through transformers.)
for bus, bval in buses.items():
    if bus not in G.nodes():  # could be the transmission source, or another bus behind the EnergyMeter
        continue
    bkV = bval['kV']
    r1 = seqz[bus][1]
    x1 = seqz[bus][2]
    r0 = seqz[bus][3]
    x0 = seqz[bus][4]
#    print (bus, bkV, r1, x1, r0, x0)
    route = nx.shortest_path(G, bus, source_bus)
#    print (route)
    for b in route:
        if b in reclosers:
            rec = reclosers[b]
            if abs(rec['kV'] - bkV) < 0.1:
#                print ('found {:s} at same voltage level'.format (rec['tag']))
                rec['Nzone'] += 1
                if r1 > rec['Zr1.re']:
                    rec['Zr1.re'] = r1
                if x1 > rec['Zr1.im']:
                    rec['Zr1.im'] = x1
                    rec['RemoteBus'] = bus
                if r0 > rec['Zr0.re']:
                    rec['Zr0.re'] = r0
                if r0 > rec['Zr0.im']:
                    rec['Zr0.im'] = x0
                break

# now find the downstream reclosers
for bus, rec in reclosers.items():
    r1 = seqz[bus][1]
    x1 = seqz[bus][2]
    r0 = seqz[bus][3]
    x0 = seqz[bus][4]
    route = nx.shortest_path(G, bus, source_bus)
    for b in route:
         if bus == b:
             continue
         if b in reclosers:
             if x1 < reclosers[b]['Zn1.im']:
                 reclosers[b]['Zn1.re'] = r1
                 reclosers[b]['Zn1.im'] = x1
                 reclosers[b]['Zn0.re'] = r0
                 reclosers[b]['Zn0.im'] = x0
                 reclosers[b]['NearestDownstream'] = rec['tag']
             break


print ('\nRecloser Setting Data for {:s} from {:s}'.format(cktname, source_bus))
print ('Bus      Label    Iload/kV              Zs1/Zs0              Zn1/Zn0              Zr1/Zr0 Nzone  NextRec RemoteBus')
for key, val in reclosers.items():
    Zs1 = '{:.2f}+j{:.2f}'.format(val['Zs1.re'], val['Zs1.im'])
    Zs0 = '{:.2f}+j{:.2f}'.format(val['Zs0.re'], val['Zs0.im'])
    Zn1 = '{:.2f}+j{:.2f}'.format(val['Zn1.re'], val['Zn1.im'])
    Zn0 = '{:.2f}+j{:.2f}'.format(val['Zn0.re'], val['Zn0.im'])
    Zr1 = '{:.2f}+j{:.2f}'.format(val['Zr1.re'], val['Zr1.im'])
    Zr0 = '{:.2f}+j{:.2f}'.format(val['Zr0.re'], val['Zr0.im'])
    print ('{:8s} {:8s} {:>8.2f} {:>20s} {:>20s} {:>20s} {:5d} {:>8s} {:s}'.format (key, val['tag'], val['Iload'], 
                                                                        Zs1, Zn1, Zr1, val['Nzone'],
                                                                        val['NearestDownstream'],
                                                                        val['RemoteBus']))
    print ('                  {:>8.2f} {:>20s} {:>20s} {:>20s}'.format (val['kV'], Zs0, Zn0, Zr0))

print ('\nRectangular Coordinate Settings')
print ('Bus      Label               Zone 1(1)            Zone 1(0)            Zone 2(0)            Zone 2(0)')
for key, val in reclosers.items():
    if val['Zn1.im'] < 1000.0:
        Zone1pos = '{:.2f}+j{:.2f}'.format (val['Zn1.re'] - val['Zs1.re'], val['Zn1.im'] - val['Zs1.im'])
        Zone1zero = '{:.2f}+j{:.2f}'.format (val['Zn0.re'] - val['Zs0.re'], val['Zn0.im'] - val['Zs0.im'])
    else:
        Zone1pos = 'N/A'
        Zone1zero = 'N/A'
    Zone2pos = '{:.2f}+j{:.2f}'.format (val['Zr1.re'] - val['Zs1.re'], val['Zr1.im'] - val['Zs1.im'])
    Zone2zero = '{:.2f}+j{:.2f}'.format (val['Zr0.re'] - val['Zs0.re'], val['Zr0.im'] - val['Zs0.im'])
    print ('{:8s} {:8s} {:>20s} {:>20s} {:>20s} {:>20s}'.format (key, val['tag'], Zone1pos, Zone1zero,
                                                                 Zone2pos, Zone2zero))

print ('\nPolar Coordinate Settings')
print ('Bus      Label               Zone 1(1)            Zone 1(0)            Zone 2(1)            Zone 2(0)')
for key, val in reclosers.items():
    if val['Zn1.im'] < 1000.0:
        re = val['Zn1.re'] - val['Zs1.re']
        im = val['Zn1.im'] - val['Zs1.im']
        mag = math.sqrt (re*re+im*im)
        ang = math.atan2 (im, re) * 180.0 / math.pi
        Zone1pos = '{:.2f}<{:.2f}'.format (mag, ang)
        re = val['Zn0.re'] - val['Zs0.re']
        im = val['Zn0.im'] - val['Zs0.im']
        mag = math.sqrt (re*re+im*im)
        ang = math.atan2 (im, re) * 180.0 / math.pi
        Zone1zero = '{:.2f}<{:.2f}'.format (mag, ang)
    else:
        Zone1pos = 'N/A'
        Zone1zero = 'N/A'
    re = val['Zr1.re'] - val['Zs1.re']
    im = val['Zr1.im'] - val['Zs1.im']
    mag = math.sqrt (re*re+im*im)
    ang = math.atan2 (im, re) * 180.0 / math.pi
    Zone2pos = '{:.2f}<{:.2f}'.format (mag, ang)
    re = val['Zr0.re'] - val['Zs0.re']
    im = val['Zr0.im'] - val['Zs0.im']
    mag = math.sqrt (re*re+im*im)
    ang = math.atan2 (im, re) * 180.0 / math.pi
    Zone2zero = '{:.2f}<{:.2f}'.format (mag, ang)
    print ('{:8s} {:8s} {:>20s} {:>20s} {:>20s} {:>20s}'.format (key, val['tag'], Zone1pos, Zone1zero,
                                                                     Zone2pos, Zone2zero))
print ('\nFull Coverage Polar Coordinate Settings')
#print ('Bus      Label                      Z1                   Z0')
print ('Bus     Device    Settings')
for key, val in reclosers.items():
    z1re = val['Zr1.re'] - val['Zs1.re']
    z1im = val['Zr1.im'] - val['Zs1.im']
    z0re = val['Zr0.re'] - val['Zs0.re']
    z0im = val['Zr0.im'] - val['Zs0.im']
    if val['Zn1.im'] < 1000.0:  # if the nearest downstream recloser exists, use the maximum of impedances to it, or the remote bus
        z1re = max (z1re, val['Zn1.re'] - val['Zs1.re'])
        z1im = max (z1im, val['Zn1.im'] - val['Zs1.im'])
        z0re = max (z0re, val['Zn0.re'] - val['Zs0.re'])
        z0im = max (z0im, val['Zn0.im'] - val['Zs0.im'])
    z1mag = math.sqrt (z1re*z1re + z1im*z1im)
    z1ang = math.atan2 (z1im, z1re) * 180.0 / math.pi
    Zpos = '{:.2f}<{:.2f}'.format (z1mag, z1ang)
    z0mag = math.sqrt (z0re*z0re + z0im*z0im)
    z0ang = math.atan2 (z0im, z0re) * 180.0 / math.pi
    Zzero = '{:.2f}<{:.2f}'.format (z0mag, z0ang)
    print ('{:8s} {:8s} Reset=60.0 Z1MAG={:.3f} Z1ANG={:.3f} Z0MAG={:.3f} Z0ANG={:.3f} Mphase=1.0 Mground=2.5 phasetrip={:.1f}'.format (key, 
      val['tag'], z1mag, z1ang, z0mag, z0ang, 1.2 * val['Iload']))
#   print ('{:8s} {:8s} {:>20s} {:>20s} Z1MAG={:.3f} Z1ANG={:.3f} Z0MAG={:.3f} Z0ANG={:.3f}'.format (key,
#                                                                                                    val['tag'],
#                                                                                                    Zpos,
#                                                                                                    Zzero,
#                                                                                                    z1mag,
#                                                                                                    z1ang,
#                                                                                                    z0mag,
#                                                                                                    z0ang))

