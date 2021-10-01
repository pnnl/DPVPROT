# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: TabulateRelays.py
""" Summarize T400L pickups from ATP-generated COMTRADE files.

Paragraph.

Public Functions:
    :main: does the work
"""

import csv

def parse_cv_casename (s):
    name = s[:-4]
    toks = name.split ('_')
    ckt = toks[0]
    loc = toks[1]
    phs = toks[2]
    if 'CAP' in loc:
        phs = 'ABC'
    return ckt, loc, phs

def parse_td_casename (s):
    name = s[6:]
    toks = name.split ('_')
    ckt = toks[0]
    loc = toks[1]
    phs = toks[2]
    if 'CAP' in loc:
        phs = 'ABC'
    return ckt, loc, phs

def count_cv_rows (cvTimes, ckt, site, loc, phs, wildcard=False):
    ntotal = 0
    nuv45 = 0
    nq46 = 0
    nq47 = 0
    for row in cvTimes:
        bSiteMatch = (row['Site'] == site)
        if wildcard:
            if 'PVXF' in row['Site']:
                if site == 'PVXFM':
                    bSiteMatch = True
            elif 'PV' in row['Site']:
                if site == 'PVPCC':
                    bSiteMatch = True
        if (row['Circuit'] == ckt) and bSiteMatch and (row['Phases'] == phs):
            bLocMatch = False
            rowLoc = row['Location']
            if loc == 'CAP':
                if ('CAP' in rowLoc):
                    bLocMatch = True
            elif (loc == 'ADJ'):
                if ('ADJ' in rowLoc):
                    bLocMatch = True
            elif (loc == 'FLT'):
                if ('ADJ' not in rowLoc) and ('CAP' not in rowLoc):
                    bLocMatch = True
            if bLocMatch:
                ntotal += 1
                if float(row['T45']) > 0.0:
                    nuv45 += 1
                if float(row['Q46']) > 0.0:
                    nq46 += 1
                if float(row['Q47']) > 0.0:
                    nq47 += 1
    return ntotal, nuv45, nq46, nq47

def count_td_rows (tdTimes, ckt, site, loc, phs, wildcard=False):
    ntotal = 0
    ntf32 = 0
    noc21p = 0
    noc21g = 0
    ntd21p = 0
    ntd21g = 0
    for row in tdTimes:
        bSiteMatch = (row['Site'] == site)
        if wildcard:
            if 'PVXF' in row['Site']:
                if site == 'PVXFM':
                    bSiteMatch = True
            elif 'PV' in row['Site']:
                if site == 'PVPCC':
                    bSiteMatch = True
        if (row['Circuit'] == ckt) and bSiteMatch and (row['Phases'] == phs):
            bLocMatch = False
            rowLoc = row['Location']
            if loc == 'CAP':
                if ('CAP' in rowLoc):
                    bLocMatch = True
            elif (loc == 'ADJ'):
                if ('ADJ' in rowLoc):
                    bLocMatch = True
            elif (loc == 'FLT'):
                if ('ADJ' not in rowLoc) and ('CAP' not in rowLoc):
                    bLocMatch = True
            if bLocMatch:
#                print (row)
                ntotal += 1
                if float(row['TF32']) > 0.0:
                    ntf32 += 1
                if float(row['OC21P']) > 0.0:
                    noc21p += 1
                if float(row['OC21G']) > 0.0:
                    noc21g += 1
                if float(row['TD21P']) > 0.0:
                    ntd21p += 1
                if float(row['TD21G']) > 0.0:
                    ntd21g += 1
    return ntotal, ntf32, noc21p, noc21g, ntd21p, ntd21g

def summarize_cv_times (cvTimes, ckt, site, wildcard = False):
    ncases = 0
    ntotal, nuv45, nq46, nq47 = count_cv_rows (cvTimes, ckt, site, 'FLT', 'ABC', wildcard)
    print ('{:8s} {:6s} {:3s} {:3s} {:3d} {:3d} {:3d} {:3d}'.format (ckt, site, 'FLT', 'ABC', ntotal, nuv45, nq46, nq47))
    ncases += ntotal

    ntotal, nuv45, nq46, nq47 = count_cv_rows (cvTimes, ckt, site, 'FLT', 'A', wildcard)
    print ('{:8s} {:6s} {:3s} {:3s} {:3d} {:3d} {:3d} {:3d}'.format ('', '', 'FLT', 'A', ntotal, nuv45, nq46, nq47))
    ncases += ntotal

    ntotal, nuv45, nq46, nq47 = count_cv_rows (cvTimes, ckt, site, 'ADJ', 'ABC', wildcard)
    print ('{:8s} {:6s} {:3s} {:3s} {:3d} {:3d} {:3d} {:3d}'.format ('', '', 'ADJ', 'ABC', ntotal, nuv45, nq46, nq47))
    ncases += ntotal

    ntotal, nuv45, nq46, nq47 = count_cv_rows (cvTimes, ckt, site, 'ADJ', 'A', wildcard)
    print ('{:8s} {:6s} {:3s} {:3s} {:3d} {:3d} {:3d} {:3d}'.format ('', '', 'ADJ', 'A', ntotal, nuv45, nq46, nq47))
    ncases += ntotal

    ntotal, nuv45, nq46, nq47 = count_cv_rows (cvTimes, ckt, site, 'CAP', 'ABC', wildcard)
    print ('{:8s} {:6s} {:3s} {:3s} {:3d} {:3d} {:3d} {:3d}'.format ('', '', 'CAP', 'ABC', ntotal, nuv45, nq46, nq47))
    ncases += ntotal

    return ncases

