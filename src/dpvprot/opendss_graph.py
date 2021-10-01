# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: opendss_graph.py
""" Build and save a NetworkX graph of the OpenDSS feeder.

Paragraph.

Public Functions:
    :main: does the work
"""

import math
import sys
import networkx as nx
import json

kvbases = [0.208, 0.418, 0.48, 4.16, 12.47, 13.2, 13.8, 34.5, 69.0, 115.0, 138.0, 230.0]
def select_kvbase (val):
    kv = 12.47
    for i in range(len(kvbases)):
        err = abs(val/kvbases[i] - 1.0)
        if err < 0.02:
            kv = kvbases[i]
    return kv

def is_node_class(cls):
    if cls == 'load':
        return True
    if cls == 'capacitor':
        return True
    if cls == 'pvsystem':
        return True
    if cls == 'vsource':
        return True
    if cls == 'circuit':
        return True
    return False

def get_nclass(nd):
    if nd == '0':
        return 'ground'
    return 'bus'

def letter_phases (dss_phases):
    phs = ''
    if '1' in dss_phases:
        phs += 'A'
    if '2' in dss_phases:
        phs += 'B'
    if '3' in dss_phases:
        phs += 'C'
    return phs

def parse_bus_phases (busphs):
    idx = busphs.find('.')
    if idx >= 0:
        bus = busphs[:idx]
        phs = letter_phases (busphs[idx+1:])
    else:
        bus = busphs
        phs = 'ABC'
    return bus, phs

def dss_bus_phases (tok):
    bus = ''
    phs = ''
    if tok.startswith('bus1=') or tok.startswith('bus2='):
        bus, phs = parse_bus_phases (tok[5:])
    return bus, phs

def dss_parm (tok):
    idx = tok.find('=')
    if idx >= 0:
        tok = tok[idx+1:]
    idx = tok.find('(')
    if idx >= 0:
        tok = tok[idx+1:]
    idx = tok.find(')')
    if idx >= 0:
        tok = tok[:idx]
    return tok.strip()

def dss_transformer_bus_phases (tok1, tok2):
    bus1, phs1 = parse_bus_phases (dss_parm(tok1))
    bus2, phs2 = parse_bus_phases (dss_parm(tok2))
    return bus1, bus2, phs1, phs2

def dss_transformer_conns (tok1, tok2):
    parm1 = dss_parm (tok1)
    parm2 = dss_parm (tok2)
    return parm1, parm2

def dss_transformer_kvas (tok1, tok2):
    parm1 = dss_parm (tok1)
    parm2 = dss_parm (tok2)
    return float (parm1), float (parm2)

def dss_transformer_kvs (tok1, tok2):
    parm1 = dss_parm (tok1)
    parm2 = dss_parm (tok2)
    return float (parm1), float (parm2)

def dss_transformer_xhl (tok):
    return float (dss_parm(tok))

def adjust_nominal_kv (kv, nphs, bDelta):
    if (nphs == 1) and not bDelta:
        kv *= math.sqrt(3.0)
    return kv

def merge_ndata(old, new): # not touching nomkv, x, y, busnum, dist, phases
    if new['kw'] != 0.0:
        old['kw'] += new['kw']
    if new['kvar'] != 0.0:
        old['kvar'] += new['kvar']
    if new['capkvar'] != 0.0:
        old['capkvar'] += new['capkvar']
    if new['derkva'] != 0.0:
        old['derkva'] += new['derkva']
    if new['source']:
        old['source'] = True
    old['shunts'].append (new['shunts'][0])
    return old

def merge_busmap(dssdata, row):
    dssdata['busnum'] = row['busnum']
    dssdata['x'] = row['x']
    dssdata['y'] = row['y']
    dssdata['phases'] = row['phases']  # TODO - accumulate these from parsing individual model lines?
    return dssdata

def format_ndata(ndata):
    ndata ['kw'] = float ('{:.3f}'.format (ndata['kw']))
    ndata ['kvar'] = float ('{:.3f}'.format (ndata['kvar']))
    ndata ['capkvar'] = float ('{:.3f}'.format (ndata['capkvar']))
    ndata ['derkva'] = float ('{:.3f}'.format (ndata['derkva']))
    ndata ['nomkv'] = select_kvbase (ndata['nomkv'])
    return ndata

