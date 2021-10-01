import sys
import csv
import random

# usage: python CreatePV.py percentage scaling_factor performance_category
penetration = 0.01 * float(sys.argv[1])
scale = float(sys.argv[2])
cat = int(sys.argv[3])

fp = open ('protected_pv.dss', 'w')
print ('// replacing all pvsystem with vccs', file=fp)
print ('batchedit pvsystem..* enabled=no', file=fp)
if (scale <= 0.0) or (penetration <= 0.0):
    print ('// zero-PV case', file=fp)
    print ('Total PV=0 kW')
    fp.close()
    quit()

pll_str = """New XYcurve.z_pll npts=3 xarray=[1.0000 -1.98515 0.98531] yarray=[0.0000 0.01485 -0.01469]"""
vccs_str = """~ filter='z_pll' fsample=10000 rmsmode=true imaxpu=1.15 vrmstau=0.01 irmstau=0.05"""
print (pll_str, file=fp)

fields = []
rows = []
total_kw = 0.0
count_pv = 0

random.seed(0) # for repeatability

with open ('TransformerList.dat', 'r') as csvfile:
    csvreader = csv.reader (csvfile)
    fields = next(csvreader)
    for row in csvreader:
        if random.random() <= penetration:
            name = row[0]
            this_kw = scale * float(row[1])
            total_kw += this_kw
            count_pv += 1
            print ('new vccs.{:s} Phases=2 Bus1={:s}.1.2 Prated={:.2f} Vrated=240 Ppct=100'.format (name,
                row[2], this_kw * 1000.0), file=fp)
            print (vccs_str, file=fp)
            print ('new relay.pv_{:s} monitoredobj=vccs.{:s} switchedobj=vccs.{:s}'.format (name, name, name), file=fp)
            print ('~  monitoredterm=1 switchedterm=1 type=voltage shots=1 delay=0.0', file=fp)
            print ('~  kvbase=0.24 overvoltcurve=ov1547_{:d} undervoltcurve=uv1547_{:d}'.format (cat, cat), file=fp)

print ('calcv', file=fp)
print ('// Total PV={:.3f} kW in {:d} units'.format (total_kw, count_pv), file=fp)
fp.close()

print ('added {:d} PV units totaling {:.2f} kW'.format(count_pv, total_kw))

