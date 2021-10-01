# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: 735scan.py
""" Writes RMS voltage, current and real power from SEL-735 COMTRADE.

Use 735trend.py to plot.

Public Functions:
    :main: does the work
"""

import sys
from comtrade import Comtrade
import numpy as np
import math
import operator
import glob

def window_rms(a, window_size):
  a2 = np.power(a,2)
  window = np.ones(window_size)/float(window_size)
  return np.sqrt(np.convolve(a2, window, 'valid'))

def scan_735 (cfg_fname, dat_fname):
    rpt = ''

    rec = Comtrade()
    rec.load(cfg_fname, dat_fname)
    t = np.array(rec.time)
    chan = {}
    for i in range(rec.analog_count):
        lbl = rec.analog_channel_ids[i]
        chan[lbl] = np.array (rec.analog[i])

    dt = t[1] - t[0]
    ncy = int (1 / 60.0 / dt + 0.5)
    npt = t.size
    varms = window_rms (chan['VA'], ncy) 
    vbrms = window_rms (chan['VB'], ncy) 
    vcrms = window_rms (chan['VC'], ncy) 
    iarms = window_rms (chan['IA'], ncy) 
    ibrms = window_rms (chan['IB'], ncy) 
    icrms = window_rms (chan['IC'], ncy) 
    ptotal = 0.001 * (chan['VA'] * chan['IA'] + chan['VB'] * chan['IB'] + chan['VC'] * chan['IC'])
    rpt = '{:s},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f},{:.2f}'.format (rec.trigger_timestamp.strftime("%m/%d/%Y, %H:%M:%S"), np.mean(ptotal),
                                                                          np.mean(varms),np.mean(vbrms),np.mean(vcrms),
                                                                          np.mean(iarms),np.mean(ibrms),np.mean(icrms))

    return rpt

#sel_dir = 'c:/EPBdata/SHE Substation/T400L/'
#sel_dir = 'c:/eRoom/Substation/'
#sel_dir = 'c:/eRoom/POI/'
sel_dir = 'c:/EPBdata/S3P009/735/'
#sel_dir = 'c:/EPBdata/S1P16567/'

pattern = sel_dir + '*.cfg'
print ('Scanning', pattern)
print ('EventNum,Date,Time,P[kW],Va,Vb,Vc,Ia,Ib,Ic')
cfg_files = glob.glob (pattern)
for cfg_fname in cfg_files:
    i1 = cfg_fname.upper().find('_')
    i2 = cfg_fname.upper().find('.CFG')
    eventnum = cfg_fname[i1+1:i2]
    dat_fname = cfg_fname [:-4] + '.dat'
    rpt = scan_735 (cfg_fname, dat_fname)
    if len(rpt) > 1:
        print ('{:s},{:s}'.format (eventnum, rpt))

