# Copyright (C) 2021 Battelle Memorial Institute
# file: RelaySummary.py
""" Summarize protection performance from a set of OpenDSS dynamic solutions.

Use RunEventStudy.py to produce all events.out files, renamed to pv*.out. The
script expects to read a set of files pv_%%_$$.out, where
%% is an integer PV penetration percentage, and $$ indicates the scheme.
$$ should be cat1, cat2, cat3, dist, or td21 (not included in report).

Sample invocation from pareto_data/IEEE8500 directory:

`python ..\..\RelaySummary.py IEEE8500 IEEE8500`

Public Functions:
    :main: does the work

Args:
    ckt_name (str): the name of the circuit for plot titles
    file_root (str): the name of PNG and PDF plot files, if desired
    max_pv (int): the percentage of PV penetration that 100 actually corresponds to.  Defaults to 100

Returns:
    str: writes a TeX row of summary values
"""

import sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

NOPEN_IDX = 0
NRECLOSE_IDX = 1
NFAILED_IDX = 2
NFALSE_IDX = 3
NPVTRIPS_IDX = 4
NFAULTS_IDX = 5
NUNCLEARED_IDX = 6
TMIN_IDX = 7
TMAX_IDX = 8
TMEAN_IDX = 9
TSTD_IDX = 10
NUM_NDATA = 11

TOC_IDX = 0
DIST_IDX = 1
TD21_IDX = 2
NUM_RELAYS = 3

CAT1_IDX = 0
CAT2_IDX = 1
CAT3_IDX = 2
NUM_CATS = 3

NUM_PCTS = 11

# default global variables
ckt_name = None
file_root = None
uv_cats = [1, 2, 3]
pv_pcts = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
plot_pv_pcts = []
# index by relay, cat, pct, val
ndata = np.zeros ((NUM_RELAYS,NUM_CATS,NUM_PCTS,NUM_NDATA))
tdata = {}

def start_pdf (nrows, ncols, suptitle=None):
    lsize = 8
    if ncols > 2:
        lsize = 8
    plt.rc('font', family='serif')
    plt.rc('xtick', labelsize=lsize)
    plt.rc('ytick', labelsize=lsize)
    plt.rc('axes', labelsize=lsize)
    plt.rc('legend', fontsize=lsize)
    pWidth = 6.5
    pHeight = pWidth / 1.618 / (0.7 * ncols)
    fig, ax = plt.subplots (nrows, ncols, figsize=(pWidth, pHeight), constrained_layout=True)
    if suptitle is not None:
        if ckt_name is not None:
            fig.suptitle ('{:s} {:s}'.format (ckt_name, suptitle))
        else:
            fig.suptitle (suptitle)
    elif ckt_name is not None:
        fig.suptitle (ckt_name)
    return ax

def finish_pdf (pdf_name=None, png_name=None):
    if pdf_name is not None:
        plt.savefig (pdf_name, dpi=300)
    if png_name is not None:
        plt.savefig (png_name, dpi=300)
    if (png_name is None) and (pdf_name is None):
        plt.show()

def make_summary_plot (rly_idx, cat_idx, suptitle, file_suffix=None):
    ax = start_pdf (1, 2, suptitle)

    n = int(ndata[rly_idx,cat_idx,0,NFAULTS_IDX])

    ax[0].set_title ('Event Counts ({:d} Faults)'.format (n))
    ax[0].plot (plot_pv_pcts, ndata[rly_idx,cat_idx,:,NFALSE_IDX], label='False Trip', color='g')
    ax[0].plot (plot_pv_pcts, ndata[rly_idx,cat_idx,:,NFAILED_IDX], label='Failed to Open', color='b')
    ax[0].plot (plot_pv_pcts, ndata[rly_idx,cat_idx,:,NUNCLEARED_IDX], label='Uncleared Fault', color='r')
    ax[0].grid()
    ax[0].set_xlabel ('PV Percent')
    ax[0].legend(loc='best')

    boxes = []
    for i in range(11):
        boxes.append (tdata[rly_idx][cat_idx][i])
    ax[1].set_title ('Fault Clearing Time [s]')
    ax[1].boxplot(boxes)
    ax[1].set_xlabel ('PV Percent')
    ax[1].set_xticklabels (plot_pv_pcts)
    ax2 = ax[1].twinx()
    ax2.plot (1.0 + 0.1 * np.array (pv_pcts), ndata[rly_idx,cat_idx,:,TMEAN_IDX], label='Mean', color='r')
    ax2.legend(loc='best')
    ax2.tick_params (axis='y', colors='r')

    pdf_name = None
    png_name = None
    if file_suffix is not None:
        if file_root is not None:
            pdf_name = file_root + file_suffix + '.pdf'
            png_name = file_root + file_suffix + '.png'

    finish_pdf (pdf_name=pdf_name, png_name=png_name)

