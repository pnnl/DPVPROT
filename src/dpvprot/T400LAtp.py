# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: T400L_ATP.py
""" Plots T400L channels from ATP-generated COMTRADE files

Paragraph.
for official use only

Public Functions:
    :main: description
"""

import sys
import matplotlib.pyplot as plt
from comtrade import Comtrade
import numpy as np
import math
from enum import Enum
import T400L
import json

tmin = -0.01
tmax =  0.04
tticks = [-0.01,0.00,0.01,0.02,0.03,0.04]

def aryplot(ax, title, t, yvals, lbls, clrs=None, stack_signals=False):
    nsigs = len(lbls)
    dstep = 1.25
    dtop = nsigs * dstep

    ax.set_title(title)
    for i in range(len(yvals)):
        lbl = lbls[i]
        if clrs is not None:
            clr = clrs[i]
        else:
            clr = 'C{:d}'.format(i)
        if stack_signals:
            ax.plot (t, dtop - i * dstep + yvals[i], label=lbls[i], color=clr)
        else:
            ax.plot (t, yvals[i], label=lbls[i], color=clr)
    ax.set_xlim(tmin, tmax)
    ax.set_xticks (tticks)
    ax.legend(loc='upper right')
    if stack_signals:
        ax.grid(axis='x')
        ax.get_yaxis().set_visible(False)
    else:
        ax.grid()

def tabulate_relay2 (lbl, PHASE, GROUND, t):
    tp = -1.0
    tg = -1.0
    itp = np.argmax(PHASE > 0)
    if itp >= 0:
        tp = t[itp]
    itg = np.argmax(GROUND > 0)
    if itg >= 0:
        tg = t[itg]
    print ('TD21 {:s} tp={:.4f} tg={:.4f}'.format (lbl, tp, tg))

def first_pickup_time (rly, sig):
    val = -1.0
    idx = np.argmax(sig > 0)
    if idx >= 0:
        val = rly.t[idx]
    return val

def summarize_relay (png_base, loc, tfault, rly):
    # refactoring opportunity - the next 5 lines also appear in make_plot
    TD32 = np.logical_or (np.logical_or (rly.P32FA, rly.P32FB), rly.P32FC)
    OC21P = np.logical_or (np.logical_or (rly.POCAB, rly.POCBC), rly.POCCA)
    OC21G = np.logical_or (np.logical_or (rly.POCAG, rly.POCBG), rly.POCCG)
    TD21P = np.logical_or (np.logical_or (rly.S21AB, rly.S21BC), rly.S21CA)
    TD21G = np.logical_or (np.logical_or (rly.S21AG, rly.S21BG), rly.S21CG)

    td32 = first_pickup_time (rly, TD32)
    oc21p = first_pickup_time (rly, OC21P)
    oc21g = first_pickup_time (rly, OC21G)
    td21p = first_pickup_time (rly, TD21P)
    td21g = first_pickup_time (rly, TD21G)

    print ('{:s},{:s},{:.5f},{:.5f},{:.5f},{:.5f},{:.5f},{:.5f}'.format (
        png_base, loc, tfault, td32, oc21p, oc21g, td21p, td21g))

def debug_plot (rly):
    nrows = 2
    fig, ax = plt.subplots(nrows, 1)

#    aryplot (ax[0], 'V (Sec)', rly.t, [rly.VA, rly.VB, rly.VC],
#             ['VA', 'VB', 'VC'], ['r', 'g', 'b'])
    aryplot (ax[0], 'DV (Sec)', rly.t, [rly.DVAB, rly.DVBC, rly.DVCA], 
             ['DVAB', 'DVBC', 'DVCA'], ['r', 'g', 'b'])
    aryplot (ax[1], 'DV (Sec)', rly.t, [rly.DVA, rly.DVB, rly.DVC], 
             ['DVA', 'DVB', 'DVC'], ['r', 'g', 'b'])

#    aryplot (ax[0], 'I (Sec)', rly.t, [rly.IA, rly.IB, rly.IC, rly.I0],
#            ['IA', 'IB', 'IC', 'I0'], ['r', 'g', 'b', 'm'])
#    aryplot (ax[0], 'DIZ (Sec)', rly.t, [rly.DIZAB, rly.DIZBC, rly.DIZCA], 
#             ['DIZAB', 'DIZBC', 'DIZCA'], ['r', 'g', 'b'])
#    aryplot (ax[1], 'DIZ (Sec)', rly.t, [rly.DIZA0, rly.DIZB0, rly.DIZC0, rly.DIZ0], 
#            ['DIZA0', 'DIZB0', 'DIZC0', 'DIZ0'], ['r', 'g', 'b', 'm'])
    ax[nrows-1].set_xlabel ('Seconds')
    plt.show()

