# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: ParseEvents.py
""" Summarize reclose, lockout, fault status from OpenDSS event study

Paragraph.

Public Functions:
    :main: does the work
"""

import json
import csv

states = {}
events = {}
tcleared = -1.0
tapplied = -1.0
operated = set()
lockopen = set()

with open('events.csv', mode='r') as infile:
  reader = csv.reader(infile)
  for row in reader:
    sec = row[1].split('=')[1]
    dvc = row[3].split('=')[1]
    act = row[4].split('=')[1]
    if len(dvc) > 1:
      print (sec, dvc, act)
      if dvc == 'Fault.flt':
        if act == '**APPLIED**':
          tapplied = float (sec)
        if act == '**CLEARED**':
          tcleared = float (sec)
      else:
        operated.add (dvc)
      states[dvc] = act
      events[sec, dvc] = act
	  
print (states)
print (events)
print ('operated devices are', operated)
for dvc in operated:
  if states[dvc] != 'CLOSED':
    lockopen.add(dvc)
print ('open devices are', lockopen)
if tcleared > 0.0:
  print ('fault cleared in', '{0:.4f}'.format(tcleared - tapplied), 'seconds')
elif tapplied > 0.0:
  print ('fault still on')
