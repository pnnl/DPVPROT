# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: CheckReducedLoads.py
""" Run and tabulate ATP phasor solutions.

Checks full and reduced feeder load, with and without PV.

Public Functions:
    :main: does the work
"""

import csv
import math
import sys
import operator
import subprocess

atp_base = sys.argv[1]
atp_path = '../../ATP/'
atp_file = atp_base + '.atp'
atp_list = atp_path + atp_base + '.lis'
atp_parm = atp_path + atp_base + '.prm'

fdr_head = sys.argv[2]
pvsystem = sys.argv[3]
dss_vpu = float(sys.argv[4])
atp_vpu = float(sys.argv[5])

fdr_elem = 'LINE.' + fdr_head.upper()
pv_elem = 'PVSYSTEM.' + pvsystem.upper()

master_dss_file = 'RIV_master.dss'
tokPVPCCA = 'PVPCCA'
tokPVPCCB = 'PVPCCB'
tokPVPCCC = 'PVPCCC'

if 'Louisa' in atp_base:
  master_dss_file = 'Master.dss'
  tokPVPCCA = 'PVXFMA'
  tokPVPCCB = 'PVXFMB'
  tokPVPCCC = 'PVXFMC'

if 'SHE' in atp_base:
  master_dss_file = 'SHE_master.dss'
  tokPVPCCA = 'PVTWOA'
  tokPVPCCB = 'PVTWOB'
  tokPVPCCC = 'PVTWOC'

def atp_line_value(line, tok, pos):
  vals = line.split(tok)
  toks = vals[1].split()
  return float(toks[pos])

def atp_line_end_value(line, pos):
  vals = line.split()
  last = len(vals) - 1
  return float(vals[last + pos])

def parse_atp_loadflow(fname):
  vfdra = 0.0
  vfdrb = 0.0
  vfdrc = 0.0

  vpcca = 0.0
  vpccb = 0.0
  vpccc = 0.0

  pfdra = 0.0
  pfdrb = 0.0
  pfdrc = 0.0

  qfdra = 0.0
  qfdrb = 0.0
  qfdrc = 0.0

  ppcca = 0.0
  ppccb = 0.0
  ppccc = 0.0

  qpcca = 0.0
  qpccb = 0.0
  qpccc = 0.0

  foundCurrents = False
  foundVoltages = False
  fp = open (fname, mode='r')
  for ln in fp:
    if foundCurrents:
      if 'FDR  A' in ln:
        pfdra = atp_line_end_value (ln, -1)
        qfdra = atp_line_end_value (ln, 0)
      if 'FDR  B' in ln:
        pfdrb = atp_line_end_value (ln, -1)
        qfdrb = atp_line_end_value (ln, 0)
      if 'FDR  C' in ln:
        pfdrc = atp_line_end_value (ln, -1)
        qfdrc = atp_line_end_value (ln, 0)
      if 'PVPCCA' in ln:
        ppcca = atp_line_end_value (ln, -1)
        qpcca = atp_line_end_value (ln, 0)
      if 'PVPCCB' in ln:
        ppccb = atp_line_end_value (ln, -1)
        qpccb = atp_line_end_value (ln, 0)
      if 'PVPCCC' in ln:
        ppccc = atp_line_end_value (ln, -1)
        qpccc = atp_line_end_value (ln, 0)
    if foundVoltages:
      if tokPVPCCA in ln:
        vpcca = atp_line_value (ln, tokPVPCCA, 0)
      if tokPVPCCB in ln:
        vpccb = atp_line_value (ln, tokPVPCCB, 0)
      if tokPVPCCC in ln:
        vpccc = atp_line_value (ln, tokPVPCCC, 0)
      if 'FDR  A' in ln:
        vfdra = atp_line_value (ln, 'FDR  A', 0)
      if 'FDR  B' in ln:
        vfdrb = atp_line_value (ln, 'FDR  B', 0)
      if 'FDR  C' in ln:
        vfdrc = atp_line_value (ln, 'FDR  C', 0)
    if 'Begin steady-state printout of EMTP output variables.   Node voltage outputs follow.' in ln:
      foundVoltages = True
      foundCurrents = False
    elif 'Output for steady-state phasor switch currents' in ln:
      foundCurrents = True
      foundVoltages = False
    elif 'Selective branch outputs follow (for column-80 keyed branches only)' in ln:
      foundCurrents = False
      foundVoltages = False
    elif 'Solution at nodes with known voltage.' in ln:
      foundCurrents = False
      foundVoltages = False
  fp.close()

  vfdr = (vfdra + vfdrb + vfdrc) / 3.0 / fdr_basev
  vpcc = (vpcca + vpccb + vpccc) / 3.0 / pcc_basev
  pfdr = (pfdra + pfdrb + pfdrc) / 1000
  qfdr = (qfdra + qfdrb + qfdrc) / 1000
  ppcc = (ppcca + ppccb + ppccc) / 1000
  qpcc = (qpcca + qpccb + qpccc) / 1000

  return vfdr, vpcc, pfdr, qfdr, ppcc, qpcc

