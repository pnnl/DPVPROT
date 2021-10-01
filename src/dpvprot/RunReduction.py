# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: RunReduction.py
""" Reduce full-size OpenDSS model to smaller OpenDSS and ATP models. The name of the
circuit, cktname, is the first command-line argument and it must match the circuit name
from the original OpenDSS model.
 
Reads buspairs.dat, created by the user. Each line contains two comma-separated bus names,
with phasing if appropriate, for links to be retained in the reduced model. The set of all
bus names referenced in this file will be retained in the reduced model. The retained buses
should include breakers, reclosers, capacitors, large DER, large loads, line regulators, major
junction points, and remote ends of feeder branches. The OpenDSS circuit plots can help
identify the important buses to retain. In buspairs.dat, annotations may be added to the end
of each line, using // to indicate such a comment.

Reads ReducedCapacitors.dss, created by the user. If there are any capacitors in the
original model, they should be copied into this new file. Their buses should also be
retained in buspairs.dat. They will appear explicitly in the generated ATP model.

Reads these files created by solving local ReductionStudy.dss in OpenDSS:

- bus data from cktname + '_Buses.Txt'
- element data from cktname + '_Elements.Txt'
- bus voltage and distance profile from cktname + '_EXP_Profile.CSV'
- short-circuit impedances from cktname + '_EXP_SEQZ.CSV'
- power flow solution from cktname + '_Power_elem_kVA.txt'
- feeder meter zone from cktname + '_ZoneOut_feeder.txt'

To create these files:

- copy TOCRelays.dss UtilityRelays.dss
- opendsscmd ReductionStudy.dss

Writes ReducedNetwork.dss with OpenDSS components between retained buses.

Writes ReducedXY.dss with coordinates of retained buses.

Writes ReducedNetwork.json for plotting and topology analysis. The format is documented
with plot_opendss_feeder.py.

Writes ReducedNetwork.atpmap to help compare OpenDSS and ATP results on the reduced
model. Each line has three space-separated tokens:

- the retained OpenDSS bus name
- the retained ATP bus name, which will be a sequential number
- A, B, and/or C to indicate the phases present at the retained bus

Writes atpfile with ATP components.

To use the reduced model in OpenDSS, the user should create a file like Reduced.dss,
which includes ReducedNetwork.dss, ReducedCapacitors.dss, and ReducedXY.dss. The Reduced.dss
file should also create the circuit, relays, reclosers, substation transformer, substation regulator
if applicable, and an energymeter at the feeder breaker, looking out into the circuit.
It should create any large DER to be studied initially; later, the user might use
ScalePV.py with BasePV.json to add more DER/PV locations of different sizes. The
Reduced.dss file should contain edit or batchedit commands to adjust base component settings
and values to accommodate the DER and obtain a good power flow solution. The file should
end with commands that calculate voltage bases and set the load multiplier.

To use the reduced model in ATP, the user might specify atpfile like ReducedNetwork.atp in a
different directory than the OpenDSS files. This file might then be included from a master
ATP file, which must also include the ATP solution parameters, substation model, DER model, etc.
The user needs an ATP license and ATP documentation to complete these steps.

Public Functions:
    :main: does the work

Args:
    cktname (str): the root name of the OpenDSS circuit to be reduced
    atpfile (str): the name of the ATP file to write

Returns:
    str: writes total PV kW to console
"""

import csv
import math
import sys
import subprocess
import networkx as nx
import dpvprot.AtpReduction as atp

bNoCaps = False  # set True if we want to ignore capacitance in the ATP line pi-section models

def GetOpenDSSPhases(abc):
  retval = ''
  if 'A' in abc:
    retval = retval + '.1'
  if 'B' in abc:
    retval = retval + '.2'
  if 'C' in abc:
    retval = retval + '.3'
  return retval

def GetAtpPhaseList(abc):
  retval = []
  if 'A' in abc:
    retval.append('A')
  if 'B' in abc:
    retval.append('B')
  if 'C' in abc:
    retval.append('C')
  return retval

