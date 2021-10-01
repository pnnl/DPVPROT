# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: T400Lplot.py
""" Plots T400L channels and inferred functions from a relay's COMTRADE file

python T400plot.py COMTRADEName [Settings] [PlotType] [Site Name] [Event Num]

PlotType choices:
    ALL = 0
    START = 1
    DIRECTIONAL = 2
    OVERCURRENT = 3
    DISTANCE = 4
    WAVEFORMS = 5
    IDENT = 6
    REPLICA = 7
    PDFS = 8

Public Functions:
    :main: does the work
"""

import sys
import matplotlib.pyplot as plt
from comtrade import Comtrade
import numpy as np
import math
from enum import Enum
import T400L
import json

scan_sigs = [
  'START',
  'TRIP',
  'ABFLT',
  'BCFLT',
  'CAFLT',
  'AGFLT',
  'BGFLT',
  'CGFLT',
  'TD32RA',
  'TD32RB',
  'TD32RC',
  'TD32FA',
  'TD32FB',
  'TD32FC',
  'OC21AB',
  'OC21BC',
  'OC21CA',
  'OC21AG',
  'OC21BG',
  'OC21CG',
  'TD21AB',
  'TD21BC',
  'TD21CA',
  'TD21AG',
  'TD21BG',
  'TD21CG',
  'TD21P',  # added to show the actual T400L trip decisions
  'TD21G',
  'TD32F',
  'FSAG',
  'FSBG',
  'FSCG',
  'FSAB',
  'FSBC',
  'FSCA']

def sig_time (sig, t):
    tp = -1.0
    itp = np.argmax(sig > 0)
    if itp >= 0:
        if sig[itp] > 0:
            tp = t[itp]
    return tp

class PlotType(Enum):
    ALL = 0
    START = 1
    DIRECTIONAL = 2
    OVERCURRENT = 3
    DISTANCE = 4
    WAVEFORMS = 5
    IDENT = 6
    REPLICA = 7
    PDFS = 8

def  get_png_name (png_root, do_plot):
    png_name = ''
    if len(png_root) > 0:
        if do_plot == PlotType.START:
            png_name = png_root + '_3_start.png' # these numbers order the PNG files for MS Word
        elif do_plot == PlotType.DIRECTIONAL:
            png_name = png_root + '_4_td32.png'
        elif do_plot == PlotType.OVERCURRENT:
            png_name = png_root + '_5_oc21.png'
        elif do_plot == PlotType.DISTANCE:
            png_name = png_root + '_6_td21.png'
        elif do_plot == PlotType.WAVEFORMS:
            png_name = png_root + '_1_iv.png'
        elif do_plot == PlotType.REPLICA:
            png_name = png_root + '_2_rep.png'
        elif do_plot == PlotType.IDENT:
            png_name = png_root + '_7_fid.png'
        else:
            png_name = png_root + '.png'
    return png_name

tmin = 0.04
tmax = 0.10
tticks = [0.04,0.06,0.08,0.10]

def waveplot(ax, title, t, y, clr, clip=False):
    ax.set_title (title)
    ax.plot (t, y, color=clr)
    ax.grid ()
    if clip:
        ax.set_xlim(tmin, tmax)
        ax.set_xticks (tticks)

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

def chanplot(ax, title, t, chan, lbls):
    colors = ['k', 'r', 'b', 'g']
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

def sigplot(ax, title, t, sigs, lbls):
    nsigs = len(lbls)
    dstep = 1.25
    dtop = nsigs * dstep
    ax.set_title (title)
    for i in range(len(lbls)):
        lbl = lbls[i]
        ax.plot (t, dtop - i * dstep + sigs[lbl], label=lbl, color='C{:d}'.format(i))
    ax.grid(axis='x')
    ax.get_yaxis().set_visible(False)
    ax.set_xlim(tmin, tmax)
    ax.set_xticks (tticks)
    ax.legend(loc='upper right')

def arysigplot(ax, title, t, yvals, lbls, clrs=None):
    nsigs = len(lbls)
    dstep = 1.25
    dtop = nsigs * dstep
    ax.set_title(title)
    for i in range(len(lbls)):
        lbl = lbls[i]
        if clrs is not None:
            clr = clrs[i]
        else:
            clr = 'C{:d}'.format(i)
        ax.plot (t, dtop - i * dstep + yvals[i], label=lbl, color=clr)
    ax.grid(axis='x')
    ax.set_xlim(tmin, tmax)
    ax.set_xticks (tticks)
    ax.legend(loc='upper right')

