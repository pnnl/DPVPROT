# Copyright (C) 2021 Battelle Memorial Institute
# file: RelayPerformance.py
""" Summarize protection performance from a set of OpenDSS dynamic solutions.

First, use a local dofaults.bat, which invokes RunFaults.py, to produce events.out.
This script appends a cumulative summary of the fault results to the file dofaults.rpt.
The summary includes total number of cleared and uncleared faults, the total number of
utility devices that tripped, failed to trip, or false-tripped, and the total number of
DER devices that tripped. Considering faults that cleared, the minimum, maximum, mean, and
standard deviation of the clearing time is reported.

Also writes the header and data rows for a summary table in LaTex format, to the file dofaults.tex.

Public Functions:
    :main: does the work

Args:
    csv_name (str): the fault output file name, defaults to events.out

Returns:
    str: writes the same summary to console as appended to dofaults.rpt
"""

import sys
import os
import matplotlib.pyplot as plt
import pandas as pd

def print_summary (data, tcleared, fp=sys.stdout):
    print('Locked Open,Reclosed,Failed to Trip,False Trips,PV Trips,Faults,Uncleared,Tmin,Tmax,Tmean,Tstd', file=fp)
    print('{:d},{:d},{:d},{:d},{:d},{:d},{:d},{:.3f},{:.3f},{:.3f},{:.3f}'.format (
        data['Nopen'].sum(),
        data['Nreclosed'].sum(),
        data['Nfailed'].sum(),
        data['Nfalse'].sum(),
        data['Npv'].sum(),
        data['Cleared?'].count(),
        data[data['Cleared?']==False]['Cleared?'].count(),
        tcleared.min(),
        tcleared.max(),
        tcleared.mean(),
        tcleared.std()), file=fp)

    print ('Uncleared = {:d}'.format (data[data['Cleared?']==False]['Cleared?'].count()), file=fp)
    print ('Nfailed   = {:d}'.format (data['Nfailed'].sum()), file=fp)
    print ('Nfalse    = {:d}'.format (data['Nfalse'].sum()), file=fp)
    print ('Npv       = {:d}'.format (data['Npv'].sum()), file=fp)
    print ('Tmean = {:.3f}'.format (tcleared.mean()), file=fp)

csv_name = 'events.out'
if len(sys.argv) > 1:
    csv_name = sys.argv[1]

data = pd.read_csv(csv_name, delimiter=',', quotechar='"', keep_default_na=False)
#print (data)
tcleared = data[data['Cleared?']==True]['Tcleared']


print_summary (data, tcleared)
rp = open ('dofaults.rpt', 'a+')
print_summary (data, tcleared, rp)
rp.close()

if os.path.exists('dofaults.tex'):
    rp = open ('dofaults.tex', 'a+')
else:
    rp = open ('dofaults.tex', 'w')
    print ('\\pnnltable{\\begin{tabular}{l|c|c|c|c|c|c|c|c}', file=rp)
    print ('\\topcopperhline', file=rp)
    print ('Mode&\\boldmath$N_{U}$&\\boldmath$N_{FL}$&\\boldmath$N_{FS}$&\\boldmath$N_{PV}$&\\boldmath$T_{min}$&\\boldmath$T_{max}$&\\boldmath$T_{avg}$&\\boldmath$T_{std}$\\\\', file=rp)
    print ('\\midcopperhline', file=rp)
print ('X&{:d}&{:d}&{:d}&{:d}&{:.3f}&{:.3f}&{:.3f}&{:.3f}\\\\'.format(data[data['Cleared?']==False]['Cleared?'].count(),
                                                                    data['Nfailed'].sum(),
                                                                    data['Nfalse'].sum(),
                                                                    data['Npv'].sum(),
                                                                    tcleared.min(),
                                                                    tcleared.max(),
                                                                    tcleared.mean(),
                                                                    tcleared.std()), file=rp)
rp.close()


