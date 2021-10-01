# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: IncrementalRelayAnalysis.py
""" Older T400L plotting and analysis on ATP-generated COMTRADE files.

Paragraph.

Public Functions:
    :main: does the work
"""

import sys
import math
import matplotlib.pyplot as plt
from comtrade import Comtrade
import numpy as np
from scipy import signal

td21_cycles = 1
td21_m = 0.85
td21_k = 1.05
warm_cycles = 5

def find_td21_pickedup_times (Da, Db, Dc, vthresh, t, tfault):
    tlast = -1.0
    td21t = -1.0
    td21_len = 0.0
    for i in range(Da.shape[0]):
        if t[i] < tfault:
            continue
        if (Da[i] > vthresh) or (Db[i] > vthresh) or (Dc[i] > vthresh):
            tlast = t[i] - tfault
        if td21t < 0.0:
            if (Da[i] > vthresh) or (Db[i] > vthresh) or (Dc[i] > vthresh):
                td21t = t[i] - tfault
    if td21t >= 0.0:
        td21_len = tlast - td21t
    return td21t, td21_len

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

def get_incremental(x, lookback):
    n = x.shape[0] - lookback
    d = np.zeros (n)
    for i in range(n):
        d[i] = x[i+lookback] - x[i]
    return d

def get_restraint(x, lookback):
    n = x.shape[0] - lookback
    d = np.zeros (n)
    for i in range(n):
        d[i] = x[i]
    return d

def running_mean(x, N):
    cumsum = np.cumsum(np.insert(x, 0, 0)) 
    return (cumsum[N:] - cumsum[:-N]) / float(N)

def set_plot_options (ax, ylabel, xticks):
    ax.grid()
    ax.set_ylabel (ylabel)
    ax.set_xticks(xticks)
    ax.set_xlim(xticks[0], xticks[-1])