def make_plot (title, png_name, rly):
    nrows = 5
    fig, ax = plt.subplots(nrows, 3, sharex = 'col', figsize=(12,1.6*nrows), constrained_layout=True)
    fig.suptitle (title)

    aryplot (ax[0, 0], 'DIZ (Sec)',  rly.t, [rly.DIZA0, rly.DIZB0, rly.DIZC0, rly.DIZ0], 
             ['DIZA', 'DIZB', 'DIZC', 'DIZ0'], ['r', 'g', 'b', 'm'])
    aryplot (ax[0, 1], 'DV (Sec)',   rly.t, [rly.DVA, rly.DVB, rly.DVC], 
             ['DVA', 'DVB', 'DVC'], ['r', 'g', 'b', 'm'])
    TD32 = np.logical_or (np.logical_or (rly.P32FA, rly.P32FB), rly.P32FC)
    OC21P = np.logical_or (np.logical_or (rly.POCAB, rly.POCBC), rly.POCCA)
    OC21G = np.logical_or (np.logical_or (rly.POCAG, rly.POCBG), rly.POCCG)
    TD21P = np.logical_or (np.logical_or (rly.S21AB, rly.S21BC), rly.S21CA)
    TD21G = np.logical_or (np.logical_or (rly.S21AG, rly.S21BG), rly.S21CG)
    aryplot (ax[0, 2], 'Pickups', rly.t, [rly.PSTART, TD32, OC21P, OC21G, TD21P, TD21G], 
             ['START', 'TD32F', 'OC21P', 'OC21G', 'TD21P', 'TD21G'], stack_signals=True)

    aryplot (ax[1,0], 'TD32 AG,AB Signals', rly.t, [rly.I32OAB, rly.I32OA, rly.I32RFAB, rly.I32RFA],
            ['Phs', 'Gnd', 'RFP', 'RFG'], ['r', 'b', 'orange', 'c'])
    aryplot (ax[1,1], 'TD32 BG,BC Signals', rly.t, [rly.I32OBC, rly.I32OB, rly.I32RFBC, rly.I32RFB],
            ['Phs', 'Gnd', 'RFP', 'RFG'], ['r', 'b', 'orange', 'c'])
    aryplot (ax[1,2], 'TD32 CG,CA Signals', rly.t, [rly.I32OCA, rly.I32OC, rly.I32RFCA, rly.I32RFC],
            ['Phs', 'Gnd', 'RFP', 'RFG'], ['r', 'b', 'orange', 'c'])

