# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: T400LScanMHR.py
""" Scan a directory of T400L 1-MHz COMTRADE files for peaks.

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

scan_chans = ['IAW', 'IBW', 'ICW', 'VA', 'VB', 'VC']

dict = {'c:/EPBdata/SHE Substation/T400L/':'ShepherdSub',
        'c:/EPBdata/S1P16567/T400L/':'ShepherdSite1',
        'c:/EPBdata/S3P009/T400L/':'ShepherdSite2',
        'c:/eRoom/Substation/':'Louisa',
        'c:/eRoom/POI/':'WhitehouseField',
        'c:/eRoom/HFRing/':'WhitehouseField'}

def append_peak (chan, lbl):
    v = chan[lbl]
    peak = np.max(np.abs(v))
    return '{:.2f}'.format (peak)

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

    dt = t[1] - t[0]
    ncy = int (1 / 60.0 / dt + 0.5)
    npt = t.size
    for lbl in scan_chans:
        vals.append (append_peak (chan, lbl))

    print (','.join(vals))

sep = ','
hdr = sep.join(['Site', 'Date', 'Time', 'Event'] + scan_chans)
print (hdr)
seqnum = 1

for sel_dir, site in dict.items():
    settings_name = 'Settings{:s}.json'.format (site)
    dict = json.load(open(settings_name))
    PTR = dict['PTR']
    CTRW = dict['CTRW']

    pattern = sel_dir + '*MHR*.cfg'
    cfg_files = glob.glob (pattern)
    for cfg_fname in cfg_files:
        i1 = cfg_fname.upper().find(',MHR,')
        i2 = cfg_fname.upper().find('.CFG')
        eventnum = cfg_fname[i1+5:i2]
        dat_fname = cfg_fname [:-4] + '.dat'
        rpt = scan_t400L (cfg_fname, dat_fname, site, eventnum, PTR, CTRW)

    pattern = sel_dir + '*1MHz.cfg'
    cfg_files = glob.glob (pattern)
    for cfg_fname in cfg_files:
        dat_fname = cfg_fname [:-4] + '.dat'
        rpt = scan_t400L (cfg_fname, dat_fname, site, str(seqnum), PTR, CTRW)
        seqnum += 1