def plot_location(loc, title, Va, Vb, Vc, Ia, Ib, Ic, vnom, inom, tdec, tfault, rs, ccos, csin, ZL, vthresh, png_file = ''):
    mZL = td21_m * ZL
    vthresh = vthresh * td21_k / 1000.0
    vnom /= 1000.0
    inom /= 1000.0

    ifirstz = warm_cycles * rs
    lookback = td21_cycles * rs
    dt = 1.0 / rs / 60.0
    tstart = tfault - 1/60
    tend = tfault + 5/60
    nstart = int(tstart / dt + 0.5)
    nend = int(tend / dt - 0.5)
    tplot = (tdec[nstart:nend] - tfault) * 60.0
    tthresh_plot = [tplot[0], tplot[-1]]
    vthresh_plot = [vthresh, vthresh]
    Nmean = 32

    print ('rs={:d} len={:d} tfault={:.5f} nstart={:d} nend={:d} lenplot={:d}'.format (rs, tdec.shape[0], tfault, nstart, nend, tplot.shape[0]))
    print ('ifirstz={:d} lookback={:d} Nmean={:d} StartOp={:d}'.format (ifirstz, lookback, Nmean, ifirstz+Nmean-1))

    nd1 = nstart-lookback
    nd2 = nend-lookback
    dIa = get_incremental (Ia, lookback)[nd1:nd2] / 1.0e3
    dIb = get_incremental (Ib, lookback)[nd1:nd2] / 1.0e3
    dIc = get_incremental (Ic, lookback)[nd1:nd2] / 1.0e3
    dVa = get_incremental (Va, lookback)[nd1:nd2] / 1.0e3
    dVb = get_incremental (Vb, lookback)[nd1:nd2] / 1.0e3
    dVc = get_incremental (Vc, lookback)[nd1:nd2] / 1.0e3
    # restraint voltage - just for one cycle after the fault
    Rag = get_restraint (Va, lookback)[nd1:nd2] / 1.0e3
    Rbg = get_restraint (Vb, lookback)[nd1:nd2] / 1.0e3
    Rcg = get_restraint (Vc, lookback)[nd1:nd2] / 1.0e3
    Rag[:rs] = 0.0
    Rag[2*rs:] = 0.0
    Rbg[:rs] = 0.0
    Rbg[2*rs:] = 0.0
    Rcg[:rs] = 0.0
    Rcg[2*rs:] = 0.0
    Rab = Rag - Rbg
    Rbc = Rbg - Rcg
    Rca = Rcg - Rag

    dVab = dVa - dVb
    dVbc = dVb - dVc
    dVca = dVc - dVa
    dIab = dIa - dIb
    dIbc = dIb - dIc
    dIca = dIc - dIa
    dV0 = (dVa + dVb + dVc) / 3.0
    dI0 = (dIa + dIb + dIc) / 3.0
    dIag = dIa - dI0
    dIbg = dIb - dI0
    dIcg = dIc - dI0

    # starting voltage signals
    dSab = np.absolute(dVab) + ZL * np.absolute(dIab)
    dSbc = np.absolute(dVbc) + ZL * np.absolute(dIbc)
    dSca = np.absolute(dVca) + ZL * np.absolute(dIca)
    dSag = np.absolute(dVa) + ZL * np.absolute(dIag)
    dSbg = np.absolute(dVb) + ZL * np.absolute(dIbg)
    dScg = np.absolute(dVc) + ZL * np.absolute(dIcg)

    Dab = running_mean (np.absolute (dVab - mZL * dIab), Nmean)
    Dbc = running_mean (np.absolute (dVbc - mZL * dIbc), Nmean)
    Dca = running_mean (np.absolute (dVca - mZL * dIca), Nmean)
    Dag = running_mean (np.absolute (dVa - mZL * dIa), Nmean)
    Dbg = running_mean (np.absolute (dVb - mZL * dIb), Nmean)
    Dcg = running_mean (np.absolute (dVc - mZL * dIc), Nmean)
    td21p, td21p_len = find_td21_pickedup_times (Dab, Dbc, Dca, vthresh, tplot[Nmean-1:]/60, 0.0)
    td21g, td21g_len = find_td21_pickedup_times (Dag, Dbg, Dcg, vthresh, tplot[Nmean-1:]/60, 0.0)

    # operating voltage
    Dab = dVab - mZL * dIab
    Dbc = dVbc - mZL * dIbc
    Dca = dVca - mZL * dIca
    Dag = dVa - mZL * dIa
    Dbg = dVb - mZL * dIb
    Dcg = dVc - mZL * dIc

    print ('dIa length={:d} Dag length={:d}'.format (dIa.shape[0], Dag.shape[0]))

    nrows = 6
    width = 8
    height = 2*nrows
    if len(png_file) > 0:
        if height > 10.5:
            height = 10.5
    elif height > 9:
        height = 9

    xticks = [-1, 0, 1, 2, 3, 4, 5]

    fig, ax = plt.subplots(nrows, 2, sharex = 'col', figsize=(width,height), constrained_layout=True)
    fig.suptitle (title)