def get_atp_loadflow(bus, fdr_basev):
  vsrc = '{:.2f}'.format (atp_vpu * fdr_basev)
  fp = open (atp_parm, mode='w')
  print ('$PARAMETER', file=fp)
  print ('_FLT_=\'' + bus.ljust(5) + '\'', file=fp)
  print ('____TMAX   =-1.0', file=fp)
  print ('_TFAULTA__ =9.05', file=fp)
  print ('_TFAULTB__ =9.05', file=fp)
  print ('_TFAULTC__ =9.05', file=fp)
  print ('_VSOURCE__ =' + vsrc, file=fp)
  print ('BLANK END PARAMETER', file=fp)
  fp.close()
  cmdline = 'runtp ' + atp_file + ' >nul'
  pw0 = subprocess.Popen (cmdline, cwd=atp_path, shell=True)
  pw0.wait()
  vfdr, vpcc, pfdr, qfdr, ppcc, qpcc = parse_atp_loadflow(atp_list)
  return vfdr, vpcc, pfdr, qfdr, ppcc, qpcc

def get_opendss_loadflow(basefile, irrad):
  fp = open ('scripted.dss', 'w')
  print ('redirect ' + basefile, file=fp)
  print ('edit pvsystem.' + pvsystem + ' irradiance=' + str(irrad), file=fp)
  print ('solve mode=snap', file=fp)
  print ('export summary', file=fp)
  print ('export elempowers', file=fp)
  print ('export voltageselements', file=fp)
  fp.close()
  subprocess.run (['opendsscmd', 'scripted.dss'], capture_output=True)

  vmin = 0.0
  vmax = 0.0
  vpcc = 0.0
  ppcc = 0.0
  qpcc = 0.0
  vfdr = 0.0
  pfdr = 0.0
  qfdr = 0.0
  with open (fdr_head + '_EXP_Summary.CSV', 'r') as fp:
    reader = csv.reader(fp)
    next (reader, None)
    for row in reader:
      vmax = float(row[15])
      vmin = float(row[16])
  with open (fdr_head + '_EXP_VOLTAGES_ELEM.CSV', 'r') as fp:
    reader = csv.reader(fp)
    next (reader, None)
    for row in reader:
      if (pv_elem == row[0].upper()) or (fdr_elem == row[0].upper()):
        nph = float(row[4])
        vavg = float(row[10])
        if nph > 1.0:
          vavg += float(row[14])
        if nph > 2.0:
          vavg += float(row[18])
        vavg /= nph
        if pv_elem == row[0].upper():
          vpcc = vavg
        else:
          vfdr = vavg

  with open (fdr_head + '_EXP_ElemPowers.CSV', 'r') as fp:
    reader = csv.reader(fp)
    next (reader, None)
    for row in reader:
      if (pv_elem == row[0].upper()) or (fdr_elem == row[0].upper()):
        ncond = float(row[2])
        psum = float(row[3])
        qsum = float(row[4])
        if ncond > 1.0:
          psum += float(row[5])
          qsum += float(row[6])
        if ncond > 2.0:
          psum += float(row[7])
          qsum += float(row[8])
        if pv_elem == row[0].upper():
          ppcc = psum
          qpcc = qsum
        else:
          pfdr = psum
          qfdr = qsum

  return vmin, vmax, vfdr, vpcc, pfdr, qfdr, ppcc, qpcc