def tabulate_relay2 (lbl, PHASE, GROUND, t):
    tp = -1.0
    tg = -1.0
    itp = np.argmax(PHASE > 0)
    if itp >= 0:
        tp = t[itp]
    itg = np.argmax(GROUND > 0)
    if itg >= 0:
        tg = t[itg]
    print ('  TD21 {:s} tp={:.4f} tg={:.4f}'.format (lbl, tp, tg))

def start_png (nrows, base_title, ncols=3):
    pWidth = 12
    pHeight = 2 * nrows

    # for a half-page plot
    lsize = 8
    plt.rc('font', family='serif')
    plt.rc('xtick', labelsize=lsize)
    plt.rc('ytick', labelsize=lsize)
    plt.rc('axes', labelsize=lsize)
    plt.rc('axes', titlesize=lsize)
    plt.rc('legend', fontsize=lsize - 2)
    pWidth = 6.5
    pHeight = 4.25

    fig, ax = plt.subplots(nrows, ncols, sharex = 'col', figsize=(pWidth, pHeight), constrained_layout=True)
    fig.suptitle (base_title, fontsize=lsize+2)
    return ax

def finish_png (plt, ax, nrows, png_name, ncols=3):
    for col in range(ncols):
        ax[nrows-1,col].set_xlabel ('Seconds')
    if len(png_name) > 0:
        plt.savefig(png_name)
#        plt.show()
    else:
        plt.show()

def start_pdf (ncols):
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
    fig, ax = plt.subplots(1, ncols, figsize=(pWidth, pHeight), constrained_layout=True)
    return ax

def finish_pdf (pdf_name):
    plt.savefig (pdf_name, dpi=300)
    plt.show()

def make_pdf_waveforms (pdf_name, rly):
    ax = start_pdf (2)
    ax[0].set_title ('Primary Currents')
    ax[0].set_ylabel ('[A peak]')
    iscale = rly.CTRW
    ax[0].plot (rly.t, iscale * rly.IA0, label='A', color='red')
    ax[0].plot (rly.t, iscale * rly.IB0, label='B', color='green')
    ax[0].plot (rly.t, iscale * rly.IC0, label='C', color='blue')
#    ax[0].plot (rly.t, iscale * rly.I0, label='0', color='magenta')
    ax[1].set_title ('Primary Voltages')
    ax[1].set_ylabel ('[kV peak]')
    vscale = rly.PTR * 0.001
    ax[1].plot (rly.t, vscale * rly.VA, label='A', color='red')
    ax[1].plot (rly.t, vscale * rly.VB, label='B', color='green')
    ax[1].plot (rly.t, vscale * rly.VC, label='C', color='blue')
    tmin = 0.0
    tmax = 0.2
    xticks = [0.0,0.05,0.10,0.15,0.20]
    for i in range(2):
        ax[i].set_xlim (tmin,tmax)
        ax[i].set_xticks(xticks)
        ax[i].set_xlabel ('Time [s]')
        ax[i].grid()
        ax[i].legend(loc='lower right')
    finish_pdf (pdf_name)

def make_pdf_incremental (pdf_name, rly):
    ax = start_pdf (2)
    ax[0].set_title ('Incremental Currents')
    ax[0].set_ylabel ('[A peak]')
    ax[0].plot (rly.t, rly.DIZA0, label='A', color='red')
    ax[0].plot (rly.t, rly.DIZB0, label='B', color='green')
    ax[0].plot (rly.t, rly.DIZC0, label='C', color='blue')
    ax[1].set_title ('Incremental Voltages')
    ax[1].set_ylabel ('[V peak]')
    ax[1].plot (rly.t, rly.DVA, label='A', color='red')
    ax[1].plot (rly.t, rly.DVB, label='B', color='green')
    ax[1].plot (rly.t, rly.DVC, label='C', color='blue')
    for i in range(2):
        ax[i].set_xlim (tmin,tmax)
        ax[i].set_xticks (tticks)
        ax[i].set_xlabel ('Time [s]')
        ax[i].grid()
        ax[i].legend(loc='lower right')
    finish_pdf (pdf_name)