#   ax[0,0].set_title ('Filtered Currents')
#   ax[0,0].plot(tplot, 0.001 * Ia[nstart:nend], color='r')
#   ax[0,0].plot(tplot, 0.001 * Ib[nstart:nend], color='g')
#   ax[0,0].plot(tplot, 0.001 * Ic[nstart:nend], color='b')
#   set_plot_options (ax[0,0], 'kA', xticks)
#
#   ax[0,1].set_title ('Filtered Voltages')
#   ax[0,1].plot(tplot, 0.001 * Va[nstart:nend], color='r')
#   ax[0,1].plot(tplot, 0.001 * Vb[nstart:nend], color='g')
#   ax[0,1].plot(tplot, 0.001 * Vc[nstart:nend], color='b')
#   set_plot_options (ax[0,1], 'kV', xticks)

    ax[0,0].set_title ('Incremental Currents')
    ax[0,0].plot(tplot, dIa, color='r')
    ax[0,0].plot(tplot, dIb, color='g')
    ax[0,0].plot(tplot, dIc, color='b')
    set_plot_options (ax[0,0], 'kA', xticks)

    ax[0,1].set_title ('Incremental Voltages')
    ax[0,1].plot(tplot, dVa, color='r')
    ax[0,1].plot(tplot, dVb, color='g')
    ax[0,1].plot(tplot, dVc, color='b')
    set_plot_options (ax[0,1], 'kV', xticks)

    ax[1,0].set_title ('Phase Replica Currents')
    ax[1,0].plot(tplot, dIab, color='r')
    ax[1,0].plot(tplot, dIbc, color='g')
    ax[1,0].plot(tplot, dIca, color='b')
    set_plot_options (ax[1,0], 'kA', xticks)
    ax[1,1].set_title ('Phase Replica Voltages')
    ax[1,1].plot(tplot, dVab, color='r')
    ax[1,1].plot(tplot, dVbc, color='g')
    ax[1,1].plot(tplot, dVca, color='b')
    set_plot_options (ax[1,1], 'kV', xticks)

    ax[2,0].set_title ('Ground Replica Currents')
    ax[2,0].plot(tplot, dIag, color='r')
    ax[2,0].plot(tplot, dIbg, color='g')
    ax[2,0].plot(tplot, dIcg, color='b')
    ax[2,0].plot(tplot, dI0, color='m')
    set_plot_options (ax[2,0], 'kA', xticks)
    ax[2,1].set_title ('Ground Replica Voltages')
    ax[2,1].plot(tplot, dVa, color='r')
    ax[2,1].plot(tplot, dVb, color='g')
    ax[2,1].plot(tplot, dVc, color='b')
    ax[2,1].plot(tplot, dV0, color='m')
    set_plot_options (ax[2,1], 'kV', xticks)

    ax[3,0].set_title ('Phase Start')
    ax[3,0].plot(tplot, dSab, color='r')
    ax[3,0].plot(tplot, dSbc, color='g')
    ax[3,0].plot(tplot, dSca, color='b')
    set_plot_options (ax[3,0], 'kV', xticks)
    ax[3,1].set_title ('Ground Start')
    ax[3,1].plot(tplot, dSag, color='r')
    ax[3,1].plot(tplot, dSbg, color='g')
    ax[3,1].plot(tplot, dScg, color='b')
    set_plot_options (ax[3,1], 'kV', xticks)

    ax[4,0].set_title ('Phase Restraint')
    ax[4,0].plot(tplot, Rab, color='r')
    ax[4,0].plot(tplot, Rbc, color='g')
    ax[4,0].plot(tplot, Rca, color='b')
    set_plot_options (ax[4,0], 'kV', xticks)
    ax[4,1].set_title ('Ground Restraint')
    ax[4,1].plot(tplot, Rag, color='r')
    ax[4,1].plot(tplot, Rbg, color='g')
    ax[4,1].plot(tplot, Rcg, color='b')
    set_plot_options (ax[4,1], 'kV', xticks)

    Nmean = 1
    ax[5,0].set_title ('Phase Operating')
    ax[5,0].plot(tplot[Nmean-1:], Dab, color='r')
    ax[5,0].plot(tplot[Nmean-1:], Dbc, color='g')
    ax[5,0].plot(tplot[Nmean-1:], Dca, color='b')
    ax[5,0].plot(tthresh_plot, vthresh_plot, color='m')
    set_plot_options (ax[5,0], 'kV', xticks)

    ax[5,1].set_title ('Ground Operating')
    ax[5,1].plot(tplot[Nmean-1:], Dag, color='r')
    ax[5,1].plot(tplot[Nmean-1:], Dbg, color='g')
    ax[5,1].plot(tplot[Nmean-1:], Dcg, color='b')
    ax[5,1].plot(tthresh_plot, vthresh_plot, color='m')
    set_plot_options (ax[5,1], 'kV', xticks)

    ax[nrows-1,0].set_xlabel ('Cycles')
    ax[nrows-1,1].set_xlabel ('Cycles')

    if len(png_file) > 0:
        print ('{:s},{:s},{:.5f},{:.5f},{:.5f},{:.5f},{:.5f}'.format (
            png_file, loc, tfault, td21p, td21p_len, td21g, td21g_len))
        plt.savefig(png_file)
    else:
        print ('Pickup times for {:s} are TD21P={:.4f} {:.4f}, TD21G={:.4f} {:.4f}'.format (loc, td21p, td21p_len, td21g, td21g_len))
        plt.show()


