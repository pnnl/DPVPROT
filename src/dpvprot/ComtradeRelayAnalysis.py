# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: ComtradeRelayAnalysis.py
""" Runs relay function analysis on ATP-generated COMTRADE files.

Includes UV, 46, 47 but not TD21.

Public Functions:
    :main: does the work
"""

import sys
import math
import matplotlib.pyplot as plt
from comtrade import Comtrade
import numpy as np
from scipy import signal
import json

warm_cycles = 5

def my_decimate(x, q):
    # signal.decimate (np.array (rec.analog[i]), intq, ftype=dec_ftype, n=dec_n)
    if q == 65:  # downsampling 1 MHz signals to 256 samples per 60-Hz cycle
        return signal.decimate (signal.decimate(x, 5), 13)
    elif q <= 13:
        return signal.decimate (x, q)
    else:
        return signal.decimate (x, q, ftype='fir', n=None)

iminseq = 0.05
vminseq = 0.05
def my_angle(z, thresh=None):
    raw = np.angle (z, deg=True)
    if thresh is not None:
        mag = np.absolute (z)
        return raw * (mag >= thresh)
    return raw

def find_4647_pickedup_times (i2, v2, t, tfault, q46_pu, q47_pu):
    tlast46 = -1.0
    tlast47 = -1.0
    q46 = -1.0
    q47 = -1.0
    q46_len = 0.0
    q47_len = 0.0
    for i in range(i2.shape[0]):
        if t[i] < tfault:
            continue
        if i2[i] > q46_pu:
            tlast46 = t[i] - tfault
        if v2[i] > q47_pu:
            tlast47 = t[i] - tfault
        if q46 < 0.0:
            if i2[i] > q46_pu:
                q46 = t[i] - tfault
        if q47 < 0.0:
            if v2[i] > q47_pu:
                q47 = t[i] - tfault
    if q46 >= 0.0:
        q46_len = tlast46 - q46
    if q47 >= 0.0:
        q47_len = tlast47 - q47
    return q46, q46_len, q47, q47_len

def update_undervoltage_pickup_times (v, t, tfault, t45, t60, t88):
    loc45 = -1.0
    loc60 = -1.0
    loc88 = -1.0
    for i in range(v.shape[0]):
        if t[i] < tfault:
            continue
        if v[i] < 0.88:
            if loc88 < 0.0:
                loc88 = t[i] - tfault
        else:
            loc88 = -1.0 
        if v[i] < 0.60:
            if loc60 < 0.0:
                loc60 = t[i] - tfault
        else:
            loc60 = -1.0 
        if v[i] < 0.45:
            if loc45 < 0.0:
                loc45 = t[i] - tfault
        else:
            loc45 = -1.0
#    print (loc45, loc60, loc88)
    if (t45 < 0.0) or (loc45 > 0.0 and loc45 < t45):
        t45 = loc45
    if (t60 < 0.0) or (loc60 > 0.0 and loc60 < t60):
        t60 = loc60
    if (t88 < 0.0) or (loc88 > 0.0 and loc88 < t88):
        t88 = loc88
    return t45, t60, t88

def get_phasors(v, ccos, csin):
    ndec = v.shape[0]
    rs = ccos.shape[0] - 1
    re = np.zeros (ndec)
    im = np.zeros (ndec)
    rms = np.zeros(ndec)
    ang = np.zeros(ndec)
    cpx = np.zeros(ndec, dtype=complex)
    scale = 2 / float(rs)
    dang = 2 * math.pi / float(rs)
    refang = 0
    for i in range(ndec):
        i1 = max (0, i-rs)
        wlen = min (i, rs)
        re[i] = scale * np.dot (v[i1:i], ccos[0:wlen])
        im[i] = -scale * np.dot (v[i1:i], csin[0:wlen])
        cpx.real[i] = re[i]
        cpx.imag[i] = im[i]
        rms[i] = math.sqrt(0.5 * (re[i]*re[i] + im[i]*im[i]))
        raw = math.atan2(im[i],re[i]) + math.pi
        ref = np.fmod (refang, 2 * math.pi)
        raw = raw - ref
        if raw < 0:
            raw += 2 * math.pi
        ang[i] = raw - math.pi
        refang += dang
    return cpx, rms, ang