def make_pdf_signals (pdf_name, rly):
    ax = start_pdf (3)
    ax[0].set_title ('TD32 CG Signals')
    ax[0].plot (rly.t, rly.I32OC, label='OP', color='red')
    ax[0].plot (rly.t, rly.I32RRC, label='RR', color='green')
    ax[0].plot (rly.t, rly.I32RFC, label='RF', color='blue')

    ax[1].set_title ('OC21 CG Signals')
    ax[1].plot (rly.t, rly.IOCCG, label='I', color='red')
    ax[1].plot (rly.t, rly.IOCPUG, label='PU', color='blue')

    ax[2].set_title ('TD21 CG Signals')
    ax[2].plot (rly.t, rly.TD21OCG, label='OP', color='red')
    ax[2].plot (rly.t, rly.TD21RCG, label='RT', color='blue')
    ax[2].plot (rly.t, -rly.TD21RCG, label='-RT', color='cyan')
    ax[2].plot (rly.t, rly.spu*rly.RPG, label='TH', color='green')
    ax[2].plot (rly.t, -rly.spu*rly.RPG, label='', color='green')

    for i in range(3):
        ax[i].set_xlim (tmin,tmax)
        ax[i].set_xticks (tticks)
        ax[i].set_xlabel ('Time [s]')
        ax[i].grid()
        ax[i].legend(loc='lower right')
    ax[2].legend(loc='center right')
    finish_pdf (pdf_name)

def make_waveform_plot (base_title, png_name, rly):
    nrows = 4
    ax = start_png (nrows, base_title)
#   waveplot (ax[0,0], 'VA', rly.t, rly.VA, 'black')
#   waveplot (ax[0,1], 'VB', rly.t, rly.VB, 'red')
#   waveplot (ax[0,2], 'VC', rly.t, rly.VC, 'blue')
#   waveplot (ax[1,0], 'IA0', rly.t, rly.IA0, 'black')
#   waveplot (ax[1,1], 'IB0', rly.t, rly.IB0, 'red')
#   waveplot (ax[1,2], 'IC0', rly.t, rly.IC0, 'blue')
#   waveplot (ax[2,0], 'VAB', rly.t, rly.VAB, 'black')
#   waveplot (ax[2,1], 'VBC', rly.t, rly.VBC, 'red')
#   waveplot (ax[2,2], 'VCA', rly.t, rly.VCA, 'blue')
#   waveplot (ax[3,0], 'IAB', rly.t, rly.IAB, 'black')
#   waveplot (ax[3,1], 'IBC', rly.t, rly.IBC, 'red')
#   waveplot (ax[3,2], 'ICA', rly.t, rly.ICA, 'blue')
    waveplot (ax[0,0], 'VA', rly.t, rly.VA, 'black')
    waveplot (ax[0,1], 'VB', rly.t, rly.VB, 'red')
    waveplot (ax[0,2], 'VC', rly.t, rly.VC, 'blue')
    if rly.haveDigitalOutputs == True:
        waveplot (ax[1,0], 'IA', rly.t, rly.chan['IA'], 'gray')
        waveplot (ax[1,1], 'IB', rly.t, rly.chan['IB'], 'salmon')
        waveplot (ax[1,2], 'IC', rly.t, rly.chan['IC'], 'c')
    else:
        waveplot (ax[1,0], 'IA', rly.t, rly.IA, 'gray')  # rly.IA was decimated to match rly.t
        waveplot (ax[1,1], 'IB', rly.t, rly.IB, 'salmon')
        waveplot (ax[1,2], 'IC', rly.t, rly.IC, 'c')
    waveplot (ax[2,0], 'I0', rly.t, rly.I0, 'green')
    waveplot (ax[2,1], 'I0', rly.t, rly.I0, 'green')
    waveplot (ax[2,2], 'I0', rly.t, rly.I0, 'green')
    waveplot (ax[3,0], 'IA0', rly.t, rly.IA0, 'gray')
    waveplot (ax[3,1], 'IB0', rly.t, rly.IB0, 'salmon')
    waveplot (ax[3,2], 'IC0', rly.t, rly.IC0, 'c')
    finish_png (plt, ax, nrows, png_name)

def make_replica_plot (base_title, png_name, rly):
    nrows = 4
    ax = start_png (nrows, base_title)
    waveplot (ax[0,0], 'DVA', rly.t, rly.DVA, 'black', clip=True)
    waveplot (ax[0,1], 'DVB', rly.t, rly.DVB, 'red', clip=True)
    waveplot (ax[0,2], 'DVC', rly.t, rly.DVC, 'blue', clip=True)
    waveplot (ax[1,0], 'DIZA0', rly.t, rly.DIZA0, 'gray', clip=True)
    waveplot (ax[1,1], 'DIZB0', rly.t, rly.DIZB0, 'salmon', clip=True)
    waveplot (ax[1,2], 'DIZC0', rly.t, rly.DIZC0, 'c', clip=True)
    waveplot (ax[2,0], 'DVAB', rly.t, rly.DVAB, 'black', clip=True)
    waveplot (ax[2,1], 'DVBC', rly.t, rly.DVBC, 'red', clip=True)
    waveplot (ax[2,2], 'DVCA', rly.t, rly.DVCA, 'blue', clip=True)
    waveplot (ax[3,0], 'DIZAB', rly.t, rly.DIZAB, 'gray', clip=True)
    waveplot (ax[3,1], 'DIZBC', rly.t, rly.DIZBC, 'salmon', clip=True)
    waveplot (ax[3,2], 'DIZCA', rly.t, rly.DIZCA, 'c', clip=True)
    finish_png (plt, ax, nrows, png_name)

