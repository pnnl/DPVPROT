# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: T400LPeaks.py
""" Tabulate the VI peaks and signal changes from a T400L COMTRADE file.

Paragraph.

Public Functions:
    :main: does the work
"""

import sys
from comtrade import Comtrade
import numpy as np
import math

def check_peaks (chan, lbl):
    v = chan[lbl]
    print ('  {:8s} {:8.2f}'.format (lbl, np.max(np.abs(v))))

def check_status (key, sig):
    smin = np.min (sig)
    smax = np.max (sig)
    if smin != smax:
        print ('  {:8s}  changed'.format (key))

sel_dir = 'c:/EPBdata/SHE Substation/T400L/'
sel_base = '201012,130042537,0T,HE215,T400L,EPB,TDR,10035'
sel_file = sel_dir + sel_base

# TODO - get these from settings JSON file
PTR = 60.0
CTRW = 160.0

if len(sys.argv) > 1:
    sel_file = sys.argv[1]

rec = Comtrade()
print (sel_file + '.cfg')
rec.load(sel_file + '.cfg', sel_file + '.dat')
print('Analog', rec.analog_count, rec.analog_channel_ids)
print('File Name', rec.filename) 
print('Station', rec.station_name)
print('N', rec.total_samples)

t = np.array(rec.time)
chan = {}
for i in range(rec.analog_count):
    lbl = rec.analog_channel_ids[i]
    ratio = PTR
    if 'I' in lbl:
        ratio = CTRW
    if 'k' in (rec.cfg.analog_channels[i]).uu:
        ratio /= 1000.0
    chan[lbl] = np.array (rec.analog[i]) / ratio
sigs = {}
for i in range(rec.status_count):
    lbl = rec.status_channel_ids[i]
    sigs[lbl] = np.array (rec.status[i])

dt = t[1] - t[0]
ncy = int (1 / 60.0 / dt + 0.5)
npt = t.size
print ('{:d} points, dt={:.6f}, {:d} points per cycle'.format (npt, dt, ncy))

for lbl in ['IA', 'IB', 'IC', 'VA', 'VB', 'VC']:
    check_peaks (chan, lbl)

for key, sig in sigs.items():
    check_status (key, sig)