def get_symmetrical_components(xa, xb, xc):
    a = np.complex (-0.5, 0.5 * math.sqrt(3))
    a2 = np.complex (-0.5, -0.5 * math.sqrt(3))
    s = np.add (xa, xb)
    x0 = np.add (s, xc)
    s = np.add (xa, a*xb)
    x1 = np.add (s, a2*xc)
    s = np.add (xa, a2*xb)
    x2 = np.add (s, a*xc)
    return x0/3.0, x1/3.0, x2/3.0

def get_symmetrical_components_rms(xarms, xarad, xbrms, xbrad, xcrms, xcrad):
    a = np.complex (-0.5, 0.5 * math.sqrt(3))
    a2 = np.complex (-0.5, -0.5 * math.sqrt(3))
    xa = np.multiply (xarms, np.vectorize(complex)(np.cos(xarad), np.sin(xarad)))
    xb = np.multiply (xbrms, np.vectorize(complex)(np.cos(xbrad), np.sin(xbrad)))
    xc = np.multiply (xcrms, np.vectorize(complex)(np.cos(xcrad), np.sin(xcrad)))
    s = np.add (xa, xb)
    x0 = np.add (s, xc) / 3.0
    s = np.add (xa, a*xb)
    x1 = np.add (s, a2*xc) / 3.0
    s = np.add (xa, a2*xb)
    x2 = np.add (s, a*xc) / 3.0
    return x0, x1, x2

