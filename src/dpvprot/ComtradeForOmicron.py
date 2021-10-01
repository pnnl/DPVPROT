# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: ComtradeLoopForOmicron.py
""" Outputs 10-kHz COMTRADE files for Omicron from ATP COMTRADE files.

Paragraph.

Public Functions:
    :main: does the work
"""

import sys
import math
from comtrade import Comtrade
import numpy as np
from scipy import signal
import datetime as dt

def comtrade_dt_format(ts):
    ret = '{:02d}/{:02d}/{:4d},{:02d}:{:02d}:{:02d}.{:06d}'.format (ts.day,ts.month,ts.year,
                                                              ts.hour,ts.minute,ts.second,
                                                              ts.microsecond)
    return ret

feeders = [{'directory':'c:/pl4/SHE215','FdrKV':12.47,
            'PV':['PVONE', 'PVTWO'],'Vbase':[480.0,480.0],'Sbase':[1e6,1e6],'XFM':['PVXF1','PVXF2'],'ZL':[2.4,2.4],
            'capdirectory':'c:/pl4/Capacitors'},
           {'directory':'c:/pl4/RIV209','FdrKV':12.47,
            'PV':['PVPCC'],'Vbase':[480.0],'Sbase':[1e6],'XFM':['PVXFM'],'ZL':[3.0],
            'capdirectory':'c:/pl4/Capacitors'},
           {'directory':'c:/pl4/Louisa','FdrKV':34.50,'ZL':[8.0],
            'PV':['PVPCC'],'Vbase':[416.0],'Sbase':[20e6],'XFM':['PVXFM'],
            'capdirectory':'c:/pl4/Capacitors'}]

subdir = sys.argv[1]   # to match the feeder directory
busname = sys.argv[2]  # to match the original bus or device name
busnum = sys.argv[3]   # mapped ATP bus number
phases = sys.argv[4]   # either CAPS, ABC or A
loc = sys.argv[5]      # to pick out the pvname, either PVONE, PVTWO or PVPCC
q = int(sys.argv[6])   # decimation factor
fname = sys.argv[7]    # root for COMTRADE cfg and dat files 
for row in feeders:
    if subdir in row['directory']:
        fdr = row

fpath = fdr['directory'] + '/' + fname
station = subdir + ' ' + busname + ' ' + busnum + ' ' + loc
if len(phases) == 3:
    atp_base = fdr['directory'] + '/I3_' + busnum
    station = station + ' I3' 
else:
    atp_base = fdr['directory'] + '/I1_' + busnum
    station = station + ' I1' 
pvChannels = {}
pvnames = []
xfnames = {}
npv = len(fdr['PV'])
for i in range(npv):
    pv = fdr['PV'][i]
    xf = fdr['XFM'][i]
    pvnames.append(pv)
    xfnames[pv] = xf
    pvChannels[pv] = {'Va':-1,'Vb':-1,'Vc':-1,'Ia':-1,'Ib':-1,'Ic':-1,
        'XfVa':-1,'XfVb':-1,'XfVc':-1,'XfIa':-1,'XfIb':-1,'XfIc':-1}

rec = Comtrade()
rec.load(atp_base + '.cfg', atp_base + '.dat')
t = np.array(rec.time)
n = int(rec.total_samples)
fs = int(rec.cfg.sample_rates[0][0])  # there will be only one from ATP

tdec = t[::q]
ndec = int (tdec.shape[0])