#   aryplot (ax[1,0], 'Starting V', rly.t, [rly.VSTAB, rly.VSTAG, rly.VSTARTP*np.ones(rly.npt),
#                                          rly.VSTARTG*np.ones(rly.npt)],
#           ['AB', 'AG', '', ''], ['r', 'b', 'orange', 'c'])
#   aryplot (ax[1,1], 'Starting V', rly.t, [rly.VSTBC, rly.VSTBG, rly.VSTARTP*np.ones(rly.npt),
#                                          rly.VSTARTG*np.ones(rly.npt)],
#           ['BC', 'BG', '', ''], ['r', 'b', 'orange', 'c'])
#   aryplot (ax[1,2], 'Starting V', rly.t, [rly.VSTCA, rly.VSTCG, rly.VSTARTP*np.ones(rly.npt),
#                                          rly.VSTARTG*np.ones(rly.npt)],
#           ['CA', 'CG', '', ''], ['r', 'b', 'orange', 'c'])

    aryplot (ax[2,0], 'OC21 AG,AB Signals', rly.t, [rly.IOCAB, rly.IOCAG, rly.IOCPUP, rly.IOCPUG],
            ['Phs', 'Gnd', 'RFP', 'RFG'], ['r', 'b', 'orange', 'c'])
    aryplot (ax[2,1], 'OC21 BG,BC Signals', rly.t, [rly.IOCBC, rly.IOCBG, rly.IOCPUP, rly.IOCPUG],
            ['Phs', 'Gnd', 'RFP', 'RFG'], ['r', 'b', 'orange', 'c'])
    aryplot (ax[2,2], 'OC21 CG,CA Signals', rly.t, [rly.IOCCA, rly.IOCCG, rly.IOCPUP, rly.IOCPUG],
            ['Phs', 'Gnd', 'RFP', 'RFG'], ['r', 'b', 'orange', 'c'])

    aryplot (ax[3,0], 'TD21 AB Signals', rly.t, [rly.TD21OAB, rly.TD21RAB, -rly.TD21RAB],
             ['OP', 'RT', '-RT'], ['r', 'b', 'c'])
    aryplot (ax[3,1], 'TD21 BC Signals', rly.t, [rly.TD21OBC, rly.TD21RBC, -rly.TD21RBC],
             ['OP', 'RT', '-RT'], ['r', 'b', 'c'])
    aryplot (ax[3,2], 'TD21 CA Signals', rly.t, [rly.TD21OCA, rly.TD21RCA, -rly.TD21RCA],
             ['OP', 'RT', '-RT'], ['r', 'b', 'c'])

    aryplot (ax[4,0], 'TD21 AG Signals', rly.t, [rly.TD21OAG, rly.TD21RAG, -rly.TD21RAG],
             ['OP', 'RT', '-RT'], ['r', 'b', 'c'])
    aryplot (ax[4,1], 'TD21 BG Signals', rly.t, [rly.TD21OBG, rly.TD21RBG, -rly.TD21RBG],
             ['OP', 'RT', '-RT'], ['r', 'b', 'c'])
    aryplot (ax[4,2], 'TD21 CG Signals', rly.t, [rly.TD21OCG, rly.TD21RCG, -rly.TD21RCG],
             ['OP', 'RT', '-RT'], ['r', 'b', 'c'])

    ax[nrows-1,0].set_xlabel ('Seconds')
    ax[nrows-1,1].set_xlabel ('Seconds')
    ax[nrows-1,2].set_xlabel ('Seconds')

    if len(png_name) > 0:
        plt.savefig(png_name)
    else:
        plt.show()

# python T400LATP.py Subdirectory FeederBus [Phases or CAPS] [PNG Name]
subdir = sys.argv[1]   # to match the feeder
busname = sys.argv[2]  # to match the original bus or device name
phases = sys.argv[3]   # either CAPS, ABC or A
busnum = ''
png_base = ''
case_title = ''
feeders = json.load(open('RelaySites.json'))['feeders']
faultChannels = {'Ia':-1,'Ib':-1,'Ic':-1}
feederChannels = {'Va':-1,'Vb':-1,'Vc':-1,'Ia':-1,'Ib':-1,'Ic':-1}
pvChannels = {}
pvnames = []
fdrSettings = {}
siteSettings = {}

for row in feeders:
    if subdir in row['directory']:
        fdr = row
        fdrSettings = json.load (open(fdr['SubSettings']))
        if phases == 'CAPS':
            atp_base = fdr['capdirectory'] + '/cap_' + busname
            case_title = 'Capacitor Switching {:s}-{:s}'.format (subdir, busname)
            if len(sys.argv) > 4:
                png_base = sys.argv[4]
        else:
            busnum = sys.argv[4] 
            case_title = 'Fault at {:s}-{:s} ({:s}) on phases {:s}'.format (subdir, busname, busnum, phases)
            if len(sys.argv) > 5:
                png_base = sys.argv[5]
            if len(phases) == 3:
                atp_base = fdr['directory'] + '/I3_' + busnum
            else:
                atp_base = fdr['directory'] + '/I1_' + busnum

npv = len(fdr['PV'])
suffix = 0
for i in range(npv):
    xf = fdr['XFM'][i]
    pvnames.append(xf)
    siteSettings[xf] = json.load (open(fdr['PVSettings'][i]))
    if npv > 1:
        suffix = i + 1
    pvChannels[xf] = {'XfVa':-1,'XfVb':-1,'XfVc':-1,'XfIa':-1,'XfIb':-1,'XfIc':-1,'ModelSuffix':suffix}

rec = Comtrade()
rec.load(atp_base + '.cfg', atp_base + '.dat')
t = np.array(rec.time)
n = rec.total_samples
fs = int (rec.cfg.sample_rates[0][0])  # there will be only one from ATP

