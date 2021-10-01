# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: AtpReduction.py
""" Writes a reduced-order ATP model, based on the model reduction of a full-size OpenDSS model.
Must be called from RunReduction.py
 
Public Functions:
    :WriteAtp: does the work

Args:
    atpfile (str): the name of the ATP file to write
    pairs (array): link information passed from RunReduction.py
    retained (set): names of retained buses, passed from RunReduction.py
    buses (dict): bus information, passed from RunReduction.py 
    seqz (dict): sequence impedancs of retained branches, passed from RunReduction.py
    foundCapacitors (boolean): indicates whether feeder capacitors are in ReducedCapacitors.dss
    bNoCaps (boolean): indicates to ignore shunt capacitance in line pi-section models

Returns:
    str: writes a message if ATP file not produced
"""

def WriteAtp(atpfile, pairs, retained, buses, seqz, foundCapacitors, bNoCaps):
  print ('**************************************************************************')
  print ('ATP file could not be written because of missing support for ATP Materials')
  print ('Please check the top-level repository readme file for more information')