for i in range(rec.analog_count):
    lbl = rec.analog_channel_ids[i]
    vals = rec.analog[i]
    a = rec.cfg.analog_channels[i].a
    b = rec.cfg.analog_channels[i].b
    if 'V-node' in lbl:
        for pv in pvnames:
            xf = xfnames[pv]
            if xf+'A' in lbl:
                pvChannels[pv]['XfVa'] = [signal.decimate (np.array (vals), int(q)), a, b]
            elif xf+'B' in lbl:
                pvChannels[pv]['XfVb'] = [signal.decimate (np.array (vals), int(q)), a, b]
            elif xf+'C' in lbl:
                pvChannels[pv]['XfVc'] = [signal.decimate (np.array (vals), int(q)), a, b]
    elif 'I-branch' in lbl:
        for pv in pvnames:
            xf = xfnames[pv]
            if pv+'A' in lbl:
                pvChannels[pv]['Ia'] = [signal.decimate (np.array (vals), int(q)), a, b]
            elif pv+'B' in lbl:
                pvChannels[pv]['Ib'] = [signal.decimate (np.array (vals), int(q)), a, b]
            elif pv+'C' in lbl:
                pvChannels[pv]['Ic'] = [signal.decimate (np.array (vals), int(q)), a, b]
            elif xf+'A' in lbl:
                pvChannels[pv]['XfIa'] = [signal.decimate (np.array (vals), int(q)), a, b]
            elif xf+'B' in lbl:
                pvChannels[pv]['XfIb'] = [signal.decimate (np.array (vals), int(q)), a, b]
            elif xf+'C' in lbl:
                pvChannels[pv]['XfIc'] = [signal.decimate (np.array (vals), int(q)), a, b]
    elif 'V-branch' in lbl:
        for pv in pvnames:
            xf = xfnames[pv]
            if pv+'A' in lbl:
                pvChannels[pv]['Va'] = [signal.decimate (np.array (vals), int(q)), a, b]
            elif pv+'B' in lbl:
                pvChannels[pv]['Vb'] = [signal.decimate (np.array (vals), int(q)), a, b]
            elif pv+'C' in lbl:
                pvChannels[pv]['Vc'] = [signal.decimate (np.array (vals), int(q)), a, b]

print ('original fs =', fs, 'n =', n, '; decimated by', q, 'to fs=', int (fs/q), 'and n=', ndec)
print ('writing to', fpath + '.cfg')

cp = open (fpath + '.cfg', 'w')
print ('{:s},999,1999'.format (station), file=cp)
print ('12,12A,0D', file=cp)
for key, chan in pvChannels.items():
    i = 0
    for tok in ['Va', 'Vb', 'Vc', 'Ia', 'Ib', 'Ic', 'XfVa', 'XfVb', 'XfVc', 'XfIa', 'XfIb', 'XfIc']:
        i += 1
        ary = chan[tok]
        vals = ary[0]
        a = ary[1]
        b = ary[2]
        if 'V' in tok:
            uu = 'V'
        else:
            uu = 'A'
        phs = tok[-1:].upper()
        print ('{:s} {:4s} MaxAbs={:8.2f} a={:15.12g} b={:15.12g}'.format (key, tok, np.max(abs(vals)), a, b))
        print ('{:d},{:s},{:s},,{:s},{:.12g},{:.12g},0.0,-99999,99999,1.0,1.0,P'.format(i,tok,phs,uu,a,b), file=cp)
print ('60', file=cp)
print ('1', file=cp)
print ('{:d},{:d}'.format (int(fs/q), ndec), file=cp)
print (comtrade_dt_format(rec.start_timestamp), file=cp)
print (comtrade_dt_format(rec.trigger_timestamp), file=cp)
print ('ASCII', file=cp)
print ('1.0', file=cp)
cp.close()

dp = open (fpath + '.dat', 'w')
for j in range(ndec):
    line = '{:d},{:d}'.format(j+1, int(1.0e6*tdec[j]))
    for tok in ['Va', 'Vb', 'Vc', 'Ia', 'Ib', 'Ic', 'XfVa', 'XfVb', 'XfVc', 'XfIa', 'XfIb', 'XfIc']:
        vals = chan[tok][0]
        a = chan[tok][1]
        b = chan[tok][2]
        ival = int ((vals[j] - b) / a)
        line += ',{:d}'.format (ival)
    print (line, file=dp)
dp.close()

