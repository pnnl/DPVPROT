# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: MakeBatchPlotLines.py
""" Make the calling lines for T400LPlot.py from COMTRADE files in a directory.

Paragraph.

Public Functions:
    :main: does the work
"""

import sys
import operator
import glob

dict = {'c:/EPBdata/SHE Substation/T400L/':'ShepherdSub',
        'c:/EPBdata/S1P16567/T400L/':'ShepherdSite1',
        'c:/EPBdata/S3P009/T400L/':'ShepherdSite2',
        'c:/eRoom/Substation/':'Louisa',
        'c:/eRoom/POI/':'WhitehouseField',
        'c:/eRoom/HFRing/':'WhitehouseField'}

seqnum = 1

for rootdir, site in dict.items():
    settingsfile = 'Settings{:s}.json'.format (site)
    pattern = rootdir + '*TDR*.cfg'
    files = glob.glob (pattern)
    for fname in files:
        i1 = fname.upper().find(',TDR,')
        i2 = fname.upper().find('.CFG')
        eventnum = fname[i1+5:i2]
        print ("""python T400LPlot.py "{:s}" {:s} 5 {:s}""".format (fname[:-4], site, eventnum))

    pattern = rootdir + '*10kHz.cfg'
    files = glob.glob (pattern)
    for fname in files:
        print ("""python T400LPlot.py "{:s}" {:s} 5 {:d}""".format (fname[:-4], site, seqnum))
        seqnum += 1