def plot_location(loc, title, Va, Vb, Vc, Ia, Ib, Ic, vnom, inom, q46pu, q47pu, tdec, tfault, rs, ccos, csin, vthresh, png_file = ''):
    ifirstz = warm_cycles * rs
    vnom /= 1000.0
    inom /= 1000.0

    nrows = 4
    width = 8
    height = max (2*nrows, 9)
    if len(png_file) > 0:
        if height > 10.5:
            height = 10.5
    elif height > 9:
        height = 9

    fig, ax = plt.subplots(nrows, 2, sharex = 'col', figsize=(width,height), constrained_layout=True)
    fig.suptitle (title)

    ax[0,0].set_title ('Filtered Currents')
    ax[0,0].plot(tdec, 0.001 * Ia, color='r')
    ax[0,0].plot(tdec, 0.001 * Ib, color='g')
    ax[0,0].plot(tdec, 0.001 * Ic, color='b')
    ax[0,0].grid()
    ax[0,0].set_ylabel ('kA')

    ax[0,1].set_title ('Filtered Voltages')
    ax[0,1].plot(tdec, 0.001 * Va, color='r')
    ax[0,1].plot(tdec, 0.001 * Vb, color='g')
    ax[0,1].plot(tdec, 0.001 * Vc, color='b')
    ax[0,1].grid()
    ax[0,1].set_ylabel ('kV')

    ax[1,0].set_title ('Phasor Currents [RMS,Ang]')
    if inom > 0.0:
        iplotbase = inom
        ax[1,0].set_ylabel ('[PU,deg]')
    else:
        iplotbase = 1.0
        ax[1,0].set_ylabel ('[kA,deg]')
    ax2 = ax[1,0].twinx()
    iarly, iarms, iaang = get_phasors (0.001 * Ia, ccos, csin)
    ax[1,0].plot(tdec, iarms/iplotbase, color='r')
    ax2.plot(tdec, (180.0/math.pi) * iaang, color='r', linestyle='dotted', linewidth=0.75)
    ibrly, ibrms, ibang = get_phasors (0.001 * Ib, ccos, csin)
    ax[1,0].plot(tdec, ibrms/iplotbase, color='g')
    ax2.plot(tdec, (180.0/math.pi) * ibang, color='g', linestyle='dotted', linewidth=0.75)
    icrly, icrms, icang = get_phasors (0.001 * Ic, ccos, csin)
    ax[1,0].plot(tdec, icrms/iplotbase, color='b')
    ax2.plot(tdec, (180.0/math.pi) * icang, color='b', linestyle='dotted', linewidth=0.75)
    ax[1,0].grid()

    t45 = -1.0
    t60 = -1.0
    t88 = -1.0
    q46 = -1.0
    q47 = -1.0

    ax[1,1].set_title ('Phasor Voltages [RMS,Ang]')
    if (vnom > 0.0) and (inom > 0.0):
        vplotbase = vnom
        ax[1,1].set_ylabel ('[PU,deg]')
    else:
        vplotbase = 1.0
        ax[1,1].set_ylabel ('[kV,deg]')
    ax2 = ax[1,1].twinx()
    varly, varms, vaang = get_phasors (0.001 * Va, ccos, csin)
    t45, t60, t88 = update_undervoltage_pickup_times (varms/vnom, tdec, tfault, t45, t60, t88)
    ax[1,1].plot(tdec, varms/vplotbase, color='r')
    ax2.plot(tdec, (180.0/math.pi) * vaang, color='r', linestyle='dotted', linewidth=0.75)
    vbrly, vbrms, vbang = get_phasors (0.001 * Vb, ccos, csin)
    t45, t60, t88 = update_undervoltage_pickup_times (vbrms/vnom, tdec, tfault, t45, t60, t88)
    ax[1,1].plot(tdec, vbrms/vplotbase, color='g')
    ax2.plot(tdec, (180.0/math.pi) * vbang, color='g', linestyle='dotted', linewidth=0.75)
    vcrly, vcrms, vcang = get_phasors (0.001 * Vc, ccos, csin)
    t45, t60, t88 = update_undervoltage_pickup_times (vcrms/vnom, tdec, tfault, t45, t60, t88)
    ax[1,1].plot(tdec, vcrms/vplotbase, color='b')
    ax2.plot(tdec, (180.0/math.pi) * vcang, color='b', linestyle='dotted', linewidth=0.75)
    ax[1,1].grid()

    tthresh_plot = [0, tdec[-1]]
    ithresh_plot = [q46pu, q46pu]
    vthresh_plot = [q47pu, q47pu]

    ax[2,0].set_title ('Sequence Currents [RMS,Ang]')
    if inom > 0.0:
        ax[2,0].set_ylabel ('[PU,deg]')
    else:
        ax[2,0].set_ylabel ('[kA,deg]')
    ax2 = ax[2,0].twinx()
    i0, i1, i2 = get_symmetrical_components_rms (iarms, iaang, ibrms, ibang, icrms, icang)
    ax[2,0].plot(tdec, np.absolute (i0)/iplotbase, color='r')
    ax[2,0].plot(tdec, np.absolute (i1)/iplotbase, color='g')
    ax[2,0].plot(tdec, np.absolute (i2)/iplotbase, color='b')
    ax2.plot(tdec, my_angle (i0, iminseq), color='r', linestyle='dotted', linewidth=0.75)
    ax2.plot(tdec, my_angle (i1, iminseq), color='g', linestyle='dotted', linewidth=0.75)
    ax2.plot(tdec, my_angle (i2, iminseq), color='b', linestyle='dotted', linewidth=0.75)
    ax[2,0].plot(tthresh_plot, ithresh_plot, color='m')
    ax[2,0].grid()

    ax[2,1].set_title ('Sequence Voltages [RMS,Ang]')
    if inom > 0.0:
        ax[2,1].set_ylabel ('[PU,deg]')
    else:
        ax[2,1].set_ylabel ('[kV,deg]')
    ax2 = ax[2,1].twinx()
    v0, v1, v2 = get_symmetrical_components_rms (varms, vaang, vbrms, vbang, vcrms, vcang)
    ax[2,1].plot(tdec, np.absolute (v0)/vplotbase, color='r')
    ax[2,1].plot(tdec, np.absolute (v1)/vplotbase, color='g')
    ax[2,1].plot(tdec, np.absolute (v2)/vplotbase, color='b')
    ax2.plot(tdec, my_angle (v0, vminseq), color='r', linestyle='dotted', linewidth=0.75)
    ax2.plot(tdec, my_angle (v1, vminseq), color='g', linestyle='dotted', linewidth=0.75)
    ax2.plot(tdec, my_angle (v2, vminseq), color='b', linestyle='dotted', linewidth=0.75)
    ax[2,1].plot(tthresh_plot, vthresh_plot, color='m')
    ax[2,1].grid()
