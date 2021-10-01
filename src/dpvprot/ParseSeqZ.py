# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: ParseSeqZ.py
""" Tabulate seqz outputs from OpenDSS

The script reads a local buslist.dat for the bus names of interest.
Only the first comma-separated value is of interest, so the same
buslist.dat file used with RunFaults.py also works with this file.

Reads the seqz.csv file exported from an OpenDSS faultstudy solution.

The output is a summary of the impedances and fault currents
at each bus of interest.

Public Functions:
    :main: does the work

Args:
    kVLL (str): the line-to-line voltage [kV] to calculate fault current from impedance
    Rf (float): the maximum fault resistance [Ohms] for a single-line-to-ground fault
"""

import csv
import math
import sys

if __name__ == '__main__':
  vll = 1000.0 * float(sys.argv[1])
  vln = vll / math.sqrt(3.0)
  rf = float(sys.argv[2])
  buses = []

  print ('vln =', '{0:.2f}'.format(vln), ' and Rfault =', rf)

  with open('buslist.dat', mode='r') as infile:
    reader = csv.reader(infile)
    for row in reader:
      buses.append (row[0])

  print ('Bus #ph R1 X1 R0 X0 I3 Ill I1 I1rf')
  with open('seqz.csv', mode='r') as infile:
    reader = csv.reader(infile)
    next (reader, None)
    for row in reader:
      bus = row[0]
      if bus in buses:
        nph = int(row[1])
        r1 = float(row[2])
        x1 = float(row[3])
        r0 = float(row[4])
        x0 = float(row[5])
        zf = math.sqrt(r1*r1 + x1*x1)
        i3 = vln / zf
        ill = vll / (2.0 * zf)
        r = r1 + r1 + r0
        x = x1 + x1 + x0
        zf = math.sqrt(r*r + x*x)
        i1 = 3.0 * vln / zf
        r += 3.0 * rf
        zf = math.sqrt(r*r + x*x)
        i1rf = 3.0 * vln / zf
        if nph < 3:
          i3 = 0.0
          if nph < 2:
            ill = 0.0
        print (bus, nph, r1, x1, r0, x0, '{0:.1f}'.format(i3), '{0:.1f}'.format(ill), '{0:.1f}'.format(i1), '{0:.1f}'.format(i1rf))