def get_opendss_voltage_bases():
  vbase_fdr = 1.0
  vbase_pcc = 1.0
  with open (fdr_head + '_EXP_VOLTAGES_ELEM.CSV', 'r') as fp:
    reader = csv.reader(fp)
    next (reader, None)
    for row in reader:
      if pv_elem == row[0].upper():
        vbase_pcc = 1000.0 * float(row[6]) * math.sqrt(2.0/3.0)
      elif fdr_elem == row[0].upper():
        vbase_fdr = 1000.0 * float(row[6]) * math.sqrt(2.0/3.0)
  return vbase_fdr, vbase_pcc

print ('DESCRIPTION       Vmin   Vmax   Vfdr   Vpcc    Pfdr      Qfdr     Ppcc')
# 1 - run the full load flow without PV
vmin, vmax, vfdr, vpcc, pfdr, qfdr, ppcc, qpcc = get_opendss_loadflow (master_dss_file, 0.01)
print ('Full without PV {:6.4f} {:6.4f} {:6.4f} {:6.4f} {:7.1f} +j {:6.1f} {:8.1f} '.format (vmin, vmax, vfdr, vpcc, pfdr, qfdr, ppcc))

# 2 - run the full load flow with PV
vmin, vmax, vfdr, vpcc, pfdr, qfdr, ppcc, qpcc = get_opendss_loadflow (master_dss_file, 1.0)
print ('Full with PV    {:6.4f} {:6.4f} {:6.4f} {:6.4f} {:7.1f} +j {:6.1f} {:8.1f} '.format (vmin, vmax, vfdr, vpcc, pfdr, qfdr, ppcc))

# 3 - run the reduced load flow without PV
vmin, vmax, vfdr, vpcc, pfdr, qfdr, ppcc, qpcc = get_opendss_loadflow ('Reduced.dss', 0.01)
print ('Reduce w/o PV   {:6.4f} {:6.4f} {:6.4f} {:6.4f} {:7.1f} +j {:6.1f} {:8.1f} '.format (vmin, vmax, vfdr, vpcc, pfdr, qfdr, ppcc))
# now find the feeder head and PV PCC voltage bases
fdr_basev, pcc_basev = get_opendss_voltage_bases ()

# 4 - run the reduced load flow with PV
vmin, vmax, vfdr, vpcc, pfdr, qfdr, ppcc, qpcc = get_opendss_loadflow ('Reduced.dss', 1.0)
print ('Reduce w/ PV    {:6.4f} {:6.4f} {:6.4f} {:6.4f} {:7.1f} +j {:6.1f} {:8.1f} '.format (vmin, vmax, vfdr, vpcc, pfdr, qfdr, ppcc))

# 5 - run the ATP phasor solution without PV
vfdr, vpcc, pfdr, qfdr, ppcc, qpcc = get_atp_loadflow ('5', fdr_basev)
print ('ATP w/o PV                    {:6.4f} {:6.4f} {:7.1f} +j {:6.1f} {:8.1f} '.format (vfdr, vpcc, pfdr, qfdr, ppcc))

# 6 - run the ATP phasor solution with PV - TODO, we don't have Type 94 model initialization yet


print ('Feeder and PCC voltage bases for ATP are {:.3f} {:.3f}'.format (fdr_basev, pcc_basev))