def make_starting_plot (base_title, png_name, rly):
#   if rly.haveDigitalOutputs == True:
#       nrows = 4
#       trig_sig_list = ['START', 'EVNTPKP', 'FL', 'ILREMI', 'VILEMI']
#   else:
#       nrows = 3
#       trig_sig_list = ['START']
    nrows = 3
    ax = start_png (nrows, base_title)
#   chanplot (ax[0, 0], 'DIZ (Sec)',  rly.t, rly.chan, ['DIZA', 'DIZB', 'DIZC', 'DIZ0'])
#   chanplot (ax[0, 1], 'DV (Sec)',   rly.t, rly.chan, ['DVA', 'DVB', 'DVC'])
#   sigplot (ax[0, 2], 'Triggers and Noise', rly.t, rly.sigs, trig_sig_list)
    aryplot (ax[0,0], 'Starting Voltage A', rly.t, [rly.VSTAG, rly.VSTAB, rly.VSTARTP*np.ones(rly.npt), 
                                           rly.VSTARTG*np.ones(rly.npt)], 
            ['Gnd', 'AB', '', ''], ['r', 'b', 'orange', 'c'])
    aryplot (ax[0,1], 'Starting Voltage B', rly.t, [rly.VSTBG, rly.VSTBC, rly.VSTARTP*np.ones(rly.npt), 
                                           rly.VSTARTG*np.ones(rly.npt)], 
            ['Gnd', 'BC', '', ''], ['r', 'b', 'orange', 'c'])
    aryplot (ax[0,2], 'Starting Voltage C', rly.t, [rly.VSTCG, rly.VSTCA, rly.VSTARTP*np.ones(rly.npt), 
                                           rly.VSTARTG*np.ones(rly.npt)],
            ['Gnd', 'CA', '', ''], ['r', 'b', 'orange', 'c'])
    aryplot (ax[1,0], 'Predicted Starting A', rly.t, [rly.PSTAG + 2, rly.PSTAB], ['Gnd', 'AB'], ['r', 'b'])
    aryplot (ax[1,1], 'Predicted Starting B', rly.t, [rly.PSTBG + 2, rly.PSTBC], ['Gnd', 'BC'], ['r', 'b'])
    aryplot (ax[1,2], 'Predicted Starting C', rly.t, [rly.PSTCG + 2, rly.PSTCA], ['Gnd', 'CA'], ['r', 'b'])
    if rly.haveDigitalOutputs == True:
        arysigplot (ax[2,0], 'Fault Ident A', rly.t, 
                    [rly.PFSAG, rly.sigs['FSAG'], rly.PFSAB, rly.sigs['FSAB']],
                    ['Gnd Pred', 'Gnd Act', 'AB Pred', 'AB Act'],
                    ['r', 'orange', 'b', 'c'])
        arysigplot (ax[2,1], 'Fault Ident B', rly.t, 
                    [rly.PFSBG, rly.sigs['FSBG'], rly.PFSBC, rly.sigs['FSBC']],
                    ['Gnd Pred', 'Gnd Act', 'BC Pred', 'BC Act'],
                    ['r', 'orange', 'b', 'c'])
        arysigplot (ax[2,2], 'Fault Ident C', rly.t, 
                    [rly.PFSCG, rly.sigs['FSCG'], rly.PFSCA, rly.sigs['FSCA']],
                    ['Gnd Pred', 'Gnd Act', 'CA Pred', 'CA Act'],
                    ['r', 'orange', 'b', 'c'])
    else:
        arysigplot (ax[2,0], 'Fault Ident A', rly.t, [rly.PFSAG, rly.PFSAB], ['Gnd', 'AB'], ['r', 'b'])
        arysigplot (ax[2,1], 'Fault Ident B', rly.t, [rly.PFSBG, rly.PFSBC], ['Gnd', 'BC'], ['r', 'b'])
        arysigplot (ax[2,2], 'Fault Ident C', rly.t, [rly.PFSCG, rly.PFSCA], ['Gnd', 'CA'], ['r', 'b'])
    finish_png (plt, ax, nrows, png_name)

