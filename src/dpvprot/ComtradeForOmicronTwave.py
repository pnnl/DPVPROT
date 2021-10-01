# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: ComtradeLoopForOmicronTwave.py
""" Outputs 5-MHz COMTRADE files for Omicron from ATP COMTRADE files.

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
           {'directory':'c:/pl4/LouisaTwave','FdrKV':34.50,'ZL':[8.0],
            'PV':['PVPCC'],'Vbase':[416.0],'Sbase':[20e6],'XFM':['PVXFM'],
            'capdirectory':'c:/pl4/Capacitors'}]

fdrdir = sys.argv[1]   # to match the feeder directory
busname = sys.argv[2]  # to match the original bus or device name
busnum = sys.argv[3]   # mapped ATP bus number
phases = sys.argv[4]   # either CAPS, ABC or A
loc = sys.argv[5]      # to pick out the pvname, either PVONE, PVTWO or PVPCC
subdir = sys.argv[6]   # subdirectory, e.g., 1MHz or 5MHz
fname = sys.argv[7]    # root for COMTRADE cfg and dat files 
for row in feeders:
    if fdrdir in row['directory']:
        fdr = row

inpath = fdr['directory'] + '/' + subdir + '/'
outpath = fdr['directory'] + '/Omicron/' + fname
station = fdrdir + ' ' + busname + ' ' + busnum + ' ' + loc
if len(phases) == 3:
    atp_base = inpath + '/I3_' + busnum
    station = station + ' I3' 
else:
    atp_base = inpath + '/I1_' + busnum
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

for i in range(rec.analog_count):
    lbl = rec.analog_channel_ids[i]
    vals = rec.analog[i]
    a = rec.cfg.analog_channels[i].a
    b = rec.cfg.analog_channels[i].b
    if 'V-node' in lbl:
        for pv in pvnames:
            xf = xfnames[pv]
            if xf+'A' in lbl:
                pvChannels[pv]['XfVa'] = [np.array (vals), a, b]
            elif xf+'B' in lbl:
                pvChannels[pv]['XfVb'] = [np.array (vals), a, b]
            elif xf+'C' in lbl:
                pvChannels[pv]['XfVc'] = [np.array (vals), a, b]
    elif 'I-branch' in lbl:
        for pv in pvnames:
            xf = xfnames[pv]
            if pv+'A' in lbl:
                pvChannels[pv]['Ia'] = [np.array (vals), a, b]
            elif pv+'B' in lbl:
                pvChannels[pv]['Ib'] = [np.array (vals), a, b]
            elif pv+'C' in lbl:
                pvChannels[pv]['Ic'] = [np.array (vals), a, b]
            elif xf+'A' in lbl:
                pvChannels[pv]['XfIa'] = [np.array (vals), a, b]
            elif xf+'B' in lbl:
                pvChannels[pv]['XfIb'] = [np.array (vals), a, b]
            elif xf+'C' in lbl:
                pvChannels[pv]['XfIc'] = [np.array (vals), a, b]
    elif 'V-branch' in lbl:
        for pv in pvnames:
            xf = xfnames[pv]
            if pv+'A' in lbl:
                pvChannels[pv]['Va'] = [np.array (vals), a, b]
            elif pv+'B' in lbl:
                pvChannels[pv]['Vb'] = [np.array (vals), a, b]
            elif pv+'C' in lbl:
                pvChannels[pv]['Vc'] = [np.array (vals), a, b]

print ('original fs =', fs, 'n =', n)
print ('writing to', outpath + '.cfg')

cp = open (outpath + '.cfg', 'w')
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
print ('{:d},{:d}'.format (int(fs), n), file=cp)
print (comtrade_dt_format(rec.start_timestamp), file=cp)
print (comtrade_dt_format(rec.trigger_timestamp), file=cp)
print ('ASCII', file=cp)
print ('1.0', file=cp)
cp.close()

dp = open (outpath + '.dat', 'w')
for j in range(n):
    line = '{:d},{:d}'.format(j+1, int(1.0e6*t[j]))
    for tok in ['Va', 'Vb', 'Vc', 'Ia', 'Ib', 'Ic', 'XfVa', 'XfVb', 'XfVc', 'XfIa', 'XfIb', 'XfIc']:
        vals = chan[tok][0]
        a = chan[tok][1]
        b = chan[tok][2]
        ival = int ((vals[j] - b) / a)
        line += ',{:d}'.format (ival)
    print (line, file=dp)
dp.close()