#    print ('sequence base quantities', inom, iplotbase, vnom, vplotbase)
    q46, q46_len, q47, q47_len = find_4647_pickedup_times (np.absolute(i2)/iplotbase, np.absolute(v2)/vplotbase, 
                                                           tdec, tfault, q46pu, q47pu)

    ax[3,0].set_title ('Phase Impedances')
    ax[3,0].set_ylabel ('[Ohm,deg]')
    ax2 = ax[3,0].twinx()
    zab = (varly[ifirstz:]-vbrly[ifirstz:]) / (iarly[ifirstz:]-ibrly[ifirstz:])
    zbc = (vbrly[ifirstz:]-vcrly[ifirstz:]) / (ibrly[ifirstz:]-icrly[ifirstz:])
    zca = (vcrly[ifirstz:]-varly[ifirstz:]) / (icrly[ifirstz:]-iarly[ifirstz:])
    ax[3,0].plot(tdec[ifirstz:], np.absolute (zab), color='r')
    ax[3,0].plot(tdec[ifirstz:], np.absolute (zbc), color='g')
    ax[3,0].plot(tdec[ifirstz:], np.absolute (zca), color='b')
    ax2.plot(tdec[ifirstz:], my_angle (zab), color='r', linestyle='dotted', linewidth=0.75)
    ax2.plot(tdec[ifirstz:], my_angle (zbc), color='g', linestyle='dotted', linewidth=0.75)
    ax2.plot(tdec[ifirstz:], my_angle (zca), color='b', linestyle='dotted', linewidth=0.75)
    ax[3,0].grid()

    ax[3,1].set_title ('Ground Impedances')
    ax[3,1].set_ylabel ('[Ohm,deg]')
    ax2 = ax[3,1].twinx()
    zag = varly[ifirstz:] / iarly[ifirstz:]
    zbg = vbrly[ifirstz:] / ibrly[ifirstz:]
    zcg = vcrly[ifirstz:] / icrly[ifirstz:]
    ax[3,1].plot(tdec[ifirstz:], np.absolute (zag), color='r')
    ax[3,1].plot(tdec[ifirstz:], np.absolute (zbg), color='g')
    ax[3,1].plot(tdec[ifirstz:], np.absolute (zcg), color='b')
    ax2.plot(tdec[ifirstz:], my_angle (zag), color='r', linestyle='dotted', linewidth=0.75)
    ax2.plot(tdec[ifirstz:], my_angle (zbg), color='g', linestyle='dotted', linewidth=0.75)
    ax2.plot(tdec[ifirstz:], my_angle (zcg), color='b', linestyle='dotted', linewidth=0.75)
    ax[3,1].grid()

    ax[nrows-1,0].set_xlabel ('Seconds')
    ax[nrows-1,1].set_xlabel ('Seconds')

    if len(png_file) > 0:
        print ('{:s},{:s},{:.5f},{:.5f},{:.5f},{:.5f},{:.5f},{:.5f},{:.5f},{:.5f}'.format (
            png_file, loc, tfault, t45, t60, t88, q46, q46_len, q47, q47_len))
        plt.savefig(png_file)
    else:
        print ('Pickup times for {:s} are T45={:.4f}, T60={:.4f}, T88={:.4f}'.format (loc, t45, t60, t88))
        print ('                          Q46={:.4f} {:.4f}, Q47={:.4f} {:.4f}'.format (q46, q46_len, q47, q47_len))
        plt.show()

feeders = json.load(open('RelaySites.json'))['feeders']
faultChannels = {'Ia':-1,'Ib':-1,'Ic':-1}
feederChannels = {'Va':-1,'Vb':-1,'Vc':-1,'Ia':-1,'Ib':-1,'Ic':-1}
pvChannels = {}
pvnames = []
vnoms = {}
inoms = {}
xfnames = {}
xfvnoms = {}
xfinoms = {}
fdrNomV = 0.0
fdrNomI = 0.0
q46fdr = 1.0
q47fdr = 1.0
q46pv = {}
q47pv = {}

subdir = sys.argv[1]   # to match the feeder
busname = sys.argv[2]  # to match the original bus or device name
phases = sys.argv[3]   # either CAPS, ABC or A
busnum = ''
png_base = ''
case_title = ''

for row in feeders:
    if subdir in row['directory']:
        fdr = row
        fdrNomV = fdr['FdrKV'] * 1000.0 * math.sqrt(1/3)
        fdrNomI = fdr['FdrS'] * 1.0e6 / 3.0 / fdrNomV
        settings = json.load (open(fdr['SubSettings']))
        q46fdr = settings['q46_pu']
        q47fdr = settings['q47_pu']
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

if len(png_base) < 1:
    print (atp_base, busname, phases, fdr['PV'])