def summarize_frame (data):
    tcleared = data[data['Cleared?']==True]['Tcleared']
    return [data['Nopen'].sum(),
            data['Nreclosed'].sum(),
            data['Nfailed'].sum(),
            data['Nfalse'].sum(),
            data['Npv'].sum(),
            data['Cleared?'].count(),
            data[data['Cleared?']==False]['Cleared?'].count(),
            tcleared.min(),
            tcleared.max(),
            tcleared.mean(),
            tcleared.std()],tcleared

def store_ndata (data, rly_idx, cat_idx, pct_idx):
    ary,tcleared = summarize_frame (data)
    tdata[rly_idx][cat_idx][pct_idx] = tcleared
    for idx in range(NUM_NDATA):
        ndata[rly_idx][cat_idx][pct_idx][idx] = ary[idx]

def find_worst_metrics (rly_idx, cat_idx):
    Nu = 0
    Nfail = 0
    Nfalse = 0
    Tclear = 0.0
    for pct_idx in range(NUM_PCTS):
        val = int (ndata[rly_idx][cat_idx][pct_idx][NUNCLEARED_IDX])
        if val > Nu:
            Nu = val
        val = int (ndata[rly_idx][cat_idx][pct_idx][NFAILED_IDX])
        if val > Nfail:
            Nfail = val
        val = int (ndata[rly_idx][cat_idx][pct_idx][NFALSE_IDX])
        if val > Nfalse:
            Nfalse = val
        val = ndata[rly_idx][cat_idx][pct_idx][TMEAN_IDX]
        if val > Tclear:
            Tclear = val
    return Nu, Nfail, Nfalse, Tclear

if __name__ == '__main__':
    # finalilze the global variables
    if len(sys.argv) > 1:
        ckt_name = sys.argv[1]
    if len(sys.argv) > 2:
        file_root = sys.argv[2]
    if len(sys.argv) > 3:
        pv_max = float(sys.argv[3])
        mult = pv_max / 100.0
        plot_pv_pcts = []
        for pct in pv_pcts:
            plot_pv_pcts.append (int(pct*mult))
    else:
        for pct in pv_pcts:
            plot_pv_pcts.append (pct)
    for i in range(NUM_RELAYS):
        tdata[i] = {}
        for j in range(NUM_CATS):
            tdata[i][j] = {}

    #print('Locked Open,Reclosed,Failed to Trip,False Trips,Faults,Uncleared,Tmin,Tmax,Tmean,Tstd')
    for pct in pv_pcts:
        for cat in uv_cats:
            case_name = 'pv_{:d}_cat{:d}'.format (pct, cat)
            data = pd.read_csv(case_name + '.out', delimiter=',', quotechar='"', keep_default_na=False)
            store_ndata (data, TOC_IDX, cat-1, int(pct/10))

    for pct in pv_pcts:
        for cat in [3]:
            case_name = 'pv_{:d}_cat{:d}_dist'.format (pct, cat)
            data = pd.read_csv(case_name + '.out', delimiter=',', quotechar='"', keep_default_na=False)
            store_ndata (data, DIST_IDX, cat-1, int(pct/10))
    #       case_name = 'pv_{:d}_cat{:d}_td21'.format (pct, cat)
    #       data = pd.read_csv(case_name + '.out', delimiter=',', quotechar='"', keep_default_na=False)
    #       store_ndata (data, TD21_IDX, cat-1, int(pct/10))

    make_summary_plot (TOC_IDX, CAT1_IDX, 'TOC Cat I', '_TOC1')
    make_summary_plot (TOC_IDX, CAT2_IDX, 'TOC Cat II', '_TOC2')
    make_summary_plot (TOC_IDX, CAT3_IDX, 'TOC Cat III', '_TOC3')
    make_summary_plot (DIST_IDX, CAT3_IDX, 'Distance Cat III', '_DIST3')

    #make_summary_plot (TD21_IDX, CAT3_IDX, 'TD21 Cat III')

    # for TOC1, TOC2, TOC3, DIST3 print the worst Nuncleared, Nfail, Nfalse, Mean Tclear
    Nu1, Nfail1, Nfalse1, Tclear1 = find_worst_metrics (TOC_IDX, CAT1_IDX)
    Nu2, Nfail2, Nfalse2, Tclear2 = find_worst_metrics (TOC_IDX, CAT2_IDX)
    Nu3, Nfail3, Nfalse3, Tclear3 = find_worst_metrics (TOC_IDX, CAT3_IDX)
    NuD, NfailD, NfalseD, TclearD = find_worst_metrics (DIST_IDX, CAT3_IDX)

    print ('{:s}&{:d}&{:d}&{:d}&{:.3f}&{:d}&{:d}&{:d}&{:.3f}&{:d}&{:d}&{:d}&{:.3f}&{:d}&{:d}&{:d}&{:.3f}'.format (ckt_name, 
      Nu1, Nfail1, Nfalse1, Tclear1, Nu2, Nfail2, Nfalse2, Tclear2, Nu3, Nfail3, Nfalse3, Tclear3, NuD, NfailD, NfalseD, TclearD))
