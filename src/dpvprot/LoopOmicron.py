# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: LoopOmicron.py
""" Plots Omicron COMTRADE files.

Uses ComtradeForOmicron.py and OmicronCases.dat.

Public Functions:
    :main: does the work
"""

import subprocess

with open('OmicronCases.dat', mode='r') as infile:
	for ln in infile:
		toks = ln.split()
		if len(toks) < 2:
			break
		fdr = toks[0]
		bus = toks[1]
		targ = toks[2]
		loc = toks[3]
		q = toks[4]
		for i in range(5, len(toks)):
			phs = toks[i]
			fname_base = 'Omicron_{:s}_{:s}_{:s}_{:s}'.format (fdr, targ, loc, phs)
			cmdline = 'python ComtradeForOmicron.py {:s} {:s} {:s} {:s} {:s} {:s} {:s}'.format (fdr, bus, targ, phs, loc, q, fname_base)
			print (cmdline)
			pw0 = subprocess.Popen (cmdline, shell=True)
			pw0.wait()
#			quit()