feeders = [{'directory':'c:/pl4/SHE215','FdrKV':12.47,'FdrZL':0.86,'FdrS':8.0,
            'PV':['PVONE', 'PVTWO'],'Vbase':[480.0,480.0],'Sbase':[1e6,1e6],'XFM':['PVXF1','PVXF2'],'PVZL':[2.29,2.44],
            'capdirectory':'c:/pl4/Capacitors'},
           {'directory':'c:/pl4/RIV209','FdrKV':12.47,'FdrZL':0.67,'FdrS':8.0,
            'PV':['PVPCC'],'Vbase':[480.0],'Sbase':[1e6],'XFM':['PVXFM'],'PVZL':[2.93],
            'capdirectory':'c:/pl4/Capacitors'},
           {'directory':'c:/pl4/Louisa','FdrKV':34.50,'FdrZL':3.15,'FdrS':20.0,
            'PV':['PVPCC'],'Vbase':[416.0],'Sbase':[20e6],'XFM':['PVXFM'],'PVZL':[8.28],
            'capdirectory':'c:/pl4/Capacitors'}]
faultChannels = {'Ia':-1,'Ib':-1,'Ic':-1}
feederChannels = {'Va':-1,'Vb':-1,'Vc':-1,'Ia':-1,'Ib':-1,'Ic':-1}
pvChannels = {}
pvnames = []
vnoms = {}
inoms = {}
xfnames = {}
xfvnoms = {}
xfinoms = {}
zmags = {}
fdrNomV = 0.0
fdrNomI = 0.0

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
    zmags[pv] = fdr['PVZL'][i]
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
            feederChannels['Va'] = signal.decimate (np.array (rec.analog[i]), intq)
        elif 'FDR  B' in lbl:
            feederChannels['Vb'] = signal.decimate (np.array (rec.analog[i]), intq)
        elif 'FDR  C' in lbl:
            feederChannels['Vc'] = signal.decimate (np.array (rec.analog[i]), intq)
        else:
            for pv in pvnames:
                xf = xfnames[pv]
                if xf+'A' in lbl:
                    pvChannels[pv]['XfVa'] = signal.decimate (np.array (rec.analog[i]), intq)
                elif xf+'B' in lbl:
                    pvChannels[pv]['XfVb'] = signal.decimate (np.array (rec.analog[i]), intq)
                elif xf+'C' in lbl:
                    pvChannels[pv]['XfVc'] = signal.decimate (np.array (rec.analog[i]), intq)

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
                pvChannels[pv]['Ia'] = signal.decimate (np.array (rec.analog[i]), intq)
            elif pv+'B' in lbl:
                pvChannels[pv]['Ib'] = signal.decimate (np.array (rec.analog[i]), intq)
            elif pv+'C' in lbl:
                pvChannels[pv]['Ic'] = signal.decimate (np.array (rec.analog[i]), intq)
            elif xf+'A' in lbl:
                pvChannels[pv]['XfIa'] = signal.decimate (np.array (rec.analog[i]), intq)
            elif xf+'B' in lbl:
                pvChannels[pv]['XfIb'] = signal.decimate (np.array (rec.analog[i]), intq)
            elif xf+'C' in lbl:
                pvChannels[pv]['XfIc'] = signal.decimate (np.array (rec.analog[i]), intq)
            elif wpMatch in lbl:
                pvChannels[pv]['wp'] = signal.decimate (np.array (rec.analog[i]), intq)
            elif angMatch in lbl:
                pvChannels[pv]['ang'] = signal.decimate (np.array (rec.analog[i]), intq)
            elif vMatch in lbl:
                pvChannels[pv]['Vmag'] = signal.decimate (np.array (rec.analog[i]), intq)
            elif iMatch in lbl:
                pvChannels[pv]['Imag'] = signal.decimate (np.array (rec.analog[i]), intq)
        if 'FDR  A' in lbl:
            feederChannels['Ia'] = signal.decimate (np.array (rec.analog[i]), intq)
        elif 'FDR  B' in lbl:
            feederChannels['Ib'] = signal.decimate (np.array (rec.analog[i]), intq)
        elif 'FDR  C' in lbl:
            feederChannels['Ic'] = signal.decimate (np.array (rec.analog[i]), intq)
        if 'FAULTA' in lbl:
            faultChannels['Ia'] = signal.decimate (np.array (rec.analog[i]), intq)
        elif 'FAULTB' in lbl:
            faultChannels['Ib'] = signal.decimate (np.array (rec.analog[i]), intq)
        elif 'FAULTC' in lbl:
            faultChannels['Ic'] = signal.decimate (np.array (rec.analog[i]), intq)
    elif 'V-branch' in lbl:
        for pv in pvnames:
            xf = xfnames[pv]
            if pv+'A' in lbl:
                pvChannels[pv]['Va'] = signal.decimate (np.array (rec.analog[i]), intq)
            elif pv+'B' in lbl:
                pvChannels[pv]['Vb'] = signal.decimate (np.array (rec.analog[i]), intq)
            elif pv+'C' in lbl:
                pvChannels[pv]['Vc'] = signal.decimate (np.array (rec.analog[i]), intq)