npv = len(fdr['PV'])
suffix = 0
for i in range(npv):
    pv = fdr['PV'][i]
    xf = fdr['XFM'][i]
    vnom = fdr['Vbase'][i] * math.sqrt(1/3)
    inom = fdr['Sbase'][i] / vnom / 3.0
    pvnames.append(pv)
    vnoms[pv] = vnom
    inoms[pv] = inom
    xfnames[pv] = xf
    xfvnoms[pv] = fdrNomV
    xfinoms[pv] = inom * vnom / fdrNomV
    settings = json.load (open(fdr['PVSettings'][i]))
    q46pv[pv] = settings['q46_pu']
    q47pv[pv] = settings['q47_pu']
    if npv > 1:
        suffix = i + 1
    pvChannels[pv] = {'Va':-1,'Vb':-1,'Vc':-1,'Ia':-1,'Ib':-1,'Ic':-1,
        'XfVa':-1,'XfVb':-1,'XfVc':-1,'XfIa':-1,'XfIb':-1,'XfIc':-1,
        'wp':-1,'ang':-1,'Vmag':-1,'Imag':-1,'ModelSuffix':suffix}

rec = Comtrade()
rec.load(atp_base + '.cfg', atp_base + '.dat')
t = np.array(rec.time)
n = rec.total_samples
fs = rec.cfg.sample_rates[0][0]  # there will be only one from ATP

rs = 256
q = fs / rs / 60
intq = int(q+0.5)
if len(png_base) < 1:
    print ('fsample = {:.2f}, for {:d} samples per cycle, the decimation factor is {:.4f} rounded to {:d}'.format (fs, rs, q, intq))
tdec = t[::intq]
ndec = tdec.shape[0]
ccos = np.ones(rs+1)
csin = np.ones(rs+1)
for i in range(rs+1):
    arg = 2.0 * math.pi * float(i) / float(rs)
    ccos[i] = math.cos(arg)
    csin[i] = math.sin(arg)

for i in range(rec.analog_count):
    lbl = rec.analog_channel_ids[i]
    #    print (i, lbl)
    if 'V-node' in lbl:
        if 'FDR  A' in lbl:
            feederChannels['Va'] = my_decimate (np.array (rec.analog[i]), intq)
        elif 'FDR  B' in lbl:
            feederChannels['Vb'] = my_decimate (np.array (rec.analog[i]), intq)
        elif 'FDR  C' in lbl:
            feederChannels['Vc'] = my_decimate (np.array (rec.analog[i]), intq)
        else:
            for pv in pvnames:
                xf = xfnames[pv]
                if xf+'A' in lbl:
                    pvChannels[pv]['XfVa'] = my_decimate (np.array (rec.analog[i]), intq)
                elif xf+'B' in lbl:
                    pvChannels[pv]['XfVb'] = my_decimate (np.array (rec.analog[i]), intq)
                elif xf+'C' in lbl:
                    pvChannels[pv]['XfVc'] = my_decimate (np.array (rec.analog[i]), intq)

    elif 'I-branch' in lbl:
        for pv in pvnames:
            xf = xfnames[pv]
            if pvChannels[pv]['ModelSuffix'] > 0:
                wpMatch = 'MODELS WP' + str(pvChannels[pv]['ModelSuffix'])
                angMatch = 'MODELS ANG' + str(pvChannels[pv]['ModelSuffix'])
                vMatch = 'MODELS MAG' + str(pvChannels[pv]['ModelSuffix'])
                iMatch = 'MODELS IRMS' + str(pvChannels[pv]['ModelSuffix'])
            else:
                wpMatch = 'MODELS WP'
                angMatch = 'MODELS ANG'
                vMatch = 'MODELS MAG'
                iMatch = 'MODELS IRMS1'
            if pv+'A' in lbl:
                pvChannels[pv]['Ia'] = my_decimate (np.array (rec.analog[i]), intq)
            elif pv+'B' in lbl:
                pvChannels[pv]['Ib'] = my_decimate (np.array (rec.analog[i]), intq)
            elif pv+'C' in lbl:
                pvChannels[pv]['Ic'] = my_decimate (np.array (rec.analog[i]), intq)
            elif xf+'A' in lbl:
                pvChannels[pv]['XfIa'] = my_decimate (np.array (rec.analog[i]), intq)
            elif xf+'B' in lbl:
                pvChannels[pv]['XfIb'] = my_decimate (np.array (rec.analog[i]), intq)
            elif xf+'C' in lbl:
                pvChannels[pv]['XfIc'] = my_decimate (np.array (rec.analog[i]), intq)
            elif wpMatch in lbl:
                pvChannels[pv]['wp'] = my_decimate (np.array (rec.analog[i]), intq)
            elif angMatch in lbl:
                pvChannels[pv]['ang'] = my_decimate (np.array (rec.analog[i]), intq)
            elif vMatch in lbl:
                pvChannels[pv]['Vmag'] = my_decimate (np.array (rec.analog[i]), intq)
            elif iMatch in lbl:
                pvChannels[pv]['Imag'] = my_decimate (np.array (rec.analog[i]), intq)
        if 'FDR  A' in lbl:
            feederChannels['Ia'] = my_decimate (np.array (rec.analog[i]), intq)
        elif 'FDR  B' in lbl:
            feederChannels['Ib'] = my_decimate (np.array (rec.analog[i]), intq)
        elif 'FDR  C' in lbl:
            feederChannels['Ic'] = my_decimate (np.array (rec.analog[i]), intq)
        if 'FAULTA' in lbl:
            faultChannels['Ia'] = my_decimate (np.array (rec.analog[i]), intq)
        elif 'FAULTB' in lbl:
            faultChannels['Ib'] = my_decimate (np.array (rec.analog[i]), intq)
        elif 'FAULTC' in lbl:
            faultChannels['Ic'] = my_decimate (np.array (rec.analog[i]), intq)
    elif 'V-branch' in lbl:
        for pv in pvnames:
            xf = xfnames[pv]
            if pv+'A' in lbl:
                pvChannels[pv]['Va'] = my_decimate (np.array (rec.analog[i]), intq)
            elif pv+'B' in lbl:
                pvChannels[pv]['Vb'] = my_decimate (np.array (rec.analog[i]), intq)
            elif pv+'C' in lbl:
                pvChannels[pv]['Vc'] = my_decimate (np.array (rec.analog[i]), intq)