def make_ident_plot (base_title, png_name, rly):
    nrows = 2
    ncols = 4
    ax = start_png (nrows, base_title, ncols)
    chanplot (ax[0, 0], 'DIZ (Sec)',  rly.t, rly.chan, ['DIZA', 'DIZB', 'DIZC', 'DIZ0'])
    chanplot (ax[0, 1], 'DV (Sec)',   rly.t, rly.chan, ['DVA', 'DVB', 'DVC'])
    aryplot (ax[1,0], 'Vstart Operating', rly.t, 
            [rly.VSTAG, rly.VSTAB, rly.VSTBG, rly.VSTBC, rly.VSTCG, rly.VSTCA, rly.VSTARTG*np.ones(rly.npt), rly.VSTARTP*np.ones(rly.npt), rly.VSTMAX], 
            ['AG', 'AB', 'BG', 'BC', 'CG', 'CA', 'GND', 'PHS', 'MAX'], 
            ['k', 'gray', 'r', 'salmon', 'b', 'c', 'green', 'limegreen', 'orange'])
#   aryplot (ax[1,1], 'TD32 Operating', rly.t,
#           [rly.I32OA, rly.I32OAB, rly.I32OB, rly.I32OBC, rly.I32OC, rly.I32OCA],
#           ['AG', 'AB', 'BG', 'BC', 'CG', 'CA'],
#           ['k', 'gray', 'r', 'salmon', 'b', 'c'])
    aryplot (ax[1,1], 'TD32 Raw', rly.t, 
            [rly.RAW32AG, rly.RAW32AB, rly.RAW32BG, rly.RAW32BC, rly.RAW32CG, rly.RAW32CA, rly.RAW32MAX], 
            ['AG', 'AB', 'BG', 'BC', 'CG', 'CA', 'MAX'], 
            ['k', 'gray', 'r', 'salmon', 'b', 'c', 'orange'])
    arysigplot (ax[0,2], 'Predicted TD32 Pickups', rly.t,
           [rly.P32FAG, rly.P32FAB, rly.P32FBG, rly.P32FBC, rly.P32FCG, rly.P32FCA],
           ['AG', 'AB', 'BG', 'BC', 'CG', 'CA'],
           ['k', 'gray', 'r', 'salmon', 'b', 'c'])
    arysigplot (ax[0,3], 'Predicted Starting', rly.t, 
            [rly.PSTAG, rly.PSTAB, rly.PSTBG, rly.PSTBC, rly.PSTCG, rly.PSTCA], 
            ['AG', 'AB', 'BG', 'BC', 'CG', 'CA'], 
            ['k', 'gray', 'r', 'salmon', 'b', 'c'])
    sigplot (ax[1, 2], 'Relay Fault Ident', rly.t, rly.sigs, ['FSAG', 'FSAB', 'FSBG', 'FSBC', 'FSCG', 'FSCA'])
    arysigplot (ax[1, 3], 'Predicted Fault Ident', rly.t, 
                [rly.PFSAG, rly.PFSAB, rly.PFSBG, rly.PFSBC, rly.PFSCG, rly.PFSCA],
                ['AG', 'AB', 'BG', 'BC', 'CG', 'CA'],
                ['k', 'gray', 'r', 'salmon', 'b', 'c'])
    finish_png (plt, ax, nrows, png_name, ncols)

def make_directional_plot (base_title, png_name, rly):
    nrows = 3
    ax = start_png (nrows, base_title)
