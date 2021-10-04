# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: T400LSite.py
""" Plots T400L analog channels from a relay's COMTRADE file

Customized for 1-MHz data from PV site during a ground
fault that was detected from the substation, but did not
produce targets at the PV site.

Public Functions:
    :main: does the work
"""

import sys
import matplotlib.pyplot as plt
from comtrade import Comtrade
import numpy as np
import math
import json
from scipy import signal

#warm_cycles = 5
iminseq = 0.05
vminseq = 0.05

def my_decimate(x, q):
    # signal.decimate (np.array (rec.analog[i]), intq, ftype=dec_ftype, n=dec_n)
    if q == 65:  # downsampling 1 MHz signals to 256 samples per 60-Hz cycle
        return signal.decimate (signal.decimate(x, 5), 13)
    elif q <= 13:
        return signal.decimate (x, q)
    else:
        return signal.decimate (x, q, ftype='fir', n=None)

def my_angle(z, t, thresh=None):
    raw = np.angle (z, deg=True)
    raw[0:256] = 0.0
    if thresh is not None:
        mag = np.absolute (z)
        return raw * (mag >= thresh)
    return raw

def get_symmetrical_components_rms(xarms, xarad, xbrms, xbrad, xcrms, xcrad):
    a = complex (-0.5, 0.5 * math.sqrt(3))
    a2 = complex (-0.5, -0.5 * math.sqrt(3))
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

def start_plot (nrows, ncols, sTitle, bPDF = True):
    if bPDF:
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
        if nrows > 1:
            pHeight = 4.0
        else:
            pHeight = 2.5
    else:
        #png setup
        pWidth = 6.5
        pHeight = pWidth / 1.618 / (0.7 * ncols)
        pHeight = 4.25

    fig, ax = plt.subplots(nrows, ncols, sharex = 'col', figsize=(pWidth, pHeight), constrained_layout=True)
    fig.suptitle (sTitle)

    return ax

def finish_plot(png_name = None, pdf_name = None):
    if pdf_name:
      plt.savefig (pdf_name, dpi=300)
      plt.show()
    elif png_name:
      plt.savefig(png_name)
    #  plt.show()
    else:
      plt.show()

def chanplot(ax, title, t, chan, lbls):
    colors = ['k', 'r', 'b', 'g']
    phs = ['A', 'B', 'C', '0']
    ax.set_title(title)
    for i in range(len(lbls)):
        lbl = lbls[i]
        ax.plot (t, chan[lbl], label=phs[i], color=colors[i])
    ax.grid()
    if len(lbls) > 1:
        ax.legend(loc='upper right')

sel_file = 'c:/eRoom/POI\\12_21_2020, 16_09_05_634, 81_375R229, SEL-T400L,1MHz'
site = 'WhitehouseField'
event = '108'

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

# voltage and current signals
#ax = start_plot (2, 1, 'Louisa PV Site Record during C-Ground Fault Detected from Substation', True)
#chanplot (ax[0], 'Voltage',  t, chan, ['VA', 'VB', 'VC'])
#chanplot (ax[1], 'Current',  t, chan, ['IAW', 'IBW', 'ICW'])
#ax[0].set_ylabel(axLabelVoltage)
#ax[1].set_ylabel(axLabelCurrent)
#ax[1].set_xlabel ('Seconds')
#finish_plot (png_name = None, pdf_name = 'PVSiteIV.pdf')

# power signals
va = chan['VA']
vb = chan['VB']
vc = chan['VC']
ia = chan['IAW']
ib = chan['IBW']
ic = chan['ICW']
#p = va*ia + vb*ib + vc*ic
#ax = start_plot (1, 1, 'Real Power Derived from Louisa PV Site Record', True)
#ax.plot (t, 0.001 * p, label='P', color='r')
#ax.grid()
#ax.set_ylabel ('MW')
#ax.set_xlabel ('Seconds')
#finish_plot (png_name = None, pdf_name = 'PVSitePQ.pdf')

