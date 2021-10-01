# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: T400LScan.py
""" Scan a directory of T400L COMTRADE files to look for relay functions that picked up.

Paragraph.

Public Functions:
    :main: does the work
"""

import sys
from comtrade import Comtrade
import numpy as np
import math
import operator
import glob
import json

bReportOnly = False

scan_chans = ['IA', 'IB', 'IC', 'VA', 'VB', 'VC']

# TD21P and TD21G already supervised by TD32 and OC21, so they indicate a trip
# one utility site mistakenly included TD32F and TD32R in the trip equation,
#   so TRIP signal cannot be used
scan_sigs = [
  'TD21P', # START
  'TD21G', # TRIP
  'FSAG',
  'FSBG',
  'FSCG',
  'FSAB',
  'FSBC',
  'FSCA',
  'TD32F',
  'TD32R',
  'OC21AB',
  'OC21BC',
  'OC21CA',
  'OC21AG',
  'OC21BG',
  'OC21CG']

dict = {'c:/EPBdata/SHE Substation/T400L/':'ShepherdSub',
        'c:/EPBdata/S1P16567/T400L/':'ShepherdSite1',
        'c:/EPBdata/S3P009/T400L/':'ShepherdSite2',
        'c:/eRoom/Substation/':'Louisa',
        'c:/eRoom/POI/':'WhitehouseField',
        'c:/eRoom/HFRing/':'WhitehouseField'}

def check_peaks (chan, lbl):
    v = chan[lbl]
    print ('  {:8s} {:8.2f}'.format (lbl, np.max(np.abs(v))))

def append_peak (chan, lbl):
    v = chan[lbl]
    peak = np.max(np.abs(v))
    return '{:.2f}'.format (peak)

def check_status (sig):
    smin = np.min (sig)
    smax = np.max (sig)
    if smin != smax:
        return True
#        print ('  {:8s}  changed'.format (key))
    return False

def sig_time (sig, t):
    tp = -1.0
    itp = np.argmax(sig > 0)
    if itp >= 0:
        if sig[itp] > 0:
            tp = t[itp]
    return tp

def scan_t400L (cfg_fname, dat_fname, site, eventnum, PTR, CTRW):
    rpt = ''

    rec = Comtrade()
    rec.load(cfg_fname, dat_fname)
    t = np.array(rec.time)
    trigger = str(rec.trigger_timestamp).split()
    vals = [site, trigger[0], trigger[1], eventnum]

    chan = {}
    for i in range(rec.analog_count):
        lbl = rec.analog_channel_ids[i]
        ratio = PTR
        if 'I' in lbl:
            ratio = CTRW
        if 'k' in (rec.cfg.analog_channels[i]).uu:
            ratio /= 1000.0
        ratio = 1.0
        chan[lbl] = np.array (rec.analog[i]) / ratio
    sigs = {}
    for i in range(rec.status_count):
        lbl = rec.status_channel_ids[i]
        sigs[lbl] = np.array (rec.status[i])

    dt = t[1] - t[0]
    ncy = int (1 / 60.0 / dt + 0.5)
    npt = t.size
    for lbl in scan_chans:
        vals.append (append_peak (chan, lbl))
#        check_peaks (chan, lbl)

    bTD21 = False
    for key in ['TD21G', 'TD21P']:
        if check_status (sigs[key]):
            bTD21 = True
    bOC21 = False
    for key in ['OC21AG', 'OC21BG', 'OC21CG', 'OC21AB', 'OC21BC', 'OC21CA']:
        if check_status (sigs[key]):
            bOC21 = True

    for key in scan_sigs:
        tsig = sig_time (sigs[key], t)
        if tsig >= 0.0:
            vals.append ('{:.5f}'.format(tsig))
        else:
            vals.append ('')

    if bOC21:
        rpt += 'OC21'
    if bTD21:
        rpt += ':TD21'

    if bReportOnly:
        if len(rpt) > 0:
            imax = 0.0
            for lbl in ['IA', 'IB', 'IC']:
                i = chan[lbl]
                peak = np.max(np.abs(i))
                rms = peak / math.sqrt(2.0)
                if rms > imax:
                    imax = rms
            print (','.join([site, trigger[0], trigger[1], eventnum, rpt, '{:.2f}'.format(imax)]))
    else:
        print (','.join(vals))

    return rpt

sep = ','
if bReportOnly:
    hdr = sep.join(['Site', 'Date', 'Time', 'Event', 'Targets', 'Imax'])
else:
    hdr = sep.join(['Site', 'Date', 'Time', 'Event'] + scan_chans + scan_sigs)
print (hdr)
seqnum = 1

for sel_dir, site in dict.items():
    settings_name = 'Settings{:s}.json'.format (site)
    dict = json.load(open(settings_name))
    PTR = dict['PTR']
    CTRW = dict['CTRW']

    pattern = sel_dir + '*TDR*.cfg'
    cfg_files = glob.glob (pattern)
    for cfg_fname in cfg_files:
        i1 = cfg_fname.upper().find(',TDR,')
        i2 = cfg_fname.upper().find('.CFG')
        eventnum = cfg_fname[i1+5:i2]
        dat_fname = cfg_fname [:-4] + '.dat'
        rpt = scan_t400L (cfg_fname, dat_fname, site, eventnum, PTR, CTRW)

    pattern = sel_dir + '*10kHz.cfg'
    cfg_files = glob.glob (pattern)
    for cfg_fname in cfg_files:
        rpt = scan_t400L (cfg_fname, dat_fname, site, str(seqnum), PTR, CTRW)
        seqnum += 1