#   chanplot (ax[0, 0], 'DIZ (Sec)',  rly.t, rly.chan, ['DIZA', 'DIZB', 'DIZC', 'DIZ0'])
#   chanplot (ax[0, 1], 'DV (Sec)',   rly.t, rly.chan, ['DVA', 'DVB', 'DVC'])
#   arysigplot (ax[0, 2], 'Fault Identification', rly.t,
#               [rly.PFSAG, rly.PFSAB, rly.PFSBG, rly.PFSBC, rly.PFSCG, rly.PFSCA],
#               ['AG', 'AB', 'BG', 'BC', 'CG', 'CA'],
#               ['k', 'gray', 'r', 'salmon', 'b', 'c'])
    aryplot (ax[0,0], 'TD32 AB Signals', rly.t, [rly.I32OAB, rly.I32RFAB, rly.I32RRAB], 
             ['OP', 'RF', 'RR'], ['r', 'b', 'g'])
    aryplot (ax[0,1], 'TD32 BC Signals', rly.t, [rly.I32OBC, rly.I32RFBC, rly.I32RRBC], 
             ['OP', 'RF', 'RR'], ['r', 'b', 'g'])
    aryplot (ax[0,2], 'TD32 CA Signals', rly.t, [rly.I32OCA, rly.I32RFCA, rly.I32RRCA], 
             ['OP', 'RF', 'RR'], ['r', 'b', 'g'])
    aryplot (ax[1,0], 'TD32 AG Signals', rly.t, [rly.I32OA, rly.I32RFA, rly.I32RRA], 
             ['OP', 'RF', 'RR'], ['r', 'b', 'g'])
    aryplot (ax[1,1], 'TD32 BG Signals', rly.t, [rly.I32OB, rly.I32RFB, rly.I32RRB], 
             ['OP', 'RF', 'RR'], ['r', 'b', 'g'])
    aryplot (ax[1,2], 'TD32 CG Signals', rly.t, [rly.I32OC, rly.I32RFC, rly.I32RRC], 
             ['OP', 'RF', 'RR'], ['r', 'b', 'g'])
    if rly.haveDigitalOutputs == True:
        aryplot (ax[2,0], 'TD32 A Pickups', rly.t, [rly.P32FA + 6, rly.sigs['TD32FA'] + 4, rly.P32RA + 2, rly.sigs['TD32RA']],
            ['Fwd Pred', 'Fwd Act', 'Rev Pred', 'Rev Act'], ['r', 'orange', 'b', 'c'])
        aryplot (ax[2,1], 'TD32 B Pickups', rly.t, [rly.P32FB + 6, rly.sigs['TD32FB'] + 4, rly.P32RB + 2, rly.sigs['TD32RB']], 
            ['Fwd Pred', 'Fwd Act', 'Rev Pred', 'Rev Act'], ['r', 'orange', 'b', 'c'])
        aryplot (ax[2,2], 'TD32 C Pickups', rly.t, [rly.P32FC + 6, rly.sigs['TD32FC'] + 4, rly.P32RC + 2, rly.sigs['TD32RC']], 
            ['Fwd Pred', 'Fwd Act', 'Rev Pred', 'Rev Act'], ['r', 'orange', 'b', 'c'])
    else:
        arysigplot (ax[2,0], 'TD32 A Pickups', rly.t, [rly.P32FA, rly.P32RA], ['Forward', 'Reverse'], ['r', 'b'])
        arysigplot (ax[2,1], 'TD32 B Pickups', rly.t, [rly.P32FB, rly.P32RB], ['Forward', 'Reverse'], ['r', 'b'])
        arysigplot (ax[2,2], 'TD32 C Pickups', rly.t, [rly.P32FC, rly.P32RC], ['Forward', 'Reverse'], ['r', 'b'])
    finish_png (plt, ax, nrows, png_name)

def make_overcurrent_plot (base_title, png_name, rly):
    nrows = 3
    ax = start_png (nrows, base_title)
