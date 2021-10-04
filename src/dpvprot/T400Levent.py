# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: T400Levent.py
""" Plots T400L analog channels from a relay's COMTRADE file

Paragraph.

Public Functions:
    :main: does the work
"""

import sys
import matplotlib.pyplot as plt
from comtrade import Comtrade
import numpy as np
import math
import json

def chanplot(ax, title, t, chan, lbls):
    colors = ['k', 'r', 'b', 'g']
    phs = ['A', 'B', 'C', '0']
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

sel_file = sys.argv[1]
site = sys.argv[2]
do_plot = int(sys.argv[3])
event = sys.argv[4]

settings_name = 'Settings{:s}.json'.format(site)
png_name = '{:s}_MHR_{:s}.png'.format (site, event)
dict = json.load(open(settings_name))
PTR = dict['PTR']
CTRW = dict['CTRW']

rec = Comtrade()
print (sel_file + '.cfg')
rec.load(sel_file + '.cfg', sel_file + '.dat')
print('Analog', rec.analog_count, rec.analog_channel_ids)
print('File Name', rec.filename) 
print('Station', rec.station_name)
print('N', rec.total_samples)
trigger = str(rec.trigger_timestamp)
print('Trigger', trigger)
print('PNG File', png_name)
print('PTR', PTR)
print('CTRW', CTRW)

axLabelVoltage = 'V'
axLabelCurrent = 'A'

t = np.array(rec.time)
chan = {}
for i in range(rec.analog_count):
    lbl = rec.analog_channel_ids[i]
    ratio = PTR
    if 'I' in lbl:
        ratio = CTRW
    if 'k' in (rec.cfg.analog_channels[i]).uu:
        ratio /= 1000.0
        if 'VA' in lbl:
            axLabelVoltage = 'kV'
        if 'IA' in lbl:
            axLabelCurrent = 'kA'
    ratio = 1.0
    chan[lbl] = np.array (rec.analog[i]) / ratio
sigs = {}
for i in range(rec.status_count):
    lbl = rec.status_channel_ids[i]
    sigs[lbl] = np.array (rec.status[i])

dt = t[1] - t[0]
ncy = int (1 / 60.0 / dt + 0.5)
npt = t.size
print ('{:d} points, dt={:.6f}, {:d} points per cycle'.format (npt, dt, ncy))

#quit()

nrows = 2
ncols = 1

#png setup
pWidth = 6.5
pHeight = pWidth / 1.618 / (0.7 * ncols)
pHeight = 4.25

# pdf setup
lsize = 9
if ncols > 2:
    lsize = 9
plt.rc('font', family='serif')
plt.rc('xtick', labelsize=lsize)
plt.rc('ytick', labelsize=lsize)
plt.rc('axes', labelsize=lsize)
plt.rc('legend', fontsize=lsize)
pWidth = 6.5
pHeight = pWidth / 1.618 / (0.7 * ncols)
pHeight = 4.0

fig, ax = plt.subplots(nrows, ncols, sharex = 'col', figsize=(pWidth, pHeight), constrained_layout=True)
#fig.suptitle ('Site {:s}, MHR_{:s}, Trigger {:s}'.format(site, event, trigger))
fig.suptitle ('Louisa PV Site Record during C-Ground Fault Detected from Substation')

chanplot (ax[0], 'Voltage',      t, chan, ['VA', 'VB', 'VC'])
#chanplot (ax[1], 'Current (W)',  t, chan, ['IAW', 'IBW', 'ICW'])
chanplot (ax[1], 'Current',  t, chan, ['IAW', 'IBW', 'ICW'])
ax[0].set_ylabel(axLabelVoltage)
ax[1].set_ylabel(axLabelCurrent)
ax[nrows-1].set_xlabel ('Seconds')

png_name = ''
pdf_name = 'LouisaPV.pdf'
if len(pdf_name) > 0:
  plt.savefig (pdf_name, dpi=300)
  plt.show()
elif len(png_name) > 0:
  plt.savefig(png_name)
#  plt.show()
else:
  plt.show()