tfault = 0.0
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

title = '{:s}, Feeder TD21'.format (case_title)
if len(png_base) > 0:
    png_file = '{:s}_{:s}.png'.format (png_base, 'Feeder')
ZL = fdr['FdrZL']
vthresh = fdrNomV
plot_location ('Feeder', title, feederChannels['Va'], feederChannels['Vb'], feederChannels['Vc'], \
               feederChannels['Ia'], feederChannels['Ib'], feederChannels['Ic'], fdrNomV, fdrNomI, \
               tdec, tfault, rs, ccos, csin, ZL, vthresh, png_file)
#quit()
for pv in pvnames:
#   title = '{:s}, {:s}'.format (case_title, pv)
#   if len(png_base) > 0:
#       png_file = '{:s}_{:s}.png'.format (png_base, pv)
#   vthresh = vnoms[pv]
#   ZL = zmags[pv] * vthresh * vthresh / fdrNomV / fdrNomV # on the low side
#   plot_location (pv, title, pvChannels[pv]['Va'], pvChannels[pv]['Vb'], pvChannels[pv]['Vc'], \
#                  pvChannels[pv]['Ia'], pvChannels[pv]['Ib'], pvChannels[pv]['Ic'], vnoms[pv], inoms[pv], \
#                  tdec, tfault, rs, ccos, csin, ZL, vthresh, png_file)

    title = '{:s}, {:s} TD21'.format (case_title, xfnames[pv])
    if len(png_base) > 0:
        png_file = '{:s}_{:s}.png'.format (png_base, xfnames[pv])
    vthresh = xfvnoms[pv]
    ZL = zmags[pv]   # on the high side
    plot_location (xfnames[pv], title, pvChannels[pv]['XfVa'], pvChannels[pv]['XfVb'], pvChannels[pv]['XfVc'], \
                   pvChannels[pv]['XfIa'], pvChannels[pv]['XfIb'], pvChannels[pv]['XfIc'], xfvnoms[pv], xfinoms[pv], \
                   tdec, tfault, rs, ccos, csin, ZL, vthresh, png_file)