tfault = 0.0
if phases == 'CAPS':
    v0 = np.absolute (feederChannels['Va'] + feederChannels['Vb'] + feederChannels['Vc'])
    n4 = int (ndec/4)
    vthresh = 1.1 * np.max (v0[0:n4])
    vmax = np.max(v0)
    i = np.argmax(v0 > vthresh)
#    print ('Determine capacitor switching time from Feeder V0 max={:.4f}, n4={:d}, vthresh={:.4f}, i={:d}'.format (vmax, n4, vthresh, i))
    tfault = tdec[i]
else:
    ithresh = 10.0
    for i in range(ndec):
        if abs(faultChannels['Ia'][i]) > ithresh:
            tfault = tdec[i]
            break
        if abs(faultChannels['Ib'][i]) > ithresh:
            tfault = tdec[i]
            break
        if abs(faultChannels['Ic'][i]) > ithresh:
            tfault = tdec[i]
            break

if len(png_base) < 1:
    print ('Fault on at {:.6f}'.format(tfault))

png_file = ''

title = '{:s}, Feeder'.format (case_title)
if len(png_base) > 0:
    png_file = '{:s}_{:s}.png'.format (png_base, 'Feeder')
vthresh = fdrNomV
plot_location ('Feeder', title, feederChannels['Va'], feederChannels['Vb'], feederChannels['Vc'], \
               feederChannels['Ia'], feederChannels['Ib'], feederChannels['Ic'], fdrNomV, fdrNomI, \
               q46fdr, q47fdr, \
               tdec, tfault, rs, ccos, csin, vthresh, png_file)
#quit()
for pv in pvnames:
    title = '{:s}, {:s}'.format (case_title, pv)
    if len(png_base) > 0:
        png_file = '{:s}_{:s}.png'.format (png_base, pv)
    vthresh = vnoms[pv]
    plot_location (pv, title, pvChannels[pv]['Va'], pvChannels[pv]['Vb'], pvChannels[pv]['Vc'], \
                   pvChannels[pv]['Ia'], pvChannels[pv]['Ib'], pvChannels[pv]['Ic'], vnoms[pv], inoms[pv], \
                   q46pv[pv], q47pv[pv], \
                   tdec, tfault, rs, ccos, csin, vthresh, png_file)

    title = '{:s}, {:s}'.format (case_title, xfnames[pv])
    if len(png_base) > 0:
        png_file = '{:s}_{:s}.png'.format (png_base, xfnames[pv])
    vthresh = xfvnoms[pv]
    plot_location (xfnames[pv], title, pvChannels[pv]['XfVa'], pvChannels[pv]['XfVb'], pvChannels[pv]['XfVc'], \
                   pvChannels[pv]['XfIa'], pvChannels[pv]['XfIb'], pvChannels[pv]['XfIc'], xfvnoms[pv], xfinoms[pv], \
                   q46pv[pv], q47pv[pv], \
                   tdec, tfault, rs, ccos, csin, vthresh, png_file)