#   chanplot (ax[0, 0], 'DIZ (Sec)',  rly.t, rly.chan, ['DIZA', 'DIZB', 'DIZC', 'DIZ0'])
#   chanplot (ax[0, 1], 'DV (Sec)',   rly.t, rly.chan, ['DVA', 'DVB', 'DVC'])
#   arysigplot (ax[0, 2], 'Fault Identification', rly.t,
#               [rly.PFSAG, rly.PFSAB, rly.PFSBG, rly.PFSBC, rly.PFSCG, rly.PFSCA],
#               ['AG', 'AB', 'BG', 'BC', 'CG', 'CA'],
#               ['k', 'gray', 'r', 'salmon', 'b', 'c'])
    aryplot (ax[0,0], 'OC21 AG Signals', rly.t, [rly.IOCAG, rly.IOCPUG], ['Iop', 'PU'], ['r', 'g'])
    aryplot (ax[0,1], 'OC21 BG Signals', rly.t, [rly.IOCBG, rly.IOCPUG], ['Iop', 'PU'], ['r', 'g'])
    aryplot (ax[0,2], 'OC21 CG Signals', rly.t, [rly.IOCCG, rly.IOCPUG], ['Iop', 'PU'], ['r', 'g'])
    aryplot (ax[1,0], 'OC21 AB Signals', rly.t, [rly.IOCAB, rly.IOCPUP], ['Iop', 'PU'], ['r', 'g'])
    aryplot (ax[1,1], 'OC21 BC Signals', rly.t, [rly.IOCBC, rly.IOCPUP], ['Iop', 'PU'], ['r', 'g'])
    aryplot (ax[1,2], 'OC21 CA Signals', rly.t, [rly.IOCCA, rly.IOCPUP], ['Iop', 'PU'], ['r', 'g'])
    if rly.haveDigitalOutputs == True:
        aryplot (ax[2,0], 'OC21 A Pickups', rly.t, [rly.POCAG + 6, rly.sigs['OC21AG'] + 4, rly.POCAB + 2, rly.sigs['OC21AB']],
                 ['Gnd Pred', 'Gnd Act', 'AB Pred', 'AB Act'], ['r', 'orange', 'b', 'c'])
        aryplot (ax[2,1], 'OC21 B Pickups', rly.t, [rly.POCBG + 6, rly.sigs['OC21BG'] + 4, rly.POCBC + 2, rly.sigs['OC21BC']],
                 ['Gnd Pred', 'Gnd Act', 'BC Pred', 'BC Act'], ['r', 'orange', 'b', 'c'])
        aryplot (ax[2,2], 'OC21 C Pickups', rly.t, [rly.POCCG + 6, rly.sigs['OC21CG'] + 4, rly.POCCA + 2, rly.sigs['OC21CA']],
                 ['Gnd Pred', 'Gnd Act', 'CA Pred', 'CA Act'], ['r', 'orange', 'b', 'c'])
    else:
        arysigplot (ax[2,0], 'OC21 A Pickups', rly.t, [rly.POCAG, rly.POCAB], ['Gnd', 'AB'], ['r', 'b'])
        arysigplot (ax[2,1], 'OC21 B Pickups', rly.t, [rly.POCBG, rly.POCBC], ['Gnd', 'BC'], ['r', 'b'])
        arysigplot (ax[2,2], 'OC21 C Pickups', rly.t, [rly.POCCG, rly.POCCA], ['Gnd', 'CA'], ['r', 'b'])
    finish_png (plt, ax, nrows, png_name)

def make_distance_plot (base_title, png_name, rly):
    nrows = 3  # TD21 outputs are already supervised, so we don't need to plot the raw pickups
    ax = start_png (nrows, base_title)
    aryplot (ax[0,0], 'TD21 AG Signals', rly.t, [rly.TD21OAG, rly.TD21RAG, -rly.TD21RAG, rly.spu*rly.RPG, -rly.spu*rly.RPG], 
             ['OP', 'RT', '-RT', 'TH', ''], ['r', 'b', 'c', 'g', 'g'])
    aryplot (ax[0,1], 'TD21 BG Signals', rly.t, [rly.TD21OBG, rly.TD21RBG, -rly.TD21RBG, rly.spu*rly.RPG, -rly.spu*rly.RPG], 
             ['OP', 'RT', '-RT', 'TH', ''], ['r', 'b', 'c', 'g', 'g'])
    aryplot (ax[0,2], 'TD21 CG Signals', rly.t, [rly.TD21OCG, rly.TD21RCG, -rly.TD21RCG, rly.spu*rly.RPG, -rly.spu*rly.RPG], 
             ['OP', 'RT', '-RT', 'TH', ''], ['r', 'b', 'c', 'g', 'g'])
    aryplot (ax[1,0], 'TD21 AB Signals', rly.t, [rly.TD21OAB, rly.TD21RAB, -rly.TD21RAB, rly.spu*rly.RPP, -rly.spu*rly.RPP], 
             ['OP', 'RT', '-RT', 'TH', ''], ['r', 'b', 'c', 'g', 'g'])
    aryplot (ax[1,1], 'TD21 BC Signals', rly.t, [rly.TD21OBC, rly.TD21RBC, -rly.TD21RBC, rly.spu*rly.RPP, -rly.spu*rly.RPP], 
             ['OP', 'RT', '-RT', 'TH', ''], ['r', 'b', 'c', 'g', 'g'])
    aryplot (ax[1,2], 'TD21 CA Signals', rly.t, [rly.TD21OCA, rly.TD21RCA, -rly.TD21RCA, rly.spu*rly.RPP, -rly.spu*rly.RPP], 
             ['OP', 'RT', '-RT', 'TH', ''], ['r', 'b', 'c', 'g', 'g'])
    if rly.haveDigitalOutputs == True:
        aryplot (ax[2,0], 'TD21 A Pickups', rly.t, [rly.S21AG + 6, rly.sigs['TD21AG'] + 4, rly.S21AB + 2, rly.sigs['TD21AB']],
                 ['Gnd Pred', 'Gnd Act', 'AB Pred', 'AB Act'], ['r', 'orange', 'b', 'c'])
        aryplot (ax[2,1], 'TD21 B Pickups', rly.t, [rly.S21BG + 6, rly.sigs['TD21BG'] + 4, rly.S21BC + 2, rly.sigs['TD21BC']],
                 ['Gnd Pred', 'Gnd Act', 'BC Pred', 'BC Act'], ['r', 'orange', 'b', 'c'])
        aryplot (ax[2,2], 'TD21 C Pickups', rly.t, [rly.S21CG + 6, rly.sigs['TD21CG'] + 4, rly.S21CA + 2, rly.sigs['TD21CA']],
                 ['Gnd Pred', 'Gnd Act', 'CA Pred', 'CA Act'], ['r', 'orange', 'b', 'c'])
    else:
        arysigplot (ax[2,0], 'TD21 A Pickups', rly.t, [rly.S21AG, rly.S21AB], ['Gnd', 'AB'], ['r', 'b'])
        arysigplot (ax[2,1], 'TD21 B Pickups', rly.t, [rly.S21BG, rly.S21BC], ['Gnd', 'BC'], ['r', 'b'])
        arysigplot (ax[2,2], 'TD21 C Pickups', rly.t, [rly.S21CG, rly.S21CA], ['Gnd', 'CA'], ['r', 'b'])
    finish_png (plt, ax, nrows, png_name)

