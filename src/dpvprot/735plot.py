# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: 735plot.py
""" Plot voltage and current from SEL-735 COMTRADE.

Calculates RMS and kVA, too.

Public Functions:
    :main: does the work
"""

import sys
import matplotlib.pyplot as plt
from comtrade import Comtrade
import numpy as np
import math

def print_range (lbl, rms):
    print ('{:s} {:.2f} to {:.2f}'.format (lbl, np.amin(rms), np.amax(rms)))

def pwrplot (ax, title, t, ptotal):
    ax.set_title(title)
    ax.plot (t, ptotal, label='Real', color='r')
    ax.grid()
    ax.legend(loc='upper right')

def rmsplot (ax, title, t, va, vb, vc):
    colors = ['r', 'g', 'b', 'm']
    phs = ['A', 'B', 'C', 'N']
    ax.set_title(title)
    ax.plot (t, va, label='A', color='r')
    ax.plot (t, vb, label='B', color='g')
    ax.plot (t, vc, label='C', color='b')
    ax.grid()
    ax.legend(loc='upper right')

def window_rms(a, window_size):
  a2 = np.power(a,2)
  window = np.ones(window_size)/float(window_size)
  return np.sqrt(np.convolve(a2, window, 'valid'))

def chanplot(ax, title, t, chan, lbls):
    colors = ['r', 'g', 'b', 'm']
    phs = ['A', 'B', 'C', 'N']
    ax.set_title(title)
    for i in range(len(lbls)):
        lbl = lbls[i]
        ax.plot (t, chan[lbl], label=phs[i], color=colors[i])
    #ax.set_ylabel ('kA')
    ax.grid()
#    ax.set_xlim(tmin, tmax)
#    ax.set_xticks (tticks)
    if len(lbls) > 1:
        ax.legend(loc='upper right')

# PV2
sel_dir = 'c:/EPBdata/S3P009/735/'
sel_base = 'HR_10126'
# PV1
sel_dir = 'c:/EPBdata/S1P16567/'
sel_base = 'HR_10265'

sel_file = sel_dir + sel_base
png_name = ''

if len(sys.argv) > 1:
    sel_file = sys.argv[1]
if len(sys.argv) > 2:
    png_name = sys.argv[2]

rec = Comtrade()
print (sel_file + '.cfg')
rec.load(sel_file + '.cfg', sel_file + '.dat')
#print('Analog', rec.analog_count, rec.analog_channel_ids)
#print('File Name', rec.filename) 
print('Station', rec.station_name)
print('Trigger', rec.trigger_timestamp)
#print('N', rec.total_samples)

t = np.array(rec.time)
chan = {}
for i in range(rec.analog_count):
    lbl = rec.analog_channel_ids[i]
    ratio = 1.0
    chan[lbl] = np.array (rec.analog[i]) / ratio
sigs = {}
for i in range(rec.status_count):
    lbl = rec.status_channel_ids[i]
    sigs[lbl] = np.array (rec.status[i])

dt = t[1] - t[0]
ncy = int (1 / 60.0 / dt + 0.5)
npt = t.size
#print ('{:d} points, dt={:.6f}, {:d} points per cycle'.format (npt, dt, ncy))
#print ('{:d} digital channels'.format (rec.status_count))
for key, sig in sigs.items():
    if np.amax(sig) != np.amin(sig):
        print (' {:s} changed value'.format(key))

varms = window_rms (chan['VA'], ncy) 
vbrms = window_rms (chan['VB'], ncy) 
vcrms = window_rms (chan['VC'], ncy) 
iarms = window_rms (chan['IA'], ncy) 
ibrms = window_rms (chan['IB'], ncy) 
icrms = window_rms (chan['IC'], ncy) 

ptotal = 0.001 * (chan['VA'] * chan['IA'] + chan['VB'] * chan['IB'] + chan['VC'] * chan['IC'])
trms = t[ncy-1:]
print ('waveform and RMS time base lengths:', t.shape[0], trms.shape[0])

print_range ('Va rms', varms)
print_range ('Vb rms', vbrms)
print_range ('Vc rms', vcrms)
print_range ('Ia rms', iarms)
print_range ('Ib rms', ibrms)
print_range ('Ic rms', icrms)
print_range ('Real Power [kW]', ptotal)

nrows = 5
ncols = 1
fig, ax = plt.subplots(nrows, ncols, sharex = 'col', figsize=(6.5,9.0), constrained_layout=True)
fig.suptitle ('File {:s} @ {:s}'.format(sel_file, str(rec.start_timestamp)))

chanplot (ax[0], 'Voltage', t, chan, ['VA', 'VB', 'VC'])
chanplot (ax[1], 'Current', t, chan, ['IA', 'IB', 'IC', 'IN'])
rmsplot (ax[2], 'RMS Voltage', trms, varms, vbrms, vcrms)
rmsplot (ax[3], 'RMS Current', trms, iarms, ibrms, icrms)
pwrplot (ax[4], 'Power [kVA]', t, ptotal)

ax[nrows-1].set_xlabel ('Seconds')

if len(png_name) > 0:
  plt.savefig(png_name)
else:
  plt.show()