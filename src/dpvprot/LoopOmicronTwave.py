# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: LoopOmicronTwave.py
""" Plots COMTRADE files for the Omicron?.

Uses ComtradeForOmicronTwave.py and OmicronCasesTwave.dat.

Public Functions:
    :main: does the work
"""

import subprocess

with open('OmicronCasesTwave.dat', mode='r') as infile:
	for ln in infile:
		toks = ln.split()
		if len(toks) < 2:
			break
		fdr = toks[0]
		bus = toks[1]
		targ = toks[2]
		loc = toks[3]
		subdir = toks[4]
		for i in range(5, len(toks)):
			phs = toks[i]
			fname_base = 'Omicron_{:s}_{:s}_{:s}_{:s}_{:s}'.format (fdr, subdir, targ, loc, phs)
			cmdline = 'python ComtradeForOmicronTwave.py {:s} {:s} {:s} {:s} {:s} {:s} {:s}'.format (fdr, bus, targ, phs, loc, subdir, fname_base)
			print (cmdline)
			pw0 = subprocess.Popen (cmdline, shell=True)
			pw0.wait()
#			quit()