for i in range(rec.analog_count):
    lbl = rec.analog_channel_ids[i]
    #    print (i, lbl)
    if 'V-node' in lbl:
        if 'FDR  A' in lbl:
            feederChannels['Va'] = np.array (rec.analog[i])
        elif 'FDR  B' in lbl:
            feederChannels['Vb'] = np.array (rec.analog[i])
        elif 'FDR  C' in lbl:
            feederChannels['Vc'] = np.array (rec.analog[i])
        else:
            for pv in pvnames:
                if pv+'A' in lbl:
                    pvChannels[pv]['XfVa'] = np.array (rec.analog[i])
                elif pv+'B' in lbl:
                    pvChannels[pv]['XfVb'] = np.array (rec.analog[i])
                elif pv+'C' in lbl:
                    pvChannels[pv]['XfVc'] = np.array (rec.analog[i])

    elif 'I-branch' in lbl:
        for pv in pvnames:
            if pv+'A' in lbl:
                pvChannels[pv]['XfIa'] = np.array (rec.analog[i])
            elif pv+'B' in lbl:
                pvChannels[pv]['XfIb'] = np.array (rec.analog[i])
            elif pv+'C' in lbl:
                pvChannels[pv]['XfIc'] = np.array (rec.analog[i])
        if 'FDR  A' in lbl:
            feederChannels['Ia'] = np.array (rec.analog[i])
        elif 'FDR  B' in lbl:
            feederChannels['Ib'] = np.array (rec.analog[i])
        elif 'FDR  C' in lbl:
            feederChannels['Ic'] = np.array (rec.analog[i])
        if 'FAULTA' in lbl:
            faultChannels['Ia'] = np.array (rec.analog[i])
        elif 'FAULTB' in lbl:
            faultChannels['Ib'] = np.array (rec.analog[i])
        elif 'FAULTC' in lbl:
            faultChannels['Ic'] = np.array (rec.analog[i])

tfault = 0.0
if phases == 'CAPS':
    v0 = np.absolute (feederChannels['Va'] + feederChannels['Vb'] + feederChannels['Vc'])
    n4 = int (n/4)
    vthresh = 1.1 * np.max (v0[0:n4])
    i = np.argmax(v0 > vthresh)
#    print ('Determine capacitor switching time from Feeder V0 n4={:d}, vthresh={:.4f}, i={:d}'.format (n4, vthresh, i))
    tfault = t[i]
else:
    ithresh = 10.0
    for i in range(n):
        if abs(faultChannels['Ia'][i]) > ithresh:
            tfault = t[i]
            break
        if abs(faultChannels['Ib'][i]) > ithresh:
            tfault = t[i]
            break
        if abs(faultChannels['Ic'][i]) > ithresh:
            tfault = t[i]
            break

if len(png_base) < 1:
    print (atp_base, pvnames, n, fs, '{:.6f}'.format(tfault))

# distance relay in the substation
title = '{:s}, Feeder'.format (case_title)
png_file = ''
if len(png_base) > 0:
    png_file = '{:s}_{:s}.png'.format (png_base, 'Feeder')
rly = T400L.T400L()
rly.update_settings (fdrSettings)
rly.load_atp (t, fs, tfault,
              feederChannels['Va'], feederChannels['Vb'], feederChannels['Vc'],
              feederChannels['Ia'], feederChannels['Ib'], feederChannels['Ic'])
if len(png_base) > 0:
    summarize_relay (png_base, 'Feeder', tfault, rly)
else:
    tabulate_relay2 ('Phase A', rly.S21AB, rly.S21AG, rly.t)
    tabulate_relay2 ('Phase B', rly.S21BC, rly.S21BG, rly.t)
    tabulate_relay2 ('Phase C', rly.S21CA, rly.S21CG, rly.t)
make_plot (title, png_file, rly)

# quit()

for pv in pvnames:
    title = '{:s}, {:s}'.format (case_title, pv)
    png_file = ''
    if len(png_base) > 0:
        png_file = '{:s}_{:s}.png'.format (png_base, pv)
    rly = T400L.T400L()
    rly.update_settings (siteSettings[pv])
    rly.load_atp (t, fs, tfault,
                  pvChannels[pv]['XfVa'], pvChannels[pv]['XfVb'], pvChannels[pv]['XfVc'],
                  pvChannels[pv]['XfIa'], pvChannels[pv]['XfIb'], pvChannels[pv]['XfIc'])
    if len(png_base) > 0:
        summarize_relay (png_base, pv, tfault, rly)
    else:
        tabulate_relay2 ('Phase A', rly.S21AB, rly.S21AG, rly.t)
        tabulate_relay2 ('Phase B', rly.S21BC, rly.S21BG, rly.t)
        tabulate_relay2 ('Phase C', rly.S21CA, rly.S21CG, rly.t)
    make_plot (title, png_file, rly)
    #debug_plot (rly)

