# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: T400Ldev.py
""" Represents the T400L relay data and functions, deprecated

Was refactored to T400L and other files.
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

class PlotType(Enum):
    START = 1
    DIRECTIONAL = 2
    OVERCURRENT = 3
    DISTANCE = 4

# factory default setting
VMIN=0.03                           # overcurrent minimum pickup, eq. 2.8
VSTARTP = 15.0                      # starting threshold for the 3 phase loops
VSTARTG = VSTARTP / math.sqrt(3.0)  # starting threshold for the 3 ground loops
rest_offset = 100.0                 # creates offset on TD32 restraining torque, paragraph below figure 2.9
secmarg_oc = 0.004  # security margin for OC21, figure 2.16
spu = 1.0           # used to pass spu*RPP or spu*RPG for TD21

# relay settings from Comtrade HDR files
CTRW=80
CTRX=80
PTR=300.00
VNOM=115
Z1MAG=3.72
Z1ANG=73.10
Z0MAG=2.21
Z0ANG=67.70
LL=10.00
TWLPT=55.00
XC=0.00
TP50P=0.30
TD32ZF=0.20
TD32ZR=0.20
TD21MP=0.70
TD21MG=0.65
TP67P=0.30
TP67G=0.30

# new setting scheme
TD21MP=0.5
TD21MG=0.5
Z1MAG=255.0
Z0MAG=255.0

tmin = 0.04
tmax = 0.10
tticks = [0.04,0.06,0.08,0.10]
start_thresh = 0.001

def make_td21_rt (VLOOP, ILOOP, ncy, m):
    vdel = VLOOP - m * Z1MAG * ILOOP
    vr = np.zeros (vdel.size)
    vr[ncy:] = vdel[:-ncy]
    return vr

def make_td21_trip (OP, RT, VT):
    condition_1 = np.ones(OP.size) * (np.absolute(OP) > np.absolute(RT))
    condition_2 = np.ones(OP.size) * (np.sign(OP * RT) < 0)
    condition_3 = np.ones(OP.size) * (np.absolute(OP) > np.absolute(VT))
    return np.logical_and (condition_1, np.logical_and (condition_2, condition_3))

def td21plot(ax, title, t, dvloop, diloop, vloop, iloop, ncy, thresh):
    npt = t.size
    vop = dvloop - TD21MP * Z1MAG * diloop
    vdel = vloop - TD21MP * Z1MAG * iloop
    vr = np.zeros (npt)
    vr[ncy:] = -vdel[:-ncy]
#    vt = 0.5 * (1.0 + np.sign (vop * vr)) * np.absolute (vop - vr)
    vt = np.zeros (npt)
    vmin = 1000.0
    for i in range(npt):
        avr = abs(vr[i])
        avop = abs(vop[i])
        if avr > vmin:
            if np.sign(vr[i] * vop[i]) < 0:
                if avop > avr:
                    vt[i] = avop - avr
    ax.set_title(title)
    ax.plot (t, vop, label='Vop', color='b')
#    ax.plot (t + 1/60, vdel, label='Delay', color='b')
    ax.plot (t, vr, label='Vr', color='g')
    ax.plot (t, vt, label='Vt', color='r')
    vthresh = thresh * np.ones (npt)
    ax.plot (t, vthresh, color='m')
    ax.plot (t, -vthresh, color='m')
    ax.grid()
    ax.set_xlim(tmin, tmax)
    ax.set_xticks (tticks)
    ax.legend(loc='upper right')

def startplot(ax, title, t, vpp, vpg):
    ax.set_title(title)
    ax.plot (t, vpp, label='PP', color='r')
    ax.plot (t, vpg, label='PG', color='g')
    ax.grid()
    ax.set_xlim(tmin, tmax)
    ax.set_xticks (tticks)
    ax.legend(loc='upper right')

def last_pos_idx (ary):
    return len(ary) - np.argmax(ary[::-1]) - 1

def ocplot(ax, title, t, izp, izg, lblp, lblg, pstp, pstg):
    pup = VNOM * VMIN / Z1MAG / (1.0 - TD21MP)
    pug = VNOM * VMIN / Z1MAG / (1.0 - TD21MG)
    dt = t[2] - t[1]
    ap = np.absolute(izp) * pstp
    ag = np.absolute(izg) * pstg
    intp = dt * np.cumsum (ap)
    intg = dt * np.cumsum (ag)
    ax.set_title(title)
    ax.plot (t, intp, label=lblp, color='r')
    ax.plot (t, intg, label=lblg, color='b')
    t0 = 0.0
    t1 = t[np.argmax(pstp > 0)]
    t2 = t[last_pos_idx(pstp)]
    i0 = 0
    i1 = 0
    i2 = pup * (t2 - t1)
    ax.plot ([t0,t1,t2,tmax], [i0,i1,i2,i2], color='orange')
    t0 = 0.0
    t1 = t[np.argmax(pstg > 0)]
    t2 = t[last_pos_idx(pstg)]
    i0 = 0
    i1 = 0
    i2 = pug * (t2 - t1)
    ax.plot ([t0,t1,t2,tmax], [i0,i1,i2,i2], color='c')
    ax.grid()
    ax.set_xlim(tmin, tmax)
    ax.set_xticks (tticks)
    ax.legend(loc='upper left')

def aryplot(ax, title, t, yvals, lbls, clrs=None):
    ax.set_title(title)
    for i in range(len(yvals)):
        lbl = lbls[i]
        if clrs is not None:
            clr = clrs[i]
        else:
            clr = 'C{:d}'.format(i)
        ax.plot (t, yvals[i], label=lbls[i], color=clr)
    ax.grid()
    ax.set_xlim(tmin, tmax)
    ax.set_xticks (tticks)
    ax.legend(loc='upper right')

def restplot(ax, title, t, valoop, vbloop, vcloop, ialoop, ibloop, icloop):
    ax.set_title(title)
    ax.plot (t + 1/60, valoop - TD21MP * Z1MAG * ialoop, label='A', color='r')
    ax.plot (t + 1/60, vbloop - TD21MP * Z1MAG * ibloop, label='B', color='g')
    ax.plot (t + 1/60, vcloop - TD21MP * Z1MAG * icloop, label='C', color='b')
    ax.grid()
    ax.set_xlim(tmin, tmax)
    ax.set_xticks (tticks)
    ax.legend(loc='upper right')

def operplot(ax, title, t, valoop, vbloop, vcloop, ialoop, ibloop, icloop):
    ax.set_title(title)
    ax.plot (t, valoop - TD21MP * Z1MAG * ialoop, label='A', color='r')
    ax.plot (t, vbloop - TD21MP * Z1MAG * ibloop, label='B', color='g')
    ax.plot (t, vcloop - TD21MP * Z1MAG * icloop, label='C', color='b')
    #ax.set_ylabel ('kA')
    ax.grid()
    ax.set_xlim(tmin, tmax)
    ax.set_xticks (tticks)
    ax.legend(loc='upper right')

def chanplot(ax, title, t, chan, lbls):
    colors = ['r', 'g', 'b', 'm']
    phs = ['A', 'B', 'C', '0']
    ax.set_title(title)
    for i in range(len(lbls)):
        lbl = lbls[i]
        ax.plot (t, chan[lbl], label=phs[i], color=colors[i])
    #ax.set_ylabel ('kA')
    ax.grid()
    ax.set_xlim(tmin, tmax)
    ax.set_xticks (tticks)
    if len(lbls) > 1:
        ax.legend(loc='upper right')

def sigplot(ax, title, t, sigs, lbls, sums=None):
#    colors = ['r', 'g', 'b', 'm', 'c', 'k', 'orange', 'y']
#    phs = ['CA', 'BC', 'AB', 'CG', 'BG', 'AG']
    nsigs = len(lbls)
    dstep = 1.25
    dtop = nsigs * dstep
    ax.set_title (title)
    for i in range(len(lbls)):
        lbl = lbls[i]
        ax.plot (t, dtop - i * dstep + sigs[lbl], label=lbl, color='C{:d}'.format(i))  #colors[i])
#   if sums is not None:
#       sum = np.zeros (t.shape[0])
#       for i in range(len(phs)):
#           lbl = sums[0] + phs[i]
#           sum = np.maximum (sum, sigs[lbl])
#       ax.plot (t, len(lbls) + sum, label=sums[0] + 'any', color = 'k')
    ax.grid(axis='x')
    ax.get_yaxis().set_visible(False)
    ax.set_xlim(tmin, tmax)
    ax.set_xticks (tticks)
    ax.legend(loc='upper right')

#def tabulate_starting (lbl, VS, FS, t):
#    idx = np.argmax(FS > 0.0)
#    jdx = np.argmax(VS > VSTART)
#    tf = t[idx]
#    tj = t[jdx]
#    v = VS[idx]
#    print ('{:s} starting time {:.4f}s at {:.4f} V; {:.4f}s at {:.4f}'.format (lbl, tf, v, tj, VSTART))

def tabulate_relay (lbl, OPP, OPG, RPP, RPG, OCP, OCG, IOP, IOG, t):
    tp = -1.0
    tg = -1.0
    tsp = -1.0
    tsg = -1.0
    ypp = np.absolute (OPP * OCP)
    ypg = np.absolute (OPG * OCG)
    thpp = np.max(np.absolute(RPP))
    thpg = np.max(np.absolute(RPG))
    mp = np.max(ypp) / thpp
    mg = np.max(ypg) / thpg
    itp = np.argmax(ypp > thpp)
    if itp >= 0:
        tp = t[itp]
    itg = np.argmax(ypg > thpg)
    if itg >= 0:
        tg = t[itg]
    itp = np.argmax(IOP > start_thresh)
    if itp >= 0:
        tsp = t[itp]
    itg = np.argmax(IOG > start_thresh)
    if itg >= 0:
        tsg = t[itg]
    print ('TD21 {:s} mp={:.4f} tp={:.4f} mg={:.4f} tg={:.4f} tsp={:.4f} tsg={:.4f}'.format (lbl, mp, tp, mg, tg, tsp, tsg))

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

def supervise_21_trip (P21, P32, POC):
    return np.logical_and (P21, np.logical_and (P32, POC))

sel_base = sys.argv[1]
png_name = ''
do_plot = PlotType.START
if len(sys.argv) > 2:
    do_plot = PlotType(int(sys.argv[2]))
if len(sys.argv) > 3:
    png_name = sys.argv[3]

rec = Comtrade()
#print (sel_base + '.cfg')
rec.load(sel_base + '.cfg', sel_base + '.dat')
#print('Analog', rec.analog_count, rec.analog_channel_ids)
#print('File Name', rec.filename) 
#print('Station', rec.station_name)
#print('N', rec.total_samples)

t = np.array(rec.time)
chan = {}
for i in range(rec.analog_count):
    lbl = rec.analog_channel_ids[i]
    ratio = PTR
    if 'I' in lbl:
        ratio = CTRW
    if 'k' in (rec.cfg.analog_channels[i]).uu:
        ratio /= 1000.0
    chan[lbl] = np.array (rec.analog[i]) / ratio
sigs = {}
for i in range(rec.status_count):
    lbl = rec.status_channel_ids[i]
    sigs[lbl] = np.array (rec.status[i])

dt = t[1] - t[0]
ncy = int (1 / 60.0 / dt + 0.5)
npt = t.size
#print ('{:d} points, dt={:.6f}, {:d} points per cycle'.format (npt, dt, ncy))

#quit()

#chanplot (ax[0, 0], 'I',    t, chan, ['IA', 'IB', 'IC'])
#chanplot (ax[0, 1], 'V',    t, chan, ['VA', 'VB', 'VC'])
#chanplot (ax[2, 0], 'FREQ', t, chan, ['FREQ'])
#operplot (ax[1,0], 'Vop Phase', t, chan['DVA']-chan['DVB'], chan['DVB']-chan['DVC'], chan['DVC']-chan['DVA'], 
#          chan['DIZA']-chan['DIZB'], chan['DIZB']-chan['DIZC'], chan['DIZC']-chan['DIZA'])
#operplot (ax[1,1], 'Vop Ground', t, chan['DVA'], chan['DVB'], chan['DVC'], 
#          chan['DIZA']-chan['DIZ0'], chan['DIZB']-chan['DIZ0'], chan['DIZC']-chan['DIZ0'])
#restplot (ax[2,0], 'Vr Phase', t, chan['VA']-chan['VB'], chan['VB']-chan['VC'], chan['VC']-chan['VA'], 
#          chan['IA']-chan['IB'], chan['IB']-chan['IC'], chan['IC']-chan['IA'])
#sigplot (ax[4, 0], 'Arming', t, sigs, ['ABARM', 'BCARM', 'CAARM', 'AGARM', 'BGARM', 'CGARM'])
#sigplot (ax[4, 1], 'Status', t, sigs, ['TD32F', 'TD21P', 'TD21G', 'ILREMI', 'VILEMI'], ['OC21'])
#sigplot (ax[3, 0], 'Pickups', t, sigs, ['TD21P', 'TD21G', 'TD32F', 'TD32R'])
#sigplot (ax[3, 1], 'Overcurrent Supervision', t, sigs, ['OC21AB', 'OC21BC', 'OC21CA', 'OC21AG', 'OC21BG', 'OC21CG'])
#sigplot (ax[4, 0], 'Tripping Loops', t, sigs, ['TD21AB', 'TD21BC', 'TD21CA', 'TD21AG', 'TD21BG', 'TD21CG'])
#sigplot (ax[4, 1], 'Fault Identification', t, sigs, ['ABFLT', 'BCFLT', 'CAFLT', 'AGFLT', 'BGFLT', 'CGFLT'])

# restrain thresholds
RPP = VNOM * math.sqrt(2.0) * np.ones(npt)
RPG = VNOM * math.sqrt(2.0/3.0) * np.ones(npt)
# loop replica currents and voltages
DVA = chan['DVA']
DVB = chan['DVB']
DVC = chan['DVC']
VA = chan['VA']
VB = chan['VB']
VC = chan['VC']
I0 = (chan['IA'] + chan['IB'] + chan['IC']) / 3.0
IA0 = chan['IA']-I0
IB0 = chan['IB']-I0
IC0 = chan['IC']-I0
DVAB = chan['DVA']-chan['DVB']
DVBC = chan['DVB']-chan['DVC']
DVCA = chan['DVC']-chan['DVA']
VAB = chan['VA']-chan['VB']
VBC = chan['VB']-chan['VC']
VCA = chan['VC']-chan['VA']
DIZAB = chan['DIZA']-chan['DIZB']
DIZBC = chan['DIZB']-chan['DIZC']
DIZCA = chan['DIZC']-chan['DIZA']
IAB = chan['IA']-chan['IB']
IBC = chan['IB']-chan['IC']
ICA = chan['IC']-chan['IA']
DIZA0 = chan['DIZA']-chan['DIZ0']
DIZB0 = chan['DIZB']-chan['DIZ0']
DIZC0 = chan['DIZC']-chan['DIZ0']
#### Fault Start Logic
FSAG = sigs['FSAG']
FSBG = sigs['FSBG']
FSCG = sigs['FSCG']
FSAB = sigs['FSAB']
FSBC = sigs['FSBC']
FSCA = sigs['FSCA']

# predicting the starting voltages and times
VSTAG = np.absolute(DVA) + Z1MAG * np.absolute(DIZA0)
VSTBG = np.absolute(DVB) + Z1MAG * np.absolute(DIZB0)
VSTCG = np.absolute(DVC) + Z1MAG * np.absolute(DIZC0)
VSTAB = np.absolute(DVAB) + Z1MAG * np.absolute(DIZAB)
VSTBC = np.absolute(DVBC) + Z1MAG * np.absolute(DIZBC)
VSTCA = np.absolute(DVCA) + Z1MAG * np.absolute(DIZCA)
# predict the loop starting signals
PSTAG = np.ones(npt) * (VSTAG > VSTARTG)
PSTBG = np.ones(npt) * (VSTBG > VSTARTG)
PSTCG = np.ones(npt) * (VSTCG > VSTARTG)
PSTAB = np.ones(npt) * (VSTAB > VSTARTP)
PSTBC = np.ones(npt) * (VSTBC > VSTARTP)
PSTCA = np.ones(npt) * (VSTCA > VSTARTP)
# predict the overall START signal
istarts = [np.argmax(PSTAG > 0),np.argmax(PSTBG > 0),np.argmax(PSTCG > 0),np.argmax(PSTAB > 0),np.argmax(PSTBC > 0),np.argmax(PSTCA > 0)]
idx1 = min(istarts)
idx2 = idx1 + ncy
print ('START active from {:.4f}s to {:.3f}s'.format (t[idx1], t[idx2]))
PSTART = np.zeros (npt)
PSTART[idx1:idx2] = 1
# suppress the starting signals outside of the one-cycle window
PSTAG = PSTAG * PSTART
PSTBG = PSTBG * PSTART
PSTCG = PSTCG * PSTART
PSTAB = PSTAB * PSTART
PSTBC = PSTBC * PSTART
PSTCA = PSTCA * PSTART

########## TD32 Equations for SynchroWave Event, but use predicted instead of actual FSAG
########## TD32A
TD32OA=-DVA*DIZA0*PSTAG # FSAG
TD32RFA=(rest_offset + DIZA0*DIZA0*TD32ZF)*PSTART
TD32RRA=(-rest_offset - DIZA0*DIZA0*TD32ZR)*PSTART
##########  TD32B
TD32OB=-DVB*DIZB0*PSTBG # FSBG
TD32RFB=(rest_offset + DIZB0*DIZB0*TD32ZF)*PSTART
TD32RRB=(-rest_offset - DIZB0*DIZB0*TD32ZR)*PSTART
##########  TD32C
TD32OC=-DVC*DIZC0*PSTCG # FSCG
TD32RFC=(rest_offset + DIZC0*DIZC0*TD32ZF)*PSTART
TD32RRC=(-rest_offset - DIZC0*DIZC0*TD32ZR)*PSTART
##########  TD32AB
TD32OAB=-DVAB*DIZAB*PSTAB # FSAB
TD32RFAB=(rest_offset + DIZAB*DIZAB*TD32ZF)*PSTART
TD32RRAB=(-rest_offset - DIZAB*DIZAB*TD32ZR)*PSTART
##########  TD32BC
TD32OBC=-DVBC*DIZBC*PSTBC # FSBC
TD32RFBC=(rest_offset + DIZBC*DIZBC*TD32ZF)*PSTART
TD32RRBC=(-rest_offset - DIZBC*DIZBC*TD32ZR)*PSTART
##########  TD32CA
TD32OCA=-DVCA*DIZCA*PSTCA # FSCA
TD32RFCA=(rest_offset + DIZCA*DIZCA*TD32ZF)*PSTART
TD32RRCA=(-rest_offset - DIZCA*DIZCA*TD32ZR)*PSTART

##########  TD21 Equations for SynchroWave Event
##########  Operate for AG, BG, CG Loops
TD21OAG=(DVA-DIZA0*TD21MG*Z1MAG)*PSTAG # FSAG
TD21OBG=(DVB-DIZB0*TD21MG*Z1MAG)*PSTBG # FSBG
TD21OCG=(DVC-DIZC0*TD21MG*Z1MAG)*PSTCG # FSCG
##########  Operate for AB, BC, CA Loops
TD21OAB=(DVAB-DIZAB*TD21MP*Z1MAG)*PSTAB # FSAB
TD21OBC=(DVBC-DIZBC*TD21MP*Z1MAG)*PSTBC # FSBC
TD21OCA=(DVCA-DIZCA*TD21MP*Z1MAG)*PSTCA # FSCA
########## actual overcurrent supervision
OC21AG = sigs['OC21AG']
OC21BG = sigs['OC21BG']
OC21CG = sigs['OC21CG']
OC21AB = sigs['OC21AB']
OC21BC = sigs['OC21BC']
OC21CA = sigs['OC21CA']

# construct the TD21 restraint and tripping quantities
TD21RAB = make_td21_rt (VAB, IAB, ncy, TD21MP)
TD21RBC = make_td21_rt (VBC, IBC, ncy, TD21MP)
TD21RCA = make_td21_rt (VCA, ICA, ncy, TD21MP)
TD21RAG = make_td21_rt (VA, IA0, ncy, TD21MG)
TD21RBG = make_td21_rt (VB, IB0, ncy, TD21MG)
TD21RCG = make_td21_rt (VC, IC0, ncy, TD21MG)
P21AB = make_td21_trip (TD21OAB, TD21RAB, spu*RPP)
P21BC = make_td21_trip (TD21OBC, TD21RBC, spu*RPP)
P21CA = make_td21_trip (TD21OCA, TD21RCA, spu*RPP)
P21AG = make_td21_trip (TD21OAG, TD21RAG, spu*RPG)
P21BG = make_td21_trip (TD21OBG, TD21RBG, spu*RPG)
P21CG = make_td21_trip (TD21OCG, TD21RCG, spu*RPG)

# integrating the TD32 operating and restraining torques
I32OA = dt * np.cumsum (TD32OA)
I32OB = dt * np.cumsum (TD32OB)
I32OC = dt * np.cumsum (TD32OC)
I32RFA = dt * np.cumsum (TD32RFA)
I32RFB = dt * np.cumsum (TD32RFB)
I32RFC = dt * np.cumsum (TD32RFC)
I32RRA = dt * np.cumsum (TD32RRA)
I32RRB = dt * np.cumsum (TD32RRB)
I32RRC = dt * np.cumsum (TD32RRC)
I32OAB = dt * np.cumsum (TD32OAB)
I32OBC = dt * np.cumsum (TD32OBC)
I32OCA = dt * np.cumsum (TD32OCA)
I32RFAB = dt * np.cumsum (TD32RFAB)
I32RFBC = dt * np.cumsum (TD32RFBC)
I32RFCA = dt * np.cumsum (TD32RFCA)
I32RRAB = dt * np.cumsum (TD32RRAB)
I32RRBC = dt * np.cumsum (TD32RRBC)
I32RRCA = dt * np.cumsum (TD32RRCA)
# predict the directional signals
P32FAG = np.ones(npt) * (I32OA > I32RFA) * PSTART
P32FBG = np.ones(npt) * (I32OB > I32RFB) * PSTART
P32FCG = np.ones(npt) * (I32OC > I32RFC) * PSTART
P32FAB = np.ones(npt) * (I32OAB > I32RFAB) * PSTART
P32FBC = np.ones(npt) * (I32OBC > I32RFBC) * PSTART
P32FCA = np.ones(npt) * (I32OCA > I32RFCA) * PSTART
P32RAG = np.ones(npt) * (I32OA < I32RRA) * PSTART
P32RBG = np.ones(npt) * (I32OB < I32RRB) * PSTART
P32RCG = np.ones(npt) * (I32OC < I32RRC) * PSTART
P32RAB = np.ones(npt) * (I32OAB < I32RRAB) * PSTART
P32RBC = np.ones(npt) * (I32OBC < I32RRBC) * PSTART
P32RCA = np.ones(npt) * (I32OCA < I32RRCA) * PSTART
P32FA = np.logical_or (np.logical_or (P32FAG, P32FAB), P32FCA)
P32FB = np.logical_or (np.logical_or (P32FBG, P32FAB), P32FBC)
P32FC = np.logical_or (np.logical_or (P32FCG, P32FBC), P32FCA)
P32RA = np.logical_or (np.logical_or (P32RAG, P32RAB), P32RCA)
P32RB = np.logical_or (np.logical_or (P32RBG, P32RAB), P32RBC)
P32RC = np.logical_or (np.logical_or (P32RCG, P32RBC), P32RCA)

#tabulate_starting ('AG', VSTAG, FSAG, t)
#tabulate_starting ('BG', VSTBG, FSBG, t)
#tabulate_starting ('CG', VSTCG, FSCG, t)
#tabulate_starting ('AB', VSTAB, FSAB, t)
#tabulate_starting ('BC', VSTBC, FSBC, t)
#tabulate_starting ('CA', VSTCA, FSCA, t)

# integrate the overcurrent signal and pickup from PSTART
IOCAB = dt * np.cumsum(np.absolute(DIZAB)*PSTAB) #PSTART)
IOCBC = dt * np.cumsum(np.absolute(DIZBC)*PSTBC) #PSTART)
IOCCA = dt * np.cumsum(np.absolute(DIZCA)*PSTCA) #PSTART)
IOCAG = dt * np.cumsum(np.absolute(DIZA0)*PSTAG) #PSTART)
IOCBG = dt * np.cumsum(np.absolute(DIZB0)*PSTBG) #PSTART)
IOCCG = dt * np.cumsum(np.absolute(DIZC0)*PSTCG) #PSTART)
pup = VNOM*VMIN/(1-TD21MP)/Z1MAG
pug = VNOM*VMIN/(1-TD21MG)/Z1MAG/math.sqrt(3.0)
IOCPUP = dt * np.cumsum(np.ones(npt)*pup*PSTART) + secmarg_oc
IOCPUG = dt * np.cumsum(np.ones(npt)*pug*PSTART) + secmarg_oc
# predict the OC21 supervision signals
POCAB = np.ones(npt) * (IOCAB > IOCPUP) * PSTART
POCBC = np.ones(npt) * (IOCBC > IOCPUP) * PSTART
POCCA = np.ones(npt) * (IOCCA > IOCPUP) * PSTART
POCAG = np.ones(npt) * (IOCAG > IOCPUG) * PSTART
POCBG = np.ones(npt) * (IOCBG > IOCPUG) * PSTART
POCCG = np.ones(npt) * (IOCCG > IOCPUG) * PSTART

# predict the supervised TD21 trip signals
S21AB = supervise_21_trip (P21AB, P32FAB, POCAB)
S21BC = supervise_21_trip (P21BC, P32FBC, POCBC)
S21CA = supervise_21_trip (P21CA, P32FCA, POCCA)
S21AG = supervise_21_trip (P21AG, P32FAG, POCAG)
S21BG = supervise_21_trip (P21BG, P32FBG, POCBG)
S21CG = supervise_21_trip (P21CG, P32FCG, POCCG)

#tabulate_relay ('Phase A', TD21OAB, TD21OAG, RPP, RPG, OC21AB, OC21AG, IOCAB, IOCAG, t)
#tabulate_relay ('Phase B', TD21OBC, TD21OBG, RPP, RPG, OC21BC, OC21BG, IOCBC, IOCBG, t)
#tabulate_relay ('Phase C', TD21OCA, TD21OCG, RPP, RPG, OC21CA, OC21CG, IOCCA, IOCCG, t)
tabulate_relay2 ('Phase A', S21AB, S21AG, t)
tabulate_relay2 ('Phase B', S21BC, S21BG, t)
tabulate_relay2 ('Phase C', S21CA, S21CG, t)

nrows = 4
fig, ax = plt.subplots(nrows, 3, sharex = 'col', figsize=(12,2*nrows), constrained_layout=True)
fig.suptitle ('Case {:s} {:s}'.format(sel_base, do_plot.name))

if do_plot == PlotType.START:
    chanplot (ax[0, 0], 'DIZ (Sec)',  t, chan, ['DIZA', 'DIZB', 'DIZC', 'DIZ0'])
    chanplot (ax[0, 1], 'DV (Sec)',   t, chan, ['DVA', 'DVB', 'DVC'])
    sigplot (ax[0, 2], 'Triggers and Noise', t, sigs, ['START', 'EVNTPKP', 'FL', 'ILREMI', 'VILEMI'])
    aryplot (ax[1,0], 'Starting V', t, [VSTAB, VSTAG, VSTARTP*np.ones(npt), VSTARTG*np.ones(npt)], 
            ['AB', 'AG', '', ''], ['r', 'b', 'orange', 'c'])
    aryplot (ax[1,1], 'Starting V', t, [VSTBC, VSTBG, VSTARTP*np.ones(npt), VSTARTG*np.ones(npt)], 
            ['BC', 'BG', '', ''], ['r', 'b', 'orange', 'c'])
    aryplot (ax[1,2], 'Starting V', t, [VSTCA, VSTCG, VSTARTP*np.ones(npt), VSTARTG*np.ones(npt)],
            ['CA', 'CG', '', ''], ['r', 'b', 'orange', 'c'])
    aryplot (ax[2,0], 'Predicted Starting', t, [PSTAB, PSTAG + 2], ['AB', 'AG'], ['r', 'b'])
    aryplot (ax[2,1], 'Predicted Starting', t, [PSTBC, PSTBG + 2], ['BC', 'BG'], ['r', 'b'])
    aryplot (ax[2,2], 'Predicted Starting', t, [PSTCA, PSTCG + 2], ['CA', 'CG'], ['r', 'b'])
    sigplot (ax[3,0], 'Actual Starting', t, sigs, ['START', 'FS3P', 'FSAG', 'FSAB', 'AGFLT', 'ABFLT'])
    sigplot (ax[3,1], 'Actual Starting', t, sigs, ['START', 'FS3P', 'FSBG', 'FSBC', 'BGFLT', 'BCFLT'])
    sigplot (ax[3,2], 'Actual Starting', t, sigs, ['START', 'FS3P', 'FSCG', 'FSCA', 'CGFLT', 'CAFLT'])
elif do_plot == PlotType.DIRECTIONAL:
    chanplot (ax[0, 0], 'DIZ (Sec)',  t, chan, ['DIZA', 'DIZB', 'DIZC', 'DIZ0'])
    chanplot (ax[0, 1], 'DV (Sec)',   t, chan, ['DVA', 'DVB', 'DVC'])
    sigplot (ax[0, 2], 'Triggers and Noise', t, sigs, ['START', 'EVNTPKP', 'FL', 'ILREMI', 'VILEMI'])
    aryplot (ax[1,0], 'TD32 AB Signals', t, [I32OAB, I32RFAB, I32RRAB], ['OP', 'RF', 'RR'], ['r', 'b', 'g'])
    aryplot (ax[1,1], 'TD32 BC Signals', t, [I32OBC, I32RFBC, I32RRBC], ['OP', 'RF', 'RR'], ['r', 'b', 'g'])
    aryplot (ax[1,2], 'TD32 CA Signals', t, [I32OCA, I32RFCA, I32RRCA], ['OP', 'RF', 'RR'], ['r', 'b', 'g'])
    aryplot (ax[2,0], 'TD32 AG Signals', t, [I32OA, I32RFA, I32RRA], ['OP', 'RF', 'RR'], ['r', 'b', 'g'])
    aryplot (ax[2,1], 'TD32 BG Signals', t, [I32OB, I32RFB, I32RRB], ['OP', 'RF', 'RR'], ['r', 'b', 'g'])
    aryplot (ax[2,2], 'TD32 CG Signals', t, [I32OC, I32RFC, I32RRC], ['OP', 'RF', 'RR'], ['r', 'b', 'g'])
    aryplot (ax[3,0], 'TD32 Pickups', t, [P32FA + 6, P32RA + 4, sigs['TD32FA'] + 2, sigs['TD32RA']],
            ['Pred FA', 'Pred RA', 'Act FA', 'Act RA'], ['r', 'b', 'orange', 'c'])
    aryplot (ax[3,1], 'TD32 Pickups', t, [P32FB + 6, P32RB + 4, sigs['TD32FB'] + 2, sigs['TD32RB']], 
            ['Pred FB', 'Pred RB', 'Act FB', 'Act RB'], ['r', 'b', 'orange', 'c'])
    aryplot (ax[3,2], 'TD32 Pickups', t, [P32FC + 6, P32RC + 4, sigs['TD32FC'] + 2, sigs['TD32RC']], 
            ['Pred FC', 'Pred RC', 'Act FC', 'Act RC'], ['r', 'b', 'orange', 'c'])
elif do_plot == PlotType.OVERCURRENT:
    chanplot (ax[0, 0], 'DIZ (Sec)',  t, chan, ['DIZA', 'DIZB', 'DIZC', 'DIZ0'])
    chanplot (ax[0, 1], 'DV (Sec)',   t, chan, ['DVA', 'DVB', 'DVC'])
    sigplot (ax[0, 2], 'Triggers and Noise', t, sigs, ['START', 'EVNTPKP', 'FL', 'ILREMI', 'VILEMI'])
#    ocplot (ax[1,0], 'OC Supervision', t, DIZAB, DIZA0, 'AB', 'AG', PSTAB, PSTAG)
#    ocplot (ax[1,1], 'OC Supervision', t, DIZBC, DIZB0, 'BC', 'BG', PSTBC, PSTBG)
#    ocplot (ax[1,2], 'OC Supervision', t, DIZCA, DIZC0, 'CA', 'CG', PSTCA, PSTCG)
    aryplot (ax[1,0], 'OC21 AB Signals', t, [IOCAB, IOCPUP], ['I', 'PU'], ['r', 'g'])
    aryplot (ax[1,1], 'OC21 BC Signals', t, [IOCBC, IOCPUP], ['I', 'PU'], ['r', 'g'])
    aryplot (ax[1,2], 'OC21 CA Signals', t, [IOCCA, IOCPUP], ['I', 'PU'], ['r', 'g'])
    aryplot (ax[2,0], 'OC21 AG Signals', t, [IOCAG, IOCPUG], ['I', 'PU'], ['b', 'g'])
    aryplot (ax[2,1], 'OC21 BG Signals', t, [IOCBG, IOCPUG], ['I', 'PU'], ['b', 'g'])
    aryplot (ax[2,2], 'OC21 CG Signals', t, [IOCCG, IOCPUG], ['I', 'PU'], ['b', 'g'])
    aryplot (ax[3,0], 'OC21 Pickups', t, [POCAB + 6, POCAG + 4, sigs['OC21AB'] + 2, sigs['OC21AG']],
             ['Pred AB', 'Pred AG', 'Act AB', 'Act AG'], ['r', 'b', 'orange', 'c'])
    aryplot (ax[3,1], 'OC21 Pickups', t, [POCBC + 6, POCBG + 4, sigs['OC21BC'] + 2, sigs['OC21BG']],
             ['Pred BC', 'Pred BG', 'Act BC', 'Act BG'], ['r', 'b', 'orange', 'c'])
    aryplot (ax[3,2], 'OC21 Pickups', t, [POCCA + 6, POCCG + 4, sigs['OC21CA'] + 2, sigs['OC21CG']],
             ['Pred CA', 'Pred CG', 'Act CA', 'Act CG'], ['r', 'b', 'orange', 'c'])
#    sigplot (ax[3,0], 'OC21 Pickups', t, sigs, ['OC21AG', 'OC21AB'])
#    sigplot (ax[3,1], 'OC21 Pickups', t, sigs, ['OC21BG', 'OC21BC'])
#    sigplot (ax[3,2], 'OC21 Pickups', t, sigs, ['OC21CG', 'OC21CA'])
elif do_plot == PlotType.DISTANCE:
    aryplot (ax[0,0], 'TD21 AB Signals', t, [TD21OAB, TD21RAB, -TD21RAB, spu*RPP, -spu*RPP], 
             ['OP', 'RT', '-RT', 'TH', ''], ['r', 'b', 'c', 'g', 'g'])
    aryplot (ax[0,1], 'TD21 BC Signals', t, [TD21OBC, TD21RBC, -TD21RBC, spu*RPP, -spu*RPP], 
             ['OP', 'RT', '-RT', 'TH', ''], ['r', 'b', 'c', 'g', 'g'])
    aryplot (ax[0,2], 'TD21 CA Signals', t, [TD21OCA, TD21RCA, -TD21RCA, spu*RPP, -spu*RPP], 
             ['OP', 'RT', '-RT', 'TH', ''], ['r', 'b', 'c', 'g', 'g'])
    aryplot (ax[1,0], 'TD21 AG Signals', t, [TD21OAG, TD21RAG, -TD21RAG, spu*RPG, -spu*RPG], 
             ['OP', 'RT', '-RT', 'TH', ''], ['r', 'b', 'c', 'g', 'g'])
    aryplot (ax[1,1], 'TD21 BG Signals', t, [TD21OBG, TD21RBG, -TD21RBG, spu*RPG, -spu*RPG], 
             ['OP', 'RT', '-RT', 'TH', ''], ['r', 'b', 'c', 'g', 'g'])
    aryplot (ax[1,2], 'TD21 CG Signals', t, [TD21OCG, TD21RCG, -TD21RCG, spu*RPG, -spu*RPG], 
             ['OP', 'RT', '-RT', 'TH', ''], ['r', 'b', 'c', 'g', 'g'])
    aryplot (ax[2,0], 'TD21 Pickups', t, [P21AB + 6, P21AG + 4, sigs['TD21AB'] + 2, sigs['TD21AG']],
             ['Raw AB', 'Raw AG', 'Act AB', 'Act AG'], ['r', 'b', 'orange', 'c'])
    aryplot (ax[2,1], 'TD21 Pickups', t, [P21BC + 6, P21BG + 4, sigs['TD21BC'] + 2, sigs['TD21BG']],
             ['Raw BC', 'Raw BG', 'Act BC', 'Act BG'], ['r', 'b', 'orange', 'c'])
    aryplot (ax[2,2], 'TD21 Pickups', t, [P21CA + 6, P21CG + 4, sigs['TD21CA'] + 2, sigs['TD21CG']],
             ['Raw CA', 'Raw CG', 'Act CA', 'Act CG'], ['r', 'b', 'orange', 'c'])
    aryplot (ax[3,0], 'Supervised TD21 AB', t, [S21AB + 8, P32FAB + 6, POCAB + 4, sigs['TD32FA'] + 2, sigs['OC21AB']],
             ['Sup 21', 'Pred 32', 'Pred OC', 'Act 32', 'Act OC'], ['m', 'r', 'b', 'orange', 'c'])
    aryplot (ax[3,1], 'Supervised TD21 BC', t, [S21BC + 8, P32FBC + 6, POCBC + 4, sigs['TD32FB'] + 2, sigs['OC21BC']],
             ['Sup 21', 'Pred 32', 'Pred OC', 'Act 32', 'Act OC'], ['m', 'r', 'b', 'orange', 'c'])
    aryplot (ax[3,2], 'Supervised TD21 CA', t, [S21CA + 8, P32FCA + 6, POCCA + 4, sigs['TD32FC'] + 2, sigs['OC21CA']],
             ['Sup 21', 'Pred 32', 'Pred OC', 'Act 32', 'Act OC'], ['m', 'r', 'b', 'orange', 'c'])
#    td21plot (ax[1,0], 'TD21 AB Signals', t, DVAB, DIZAB, VAB, IAB, ncy, spu*RPP)
#    td21plot (ax[1,1], 'TD21 BC Signals', t, DVBC, DIZBC, VBC, IBC, ncy, spu*RPP)
#    td21plot (ax[1,2], 'TD21 CA Signals', t, DVCA, DIZCA, VCA, ICA, ncy, spu*RPP)
#    td21plot (ax[2,0], 'TD21 AG Signals', t, DVA, DIZA0, VA, IA0, ncy, spu*RPG)
#    td21plot (ax[2,1], 'TD21 BG Signals', t, DVC, DIZB0, VB, IB0, ncy, spu*RPG)
#    td21plot (ax[2,2], 'TD21 CG Signals', t, DVC, DIZC0, VC, IC0, ncy, spu*RPG)
#    sigplot (ax[3,0], 'Actual Pickups', t, sigs, ['TD21AB', 'TD21AG', 'OC21AB', 'OC21AG', 'TD32FA', 'TD32RA'])
#    sigplot (ax[3,1], 'Actual Pickups', t, sigs, ['TD21BC', 'TD21BG', 'OC21BC', 'OC21BG', 'TD32FB', 'TD32RB'])
#    sigplot (ax[3,2], 'Actual Pickups', t, sigs, ['TD21CA', 'TD21CG', 'OC21CA', 'OC21CG', 'TD32FC', 'TD32RC'])
    #aryplot (ax[1,0], 'TD21 Operating', t, [TD21OAB, TD21OAG, RPP, -RPP, RPG, -RPG], 
    #         ['AB', 'AG', '', '', '', ''], ['r', 'b', 'y', 'y', 'c', 'c'])
    #aryplot (ax[1,1], 'TD21 Operating', t, [TD21OBC, TD21OBG, RPP, -RPP, RPG, -RPG], 
    #         ['BC', 'BG', '', '', '', ''], ['r', 'b', 'y', 'y', 'c', 'c'])
    #aryplot (ax[1,2], 'TD21 Operating', t, [TD21OCA, TD21OCG, RPP, -RPP, RPG, -RPG], 
    #         ['CA', 'CG', '', '', '', ''], ['r', 'b', 'y', 'y', 'c', 'c'])


ax[nrows-1,0].set_xlabel ('Seconds')
ax[nrows-1,1].set_xlabel ('Seconds')
ax[nrows-1,2].set_xlabel ('Seconds')

if len(png_name) > 0:
  plt.savefig(png_name)
else:
  plt.show()