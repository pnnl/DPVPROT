# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: 735trend.py
""" Plots RMS voltage, current and real power from SEL-735 COMTRADE.

Use 735scan.py to extract the CSV data first.

Public Functions:
    :main: does the work
"""

import sys
import matplotlib.pyplot as plt
import numpy as np
import math
import csv

csv_name = 'PV1Summary.txt'
pv_name = 'S1P16567'

#csv_name = 'PV2Summary.txt'
#pv_name = 'S3P009'

png_name = ''
png_name = pv_name + '.png'
if len(sys.argv) > 1:
    png_name = sys.argv[1]

data = np.genfromtxt(csv_name, skip_header=2, delimiter=',', dtype=str)
print (csv_name, data.shape, data[0,1], data[0,2])
start_date = data[0,1]
start_time = data[0,2]
npts = data.shape[0]
kw = data[:,3].astype(np.float)
va = data[:,4].astype(np.float)
vb = data[:,5].astype(np.float)
vc = data[:,6].astype(np.float)
ia = data[:,7].astype(np.float)
ib = data[:,8].astype(np.float)
ic = data[:,9].astype(np.float)
h = np.linspace (0.0, npts-1.0, num=npts)

nrows = 3
ncols = 1
fig, ax = plt.subplots(nrows, ncols, sharex = 'col', figsize=(6.5,9.0), constrained_layout=True)
fig.suptitle ('Site {:s} Starts {:s} {:s}'.format (pv_name, start_date, start_time))

ax[0].set_title ('RMS Voltage')
ax[0].plot (h, va, label='A', color='r')
ax[0].plot (h, vb, label='B', color='g')
ax[0].plot (h, vc, label='C', color='b')
ax[0].grid()
ax[0].legend(loc='lower right')

ax[1].set_title ('RMS Current')
ax[1].plot (h, ia, label='A', color='r')
ax[1].plot (h, ib, label='B', color='g')
ax[1].plot (h, ic, label='C', color='b')
ax[1].grid()
ax[1].legend(loc='upper right')

ax[2].set_title ('Power [kVA]')
ax[2].plot (h, kw, label='Real', color='r')
ax[2].grid()
ax[2].legend(loc='lower right')

ax[nrows-1].set_xlabel ('Hours')

if len(png_name) > 0:
  plt.savefig(png_name)
else:
  plt.show()