#----------------------------
# Read file from command line
#----------------------------
# example: python opendss_graph.py ReducedNetwork ReducedXY.dss
print ('usage: python opendss_graph.py ReducedNetwork ReducedXY.dss')
print ('       reads ReducedNetwork.atpmap, ReducedNetwork.dss and ReducedXY.dss')
print ('       writes ReducedNetwork.json')

# load in the bus names and numbers with XY coordinates
busxy = {}
xyp = open (sys.argv[2], 'r')
for row in xyp:
    busname, busx, busy, dist = row.lower().split()
    if busname not in busxy:
        busxy[busname] = {'x':float(busx),'y':float(busy),'dist':float(dist)}
xyp.close()
print ('loaded', len(busxy), 'bus coordinates')

root = sys.argv[1]

busmap = {}
mp = open(root + '.atpmap','r')
nxy = 0
for row in mp:
    busname, busnum, phases = row.lower().split()
    x = 0.0
    y = 0.0
    dist = 0.0
    if busname in busxy:
        x = busxy[busname]['x']
        y = busxy[busname]['y']
        d = busxy[busname]['dist']
        nxy += 1
    if busname not in busmap:
        busmap[busname] = {'busnum':int(busnum),'phases':phases,'x':x,'y':y,'dist':d,
            'kw':0.0,'kvar':0.0,'capkvar':0.0,'source':False,'derkva':0.0,'nomkv':0.0} # TODO - update these initial defaults?
mp.close()
print ('loaded', len(busmap), 'bus map entries, of which', nxy, 'have xy coordinates')
#print (busmap)

#-----------------------
# Pull Model Into Memory
#-----------------------
dp = open(root + '.dss','r')
lines = []
toks = None
for line in dp:
    line = line.strip().lower()
    if len(line) > 0:
        bContinue = line.startswith('~')
        bComment = line.startswith('//')
        if not bComment:
            newtoks = line.split()
            if bContinue:
                for i in range(1, len(newtoks)):
                    toks.append (newtoks[i])
            else:
                if toks:
                    lines.append (toks)
                toks = newtoks
lines.append(toks)
dp.close()
print ('read', len(lines), 'network model lines')

#for i in range(len(lines)):
#    if 'transformer' in lines[i][1]:
#        print (lines[i])