def summarize_td_times (tdTimes, ckt, site, wildcard = False):
    ncases = 0
    ntotal, ntf32, noc21p, noc21g, ntd21p, ntd21g = count_td_rows (tdTimes, ckt, site, 'FLT', 'ABC', wildcard)
    print ('{:8s} {:6s} {:3s} {:3s} {:3d} {:5d} {:5d} {:5d} {:5d} {:5d}'.format (ckt, site, 'FLT', 'ABC', ntotal, ntf32, noc21p, noc21g, ntd21p, ntd21g))
    ncases += ntotal

    ntotal, ntf32, noc21p, noc21g, ntd21p, ntd21g = count_td_rows (tdTimes, ckt, site, 'FLT', 'A', wildcard)
    print ('{:8s} {:6s} {:3s} {:3s} {:3d} {:5d} {:5d} {:5d} {:5d} {:5d}'.format ('', '', 'FLT', 'A', ntotal, ntf32, noc21p, noc21g, ntd21p, ntd21g))
    ncases += ntotal

    ntotal, ntf32, noc21p, noc21g, ntd21p, ntd21g = count_td_rows (tdTimes, ckt, site, 'ADJ', 'ABC', wildcard)
    print ('{:8s} {:6s} {:3s} {:3s} {:3d} {:5d} {:5d} {:5d} {:5d} {:5d}'.format ('', '', 'ADJ', 'ABC', ntotal, ntf32, noc21p, noc21g, ntd21p, ntd21g))
    ncases += ntotal

    ntotal, ntf32, noc21p, noc21g, ntd21p, ntd21g = count_td_rows (tdTimes, ckt, site, 'ADJ', 'A', wildcard)
    print ('{:8s} {:6s} {:3s} {:3s} {:3d} {:5d} {:5d} {:5d} {:5d} {:5d}'.format ('', '', 'ADJ', 'A', ntotal, ntf32, noc21p, noc21g, ntd21p, ntd21g))
    ncases += ntotal

    ntotal, ntf32, noc21p, noc21g, ntd21p, ntd21g = count_td_rows (tdTimes, ckt, site, 'CAP', 'ABC', wildcard)
    print ('{:8s} {:6s} {:3s} {:3s} {:3d} {:5d} {:5d} {:5d} {:5d} {:5d}'.format ('', '', 'CAP', 'ABC', ntotal, ntf32, noc21p, noc21g, ntd21p, ntd21g))
    ncases += ntotal

    return ncases

cvTimes = []
with open('RelayTimesNew.csv', mode='r') as infile:
    reader = csv.reader(infile)
    for row in reader:
        ckt, loc, phs = parse_cv_casename (row[0])
        cvTimes.append ({'Circuit':ckt, 'Location':loc, 'Phases':phs, 'Site':row[1], 'Tfault':row[2], 'T45':row[3], 'T60':row[4], 'T88':row[5], 'Q46':row[6], 'Q46len':row[7], 'Q47':row[8], 'Q47len':row[9]})

tdTimes = []
with open('T400LTimes.csv', mode='r') as infile:
    reader = csv.reader(infile)
    for i in range(3):
        next (reader)
    for row in reader:
        ckt, loc, phs = parse_td_casename (row[0])
        tdTimes.append ({'Circuit':ckt, 'Location':loc, 'Phases':phs, 'Site':row[1], 'Tfault':row[2], 'TF32':row[3], 'OC21P':row[4], 'OC21G':row[5], 'TD21P':row[6], 'TD21G':row[7]})

#print (tdTimes)

ncvsumm = 0
print ('                        CNT NUV N46 N47')
ckt = 'Louisa'
for site in ['Feeder', 'PVXFM', 'PVPCC']:
    ncvsumm += summarize_cv_times (cvTimes, ckt, site)
ckt = 'SHE215'
#for site in ['Feeder', 'PVXF1', 'PVXF2', 'PVONE', 'PVTWO']:
for site in ['Feeder', 'PVXFM', 'PVPCC']:
    ncvsumm += summarize_cv_times (cvTimes, ckt, site, wildcard=True)
ckt = 'RIV209'
for site in ['Feeder', 'PVXFM', 'PVPCC']:
    ncvsumm += summarize_cv_times (cvTimes, ckt, site)

print ('Summarized {:d} UV and Negative Sequence Cases'.format (ncvsumm))

ntdsumm = 0
print ('                        CNT TD32F OC21P OC21G TD21P TD21G')
ckt = 'Louisa'
for site in ['Feeder', 'PVXFM']:
    ntdsumm += summarize_td_times (tdTimes, ckt, site)
ckt = 'SHE215'
#for site in ['Feeder', 'PVXF1', 'PVXF2']:
for site in ['Feeder', 'PVXFM']:
    ntdsumm += summarize_td_times (tdTimes, ckt, site, wildcard=True)
ckt = 'RIV209'
for site in ['Feeder', 'PVXFM']:
    ntdsumm += summarize_td_times (tdTimes, ckt, site)

print ('Summarized {:d} Incremental Distance Cases'.format (ntdsumm))