if __name__ == '__main__':
  cktname = sys.argv[1]
  atpfile = sys.argv[2]
  fname_bus = cktname + '_Buses.Txt'
  fname_profile = cktname + '_EXP_Profile.CSV'
  fname_seqz = cktname + '_EXP_SEQZ.CSV'
  fname_elements = cktname + '_Elements.Txt'
  fname_power = cktname + '_Power_elem_kVA.txt'
  fname_zone = cktname + '_ZoneOut_feeder.txt'

  print ('Reading buses from   ', fname_bus)
  print ('Reading elements from', fname_elements)
  print ('Reading profile from ', fname_profile)
  print ('Reading seq Z from   ', fname_seqz)
  print ('Reading power from   ', fname_power)
  print ('Reading zones from   ', fname_zone)
  print ('Writing ATP network to', atpfile)

  pairs = []
  retained = set()
  with open('buspairs.dat', mode='r') as infile:
    reader = csv.reader(infile)
    for row in reader:
      if len(row) > 1:
        bus1 = row[0].upper().split('.')[0]
        bus2 = row[1].upper().split('.')[0]
        retained.add(bus1)
        retained.add(bus2)
        pairs.append ({'bus1':bus1,'bus2':bus2})
  print ('there are', len(retained), 'retained buses')
  # print (sorted(retained))

  # subprocess.run (['opendsscmd', 'ReductionStudy.dss'])

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

  dist = {}
  with open(fname_profile, mode='r') as infile:
    reader = csv.reader(infile)
    next (reader, None)
    for row in reader:
      branch = row[0].upper()
      d1 = float(row[1])
      d2 = float(row[3])
      dist[branch] = [d1,d2]

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

  foundCapacitors = False
  nCapacitors = 0
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
      if toks[0] == 'CAPACITOR':
        foundCapacitors = True
        nCapacitors += 1
      elif toks[0] == 'LINE':
        lines[toks[1]] = {'bus1':bus1,'bus2':bus2}
      elif toks[0] == 'TRANSFORMER':
        transformers[toks[1]] = {'bus1':bus1,'bus2':bus2}

  print ('Found', nCapacitors, 'Capacitors')

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

  for pair in pairs:
      seqz1 = seqz[pair['bus1']]
      seqz2 = seqz[pair['bus2']]
      pair['nphases'] = seqz1[0]
      pair['len'] = abs(buses[pair['bus1']]['dist'] - buses[pair['bus2']]['dist'])

  print ('there are', len(pairs), 'reduced branches')

  # read the snapshot power flows at retained buses
  bInElement = False
  #bBus1 = False
  #bBus2 = False
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

  print ('**', len(powers),'branch power flows at retained buses')
  #for key in powers:
  #  elm = powers[key]
  #  print (key, elm['class'], elm['name'], elm['bus1'], elm['bus2'], elm['p'], elm['q'])

  # read the full-model meter zones
  G = nx.Graph()
  nAdded = 0
  nNotAdded = 0
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
            bus2 = branch_buses[branch][1]
            G.add_edge (bus1, bus2)
            G[bus1][bus2]['name'] = branch
            nAdded += 1
        else:
            nNotAdded += 1
  #      print (level, branch, bus1, bus2)
  print ('Branches added to graph =', nAdded, 'not added =', nNotAdded)

  # print (nx.shortest_path (G, '172049D0', '87375'))
  # try to match up the full-network branch flows to the corresponding reduced branch
  total_pload = 0.0
  total_qload = 0.0
  for pair in pairs:
    bus1 = pair['bus1']
    bus2 = pair['bus2']
    path12 = nx.shortest_path (G, bus1, bus2)
    path21 = nx.shortest_path (G, bus2, bus1)
    next12 = path12[1]
    next21 = path21[1]
    key12 = ''
    end12 = 0
    key21 = ''
    end21 = 0
    for key in powers:
      br1 = powers[key]['bus1']
      br2 = powers[key]['bus2']
      if (br1 == bus1) and (br2 == next12):
        key12 = key
        end12 = 1
      elif (br1 == next12) and (br2 == bus1):
        key12 = key
        end12 = 2
      if (br1 == bus2) and (br2 == next21):
        key21 = key
        end21 = 1
      elif (br1 == next21) and (br2 == bus2):
        key21 = key
        end21 = 2
    p12 = powers[key12]['p'][end12-1]
    q12 = powers[key12]['q'][end12-1]
    p21 = powers[key21]['p'][end21-1]
    q21 = powers[key21]['q'][end21-1]
    pload = [round(a_i + b_i,3) for a_i, b_i in zip(p12, p21)]
    qload = [round(a_i + b_i,3) for a_i, b_i in zip(q12, q21)]
    total_pload += (sum(pload))
    total_qload += (sum(qload))
    if sum(pload) < 0.0:
        print ('pair', bus1, bus2, pload, sum(pload), '{:.2f}'.format (total_pload), qload)
        print ('  from 1-2:', bus1, next12, key12, end12, '{:3f}'.format(sum(p12)), '{:3f}'.format(sum(q12)))
        print ('  from 2-1:', bus2, next21, key21, end21, '{:3f}'.format(sum(p21)), '{:3f}'.format(sum(q21)))
        print (' ', nx.shortest_path (G, bus1, bus2))
    pair['pload'] = pload
    pair['qload'] = qload
  print ('found total load of {:.3f} + j{:.3f} kva in the pairs'.format (total_pload, total_qload))

  total_pload = 0.0
  total_qload = 0.0
  idx = 0
  op = open ('ReducedNetwork.dss', mode='w')
  for pair in pairs:
    idx += 1
    bus1 = pair['bus1']
    bus2 = pair['bus2']
    kv1 = buses[bus1]['kV']
    kv2 = buses[bus2]['kV']
    nt = kv1 / kv2
    seqz1 = seqz[pair['bus1']]
    seqz2 = seqz[pair['bus2']]
    km = pair['len']
    nph = buses[bus1]['nph']
    nph2 = buses[bus2]['nph']
    phases = GetOpenDSSPhases (buses[bus1]['phases'])
    phases2 = GetOpenDSSPhases (buses[bus2]['phases'])
    r1 = abs(seqz1[1] - seqz2[1]*nt*nt) # refer to side 1
    x1 = abs(seqz1[2] - seqz2[2]*nt*nt)
    r0 = abs(seqz1[3] - seqz2[3]*nt*nt)
    x0 = abs(seqz1[4] - seqz2[4]*nt*nt)
    rslgf = abs(((2*seqz1[1]+seqz1[3]) - (2*seqz2[1]+seqz2[3])*nt*nt) / 3.0) 
    xslgf = abs(((2*seqz1[2]+seqz1[4]) - (2*seqz2[2]+seqz2[4])*nt*nt) / 3.0) 
    if nph2 < nph:
      nph = nph2
      phases = phases2
    if float(buses[bus1]['dist']) > float(buses[bus2]['dist']):
      bus1phs = bus2 + phases
      bus2phs = bus1 + phases
      kv1 = buses[bus2]['kV']
      kv2 = buses[bus1]['kV']
    else:
      bus1phs = bus1 + phases
      bus2phs = bus2 + phases
    if abs(kv1 - kv2) < 0.2:
      if x0 >= 2.0 * x1: #overhead
        z0 = 800.0
        z1 = 450.0
        v0 = 2.0e5  # km/s
        v1 = 3.0e5
      else: #underground
        z0 = 30.0
        z1 = 30.0
        v0 = 1.0e5
        v1 = 1.0e5
      c0 = 1.0e9 / z0 / v0 / 377.0  # nF
      c1 = 1.0e9 / z1 / v1 / 377.0
      print ('new line.' + str(idx) + ' phases=' + str(nph) + 
             ' bus1=' + bus1phs + ' bus2=' + bus2phs, file=op);
      if nph > 1:
        print ('~   r1={:.5f}'.format(r1) + ' x1={:.5f}'.format(x1) + 
               ' r0={:.5f}'.format(r0) + ' x0={:.5f}'.format(x0) +
               ' c1={:.5f} c0={:.5f} // len={:.5f}'.format(c1, c0, km), file=op)
      else:
        print ('~   rmatrix=[{:5f}] xmatrix=[{:.5f}] cmatrix=[0] // len={:.5f}'.format(rslgf, xslgf, km), file=op)
    else:
      if kv1 > kv2:
        zbase = kv1 * kv1
      else:
        zbase = kv2 * kv2
      conns = '(w w)'
      bSecondaryDelta = False
      bPrimaryDelta = False
      if x0 < 0.8 * x1:
        if kv1 > kv2:
          conns = '(d w)'
          bPrimaryDelta = True
        else:
          conns = '(w d)'
          bSecondaryDelta = True
      xhl = 100.0 * x1 / zbase
      sbase = 1000.0
      kv1base = kv1
      kv2base = kv2
      if nph == 2:
        sbase /= 1.5
      elif nph == 1:
        sbase /= 3.0
        if bSecondaryDelta == False:
          kv2base /= math.sqrt(3)
        if bPrimaryDelta == False:
          kv1base /= math.sqrt(3)
      print ('new transformer.{:d} phases={:d} buses=({:s} {:s}) conns={:s}'.format (idx, nph, bus1phs, bus2phs, conns), file=op);
      print ('~   kvs=({:.3f} {:.3f}) kvas=({:.2f} {:.2f}) xhl={:.5f}'.format(kv1base,kv2base,sbase,sbase,xhl), file=op)
      print ('~   // r1={:.5f} x1={:.5f} r0={:.5f} x0={:.5f}'.format(r1, x1, r0, x0), file=op)
    pload = sum(pair['pload'])
    qload = sum(pair['qload'])
    if pload > 0.0:
      total_pload += pload
      total_qload += qload
      if pload > 3000.0:
        print (bus1, bus2, pair['pload'], '{:.2f}'.format(pload))
        print (nx.shortest_path (G, bus1, bus2))
      pload *= 0.5
      qload *= 0.5
      if nph < 2:
          kv1 /= math.sqrt(3)
          kv2 /= math.sqrt(3)
          kv1 = round(kv1, 3)
          kv2 = round(kv2, 3)
      print ('new load.' + str(idx) + '_1 phases=' + str(nph) + \
             ' bus1=' + bus1phs + ' kv=' + str(kv1) + ' conn=wye model=2' + \
             ' kw={:.3f}'.format(pload) + ' kvar={:.3f}'.format(qload), file=op)
      print ('new load.' + str(idx) + '_2 phases=' + str(nph) + \
             ' bus1=' + bus2phs + ' kv=' + str(kv2) + ' conn=wye model=2' + \
             ' kw={:.3f}'.format(pload) + ' kvar={:.3f}'.format(qload), file=op)

  op.close()
  print ('wrote total load of {:.3f} + j{:.3f} kva to the reduced OpenDSS network file'.format (total_pload, total_qload))

  xp = open ('ReducedXY.dss', mode='w')
  for val in sorted(retained):
    bus = buses[val]
    print (val,'{:.5f}'.format(float(bus['x'])),'{:.5f}'.format(float(bus['y'])),
           '{:9.5f}'.format(float(bus['dist'])),sep='\t',file=xp)
  xp.close()

  atp.WriteAtp(atpfile, pairs, retained, buses, seqz, foundCapacitors, bNoCaps)
  quit()

  # informational output for debugging
  for pair in pairs:
      print (pair['bus1'], pair['bus2'], '{:.5f}'.format(pair['r1']), 
             '{:.5f}'.format(pair['x1']), '{:.5f}'.format(pair['r0']), 
             '{:.5f}'.format(pair['x0']), '{:.5f}'.format(pair['len']),
             '{:.5f}'.format(pair['xperkm']))