def make_plot (do_plot, base_title, png_name, rly):
    base_title = '{:s} {:s}'.format(base_title, do_plot.name)

    if do_plot == PlotType.WAVEFORMS:
        make_waveform_plot (base_title, png_name, rly)
    if do_plot == PlotType.START:
        make_starting_plot (base_title, png_name, rly)
    elif do_plot == PlotType.DIRECTIONAL:
        make_directional_plot (base_title, png_name, rly)
    elif do_plot == PlotType.OVERCURRENT:
        make_overcurrent_plot (base_title, png_name, rly)
    elif do_plot == PlotType.DISTANCE:
        make_distance_plot (base_title, png_name, rly)
    elif do_plot == PlotType.IDENT:
        make_ident_plot (base_title, png_name, rly)
    elif do_plot == PlotType.REPLICA:
        make_replica_plot (base_title, png_name, rly)
    elif do_plot == PlotType.PDFS:
        make_pdf_waveforms ('Figure4.pdf', rly)
        make_pdf_incremental ('Figure5.pdf', rly)
        make_pdf_signals ('Figure6.pdf', rly)

sel_base = sys.argv[1]
settings_name = ''
do_plot = PlotType.START
site_name = ''
event_num = ''
if len(sys.argv) > 2:
    site_name = sys.argv[2]
if len(sys.argv) > 3:
    do_plot = PlotType(int(sys.argv[3]))
if len(sys.argv) > 4:
    event_num = sys.argv[4]

settings_name = 'Settings{:s}.json'.format(site_name)
png_name = '{:s}_TDR_{:s}.png'.format (site_name, event_num)

rec = Comtrade()
rec.load(sel_base + '.cfg', sel_base + '.dat')
trigger = str(rec.trigger_timestamp).split()
rly = T400L.T400L()
if len(settings_name) > 0:
    dict = json.load(open(settings_name))
    rly.update_settings (dict)
rly.load_comtrade (rec)

#print (sel_base, 'Pickup Times')
#tabulate_relay2 ('Phase A', rly.S21AB, rly.S21AG, rly.t)
#tabulate_relay2 ('Phase B', rly.S21BC, rly.S21BG, rly.t)
#tabulate_relay2 ('Phase C', rly.S21CA, rly.S21CG, rly.t)

vals = [site_name, trigger[0], trigger[1], event_num]
print (','.join(['Site', 'Date', 'Time', 'Event'] + scan_sigs))
for key in scan_sigs:
    tsig = sig_time (rly.sigs[key], rly.t)
    if tsig >= 0.0:
        vals.append ('{:.5f}'.format(tsig))
    else:
        vals.append ('')
print (','.join(vals))

if do_plot == PlotType.ALL:
    plot_set = [PlotType.WAVEFORMS, PlotType.REPLICA, PlotType.START, PlotType.DIRECTIONAL, PlotType.OVERCURRENT, PlotType.DISTANCE]
else:
    plot_set = [do_plot]

base_title = 'Site {:s}, TDR_{:s}, Date {:s}, Time {:s}'.format(site_name, event_num, trigger[0], trigger[1])
for do_plot in plot_set:
    png_name = get_png_name ('{:s}_TDR_{:s}'.format (site_name, event_num), do_plot)
#    png_name = '{:s}_TDR_{:s}_{:d}.png'.format (site_name, event_num)
#    png_name = ''
    make_plot (do_plot, base_title, png_name, rly)