# sequence quantities
# prepare for phasor analysis
fs = rec.cfg.sample_rates[0][0]
rs = 256
q = fs / rs / 60
intq = int(q+0.5)
print ('fsample = {:.2f}, for {:d} samples per cycle, the decimation factor is {:.4f} rounded to {:d}'.format (fs, rs, q, intq))
tdec = t[::intq]
ndec = tdec.shape[0]
ccos = np.ones(rs+1)
csin = np.ones(rs+1)
for i in range(rs+1):
    arg = 2.0 * math.pi * float(i) / float(rs)
    ccos[i] = math.cos(arg)
    csin[i] = math.sin(arg)

va_dec = my_decimate (va, intq)
vb_dec = my_decimate (vb, intq)
vc_dec = my_decimate (vc, intq)
ia_dec = my_decimate (ia, intq)
ib_dec = my_decimate (ib, intq)
ic_dec = my_decimate (ic, intq)
va_cpx, va_rms, va_ang = get_phasors (va_dec, ccos, csin)
vb_cpx, vb_rms, vb_ang = get_phasors (vb_dec, ccos, csin)
vc_cpx, vc_rms, vc_ang = get_phasors (vc_dec, ccos, csin)
v0, v1, v2 = get_symmetrical_components_rms (va_rms, va_ang, vb_rms, vb_ang, vc_rms, vc_ang)
ia_cpx, ia_rms, ia_ang = get_phasors (ia_dec, ccos, csin)
ib_cpx, ib_rms, ib_ang = get_phasors (ib_dec, ccos, csin)
ic_cpx, ic_rms, ic_ang = get_phasors (ic_dec, ccos, csin)
i0, i1, i2 = get_symmetrical_components_rms (ia_rms, ia_ang, ib_rms, ib_ang, ic_rms, ic_ang)

ax = start_plot (2, 2, 'Sequence Quantities from Louisa PV Site Record', True)

ax[0,0].set_title ('Voltage Magnitudes')
ax[0,0].plot(tdec, np.absolute (v0), color='k', label='Zero')
ax[0,0].plot(tdec, np.absolute (v1), color='r', label='Pos')
ax[0,0].plot(tdec, np.absolute (v2), color='b', label='Neg')
ax[0,0].grid()
ax[0,0].set_ylabel ('kV')
ax[0,0].legend(loc='upper right')

ax[1,0].set_title ('Current Magnitudes')
ax[1,0].plot(tdec, np.absolute (i0), color='k', label='Zero')
ax[1,0].plot(tdec, np.absolute (i1), color='r', label='Pos')
ax[1,0].plot(tdec, np.absolute (i2), color='b', label='Neg')
ax[1,0].grid()
ax[1,0].set_ylabel ('A')
ax[1,0].legend(loc='upper right')

ax[0,1].set_title ('Voltage Angles')
ax[0,1].plot(tdec, my_angle (v0, tdec, 1.0), color='k', label='Zero')
ax[0,1].plot(tdec, my_angle (v1, tdec, 1.0), color='r', label='Pos')
ax[0,1].plot(tdec, my_angle (v2, tdec, 1.0), color='b', label='Neg')
ax[0,1].grid()
ax[0,1].set_ylabel ('deg')
ax[0,1].legend(loc='upper right')

ax[1,1].set_title ('Current Angles')
ax[1,1].plot(tdec, my_angle (i0, tdec, 10.0), color='k', label='Zero')
ax[1,1].plot(tdec, my_angle (i1, tdec, 10.0), color='r', label='Pos')
ax[1,1].plot(tdec, my_angle (i2, tdec, 10.0), color='b', label='Neg')
ax[1,1].grid()
ax[1,1].set_ylabel ('deg')
ax[1,1].legend(loc='upper right')

ax[1,0].set_xlabel ('Seconds')
ax[1,1].set_xlabel ('Seconds')

finish_plot (png_name = None, pdf_name = 'PVSiteSeq.pdf')