# construct a graph of the model, starting with known links
G = nx.Graph()
for ln in lines:
    if ln[0] == 'new':
        toks = ln[1].split('.')
        dssclass = toks[0]
        dssname = toks[1]
        phases = ''
        n1 = '0'
        n2 = '0'
        dssdata = {}
        if is_node_class (dssclass):
            dssdata['shunts'] = ['{:s}.{:s}'.format (dssclass, dssname)]
            dssdata['nomkv'] = 0.0
            dssdata['kw'] = 0.0
            dssdata['kvar'] = 0.0
            dssdata['capkvar'] = 0.0
            dssdata['derkva'] = 0.0
            if (dssclass == 'vsource') or (dssclass == 'circuit'):
                dssdata['source'] = True
            else:
                dssdata['source'] = False
            bDelta = False
            for i in range(2,len(ln)):
                if ln[i].startswith('bus1='):
                    n1, phases = dss_bus_phases (ln[i])
                elif ln[i].startswith('conn='):
                    if 'd' in dss_parm(ln[i]):
                        bDelta = True
                elif ln[i].startswith('kv='):
                    dssdata['nomkv'] = float (dss_parm(ln[i]))
                elif ln[i].startswith('kw=') and dssclass != 'storage':
                    dssdata['kw'] = float (dss_parm(ln[i]))
                elif ln[i].startswith('kvar='):
                    if dssclass == 'capacitor':
                        dssdata['capkvar'] = float (dss_parm(ln[i]))
                    else:
                        dssdata['kvar'] = float (dss_parm(ln[i]))
                elif ln[i].startswith('kva='):
                    dssdata['derkva'] = float (dss_parm(ln[i]))
            dssdata['phases'] = phases
            if 'nomkv' in dssdata:
                dssdata['nomkv'] = adjust_nominal_kv (dssdata['nomkv'], len(phases), bDelta)
            if n1 not in G.nodes():
                if n1 in busmap:
                    dssdata = merge_busmap (dssdata, busmap[n1])
                G.add_node (n1, nclass=get_nclass(n1), ndata=format_ndata(dssdata))
            else:
                if 'ndata' in G.nodes()[n1]:
                    dssdata = merge_ndata (G.nodes()[n1]['ndata'], dssdata)
                elif n1 in busmap:
                    dssdata = merge_busmap (dssdata, busmap[n1])
                G.nodes()[n1]['ndata'] = format_ndata(dssdata)
        else:
            for i in range(2,len(ln)):
                if ln[i].startswith('bus1='):
                    n1, phases = dss_bus_phases (ln[i])
                elif ln[i].startswith('bus2='):
                    n2, phases = dss_bus_phases (ln[i])
                elif ln[i].startswith('buses='):  # TODO: handle transformers with more than 2 windings
                    n1, n2, phs1, phs2 = dss_transformer_bus_phases (ln[i], ln[i+1])
                    dssdata['phs1'] = phs1
                    dssdata['phs2'] = phs2
                    phases = phs1
                elif ln[i].startswith('conns='):
                    conn1, conn2 = dss_transformer_conns (ln[i], ln[i+1])
                    dssdata['conn1'] = conn1
                    dssdata['conn2'] = conn2
                elif ln[i].startswith('kvs='):
                    kv1, kv2 = dss_transformer_kvs (ln[i], ln[i+1])
                    dssdata['kv1'] = kv1
                    dssdata['kv2'] = kv2
                elif ln[i].startswith('kvas='):
                    kva1, kva2 = dss_transformer_kvas (ln[i], ln[i+1])
                    dssdata['kva1'] = kva1
                    dssdata['kva2'] = kva2
                elif ln[i].startswith('xhl='):
                    dssdata['xhl'] = dss_transformer_xhl (ln[i])
                elif ln[i].startswith('kw='):
                    dssdata['kw'] = float (dss_parm(ln[i]))
                elif ln[i].startswith('kvar='):
                    dssdata['kvar'] = float (dss_parm(ln[i]))
                elif ln[i].startswith('len='):
                    dssdata['len'] = float (dss_parm(ln[i]))
                elif ln[i].startswith('kv='):
                    dssdata['kv'] = float (dss_parm(ln[i]))
                elif ln[i].startswith('r1='):
                    dssdata['r1'] = float (dss_parm(ln[i]))
                elif ln[i].startswith('x1='):
                    dssdata['x1'] = float (dss_parm(ln[i]))
                elif ln[i].startswith('c1='):
                    dssdata['c1'] = float (dss_parm(ln[i]))
                elif ln[i].startswith('r0='):
                    dssdata['r0'] = float (dss_parm(ln[i]))
                elif ln[i].startswith('x0='):
                    dssdata['x0'] = float (dss_parm(ln[i]))
                elif ln[i].startswith('c0='):
                    dssdata['c0'] = float (dss_parm(ln[i]))
                elif ln[i].startswith('conn='):
                    dssdata['conn'] = dss_parm(ln[i])
            dssdata['phases'] = phases
            G.add_edge(n1,n2,eclass=dssclass,ename=dssname,edata=dssdata)

# backfill missing node attributes
# TODO: try to fill in the missing/zero nomkv values
for n in G.nodes():
    if 'ndata' not in G.nodes()[n]:
        if n in busmap:
            row = busmap[n]
            dssdata = {'shunts':[], 'nomkv':0.0, 'kw':0.0, 'kvar':0.0, 'capkvar':0.0, 'derkva':0.0, 'source':False,
                    'phases':row['phases'], 'busnum':row['busnum'], 'x':row['x'], 'y':row['y']}
            G.nodes()[n]['ndata'] = dssdata
        else:
            print ('cannot find node', n, 'in the busmap')

# save the graph
json_fp = open (root + '.json', 'w')
json_data = nx.readwrite.json_graph.node_link_data(G)
json.dump (json_data, json_fp, indent=2)
json_fp.close()

