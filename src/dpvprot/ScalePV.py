# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: ScalePV.py
""" Change sizes of PV, assign IEEE 1547 category.

Reads the list of PV installations from local BasePV.json file.

Writes each PV as a VCCS, resizes the interconnection transformer, and writes undervoltage
relay with Category I, II, or III settings. Output to local protected_pv.dss

Writes the distance relay for each PV to local DistanceRelaysPV.dss, to be
included from local DistanceRelays.dss that has the utility distance relays.
Writes the incremental distance relay for each PV to local TD21RelaysPV.dss, to be
included from local TD21Relays.dss that has the utility TD21 relays. The
relay settings are based on rated current and base impedance. The impedance setting,
looking out into the grid, is 0.9 times the base impedance at an angle of
10 degrees. The minimum current to trip is 1.1 times rated current. The time
to trip is fixed at 0.5 s delay plus 0.032 s breaker time. The reset time
is fixed at 5.0 s. There is one trip to lockout. Phase and ground settings
are the same.

BasePV.json contains an array of VCCS elements, as follows:

- Name (str): the name of the existing pvsystem to replace with VCCS
- Bus (str): the name of the existing bus where pvsystem is connected
- Xfmr (str): the name of the existing interconnection transformer
- Prated (float): the nominal pv rating in Watts, doesn't have to match existing pvsystem
- Vrated (float): the nominal line-to-line (for three-phase) or line-to-neutral voltage, in Volts
- Phases (int): choose 3 or 1

Public Functions:
    :main: does the work

Args:
    arg1 (float): scale factor applied to BasePV.json
    arg2 (int): IEEE 1547 disturbance category, 1..3

Returns:
    str: writes total PV kW to console

"""

import sys
import json
import math

if __name__ == '__main__':
  # usage: python ScalePV.py scaling_factor performance_category
  scale = float(sys.argv[1])
  cat = int(sys.argv[2])

  lp = open ('BasePV.json').read()
  dict = json.loads(lp)

  fp = open ('protected_pv.dss', 'w')
  print ('// replacing all pvsystem with vccs', file=fp)
  print ('batchedit pvsystem..* enabled=no', file=fp)
  if scale <= 0.0:
      print ('// zero-PV case', file=fp)
      print ('Total PV=0 kW')
      fp.close()
      quit()

  pll_str = """New XYcurve.z_pll npts=3 xarray=[1.0000 -1.98515 0.98531] yarray=[0.0000 0.01485 -0.01469]"""
  vccs_str = """~ filter='z_pll' fsample=10000 rmsmode=true imaxpu=1.15 vrmstau=0.01 irmstau=0.05"""
  print (pll_str, file=fp)

  total_kw = 0.0
  for pv in dict['vccs']:
      name = pv['Name']
      kw = 0.001 * scale * pv['Prated']
      kVbase = 0.001 * pv['Vrated']
      total_kw += kw
      print ('new vccs.{:s} Phases={:d} Bus1={:s} Prated={:.2f} Vrated={:.2f} Ppct={:.2f}'.format (name,
                                                                                                   pv['Phases'],
                                                                                                   pv['Bus'],
                                                                                                   kw * 1000.0,
                                                                                                   pv['Vrated'],
                                                                                                   100.0), file=fp)
      print (vccs_str, file=fp)
      print ('edit transformer.{:s} kvas=[{:.2f} {:.2f}]'.format (pv['Xfmr'], kw, kw), file=fp)
      print ('new relay.pv_{:s} monitoredobj=vccs.{:s} switchedobj=vccs.{:s}'.format (name, name, name), file=fp)
      print ('~  monitoredterm=1 switchedterm=1 type=voltage shots=1 delay=0.0', file=fp)
      print ('~  kvbase={:.3f} overvoltcurve=ov1547_{:d} undervoltcurve=uv1547_{:d}'.format (kVbase, cat, cat), file=fp)

  print ('calcv', file=fp)
  print ('// Total PV={:.3f} kW'.format (total_kw), file=fp)
  fp.close()

  fp = open ('TD21RelaysPV.dss', 'w')
  print ('redirect TD21Relays.dss', file=fp)
  vll = dict['vll']
  for pv in dict['vccs']:
      irated = pv['Prated'] / vll / math.sqrt(3.0)
      zrated = vll * vll / pv['Prated']
      name = pv['Name']
      zset = zrated * 0.9
      iset = irated * 1.1
      print ('new Relay.dist_{:s} type=td21 monitoredobj=Transformer.{:s} monitoredterm=1 switchedobj=vccs.{:s} switchedterm=1 breakertime=0.032'.format (name, pv['Xfmr'], name), file=fp)
      print ('~ shots=1 Reset=5.0 delay=0.5 Z1Mag={:.1f} Z1Ang=10.0 Z0Mag={:.1f} Z0Ang=10.0 Mphase=1.0 Mground=1.0 debugtrace=no distreverse=yes phasetrip={:.1f}'.format (zset, zset, iset), file=fp)
  fp.close()

  fp = open ('DistanceRelaysPV.dss', 'w')
  print ('redirect DistanceRelays.dss', file=fp)
  vll = dict['vll']
  for pv in dict['vccs']:
      irated = pv['Prated'] / vll / math.sqrt(3.0)
      zrated = vll * vll / pv['Prated']
      name = pv['Name']
      zset = zrated * 0.9
      iset = irated * 1.1
      print ('new Relay.dist_{:s} type=distance monitoredobj=Transformer.{:s} monitoredterm=1 switchedobj=vccs.{:s} switchedterm=1 breakertime=0.032'.format (name, pv['Xfmr'], name), file=fp)
      print ('~ shots=1 Reset=5.0 delay=0.5 Z1Mag={:.1f} Z1Ang=10.0 Z0Mag={:.1f} Z0Ang=10.0 Mphase=1.0 Mground=1.0 debugtrace=no distreverse=yes phasetrip={:.1f}'.format (zset, zset, iset), file=fp)
  fp.close()

  print ('Total PV={:.3f} kW'.format (total_kw))

  #for pv in dict['pvsystems']:
  #    pvname = 'pvsystem.' + pv['name']
  #    relayname = 'relay.pvv_' + pv['name']
  #    kW = '{0:.2f}'.format(scale * pv['kW'])
  #    if 'kVA' in pv:
  #        kVA = '{0:.2f}'.format(scale * pv['kVA'])
  #    else:
  #        kVA = kW
  #    kVbase = '{0:.3f}'.format(pv['kV'])
  #    print ('edit', pvname, 'pmpp=' + kW, 'kva=' + kVA, file=fp)
  #    print ('new', relayname, 'monitoredobj=' + pvname, 'switchedobj=' + pvname, file=fp)
  #    print ('~  monitoredterm=1 switchedterm=1 type=voltage shots=1 delay=0.0', file=fp)
  #    print ('~  kvbase=' + kVbase, 'overvoltcurve=ov1547_' + cat, 'undervoltcurve=uv1547_' + cat, file=fp)

  #fp.close()
