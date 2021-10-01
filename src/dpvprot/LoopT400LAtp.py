# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: LoopT400LAtp.py
""" Runs T400L plotting and analysis on ATP-generated COMTRADE files.

Uses T400LAtp.py and RelayCases.dat.

Public Functions:
    :main: does the work
"""

import subprocess

with open('RelayCases.dat', mode='r') as infile:
    for ln in infile:
        toks = ln.split()
        if len(toks) < 2:
            break
        fdr = toks[0]
        bus = toks[1]
        targ = toks[2]
        if targ == 'CAPS':
            png_base = 'T400L_{:s}_CAP_{:s}'.format (fdr, bus)
            cmdline = 'python T400LAtp.py {:s} {:s} CAPS {:s}'.format (fdr, bus, png_base)
#            print (cmdline)
            pw0 = subprocess.Popen (cmdline, shell=True)
            pw0.wait()
        else:
            atp = targ
            for i in range(3, len(toks)):
                phs = toks[i]
                png_base = 'T400L_{:s}_{:s}_{:s}'.format (fdr, atp, phs)
                cmdline = 'python T400LAtp.py {:s} {:s} {:s} {:s} {:s}'.format (fdr, bus, phs, atp, png_base)
#                print (cmdline)
                pw0 = subprocess.Popen (cmdline, shell=True)
                pw0.wait()
#        quit()

