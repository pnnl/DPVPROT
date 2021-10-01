# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: ComtradeCasePlot.py
""" Plots the ATP simulation results from COMTRADE files.

Paragraph.

Public Functions:
    :main: does the work
"""

import sys
import matplotlib.pyplot as plt
from comtrade import Comtrade
import numpy as np

#print (plt.gcf().canvas.get_supported_filetypes())
#quit()
faultChannels = {'Ia':-1,'Ib':-1,'Ic':-1}
feederChannels = {'Va':-1,'Vb':-1,'Vc':-1,'Ia':-1,'Ib':-1,'Ic':-1}
pvChannels = {}
pvnames = []

#pl4_path = 'c:/pl4/Louisa/'
#atp_case = sys.argv[1]
#atp_base = pl4_path + atp_case
atp_base = sys.argv[1]

idx = atp_base.upper().find('/PL4/')
png_name = atp_base[idx+5:].replace('/', '_') + '.png'
#png_name = ''
#print (png_name)
#quit()

npv = len(sys.argv) - 2
suffix = 0
for i in range(npv):
    pv = sys.argv[2+i]
    pvnames.append(pv)
    if npv > 1:
        suffix = i + 1
    pvChannels[pv] = {'Va':-1,'Vb':-1,'Vc':-1,'Ia':-1,'Ib':-1,'Ic':-1,
        'wp':-1,'ang':-1,'Vmag':-1,'Imag':-1,'ModelSuffix':suffix}

rec = Comtrade()
rec.load(atp_base + '.cfg', atp_base + '.dat')
#print('Analog Count', rec.analog_count)
#print('Status Count', rec.status_count)
#print('File Name', rec.filename) 
#print('Station', rec.station_name)
#print('N', rec.total_samples)

t = np.array(rec.time)
for i in range(rec.analog_count):
    lbl = rec.analog_channel_ids[i]
#    print (i, lbl)
    if 'V-node' in lbl:
        if 'FDR  A' in lbl:
            feederChannels['Va'] = np.array (rec.analog[i])
        elif 'FDR  B' in lbl:
            feederChannels['Vb'] = np.array (rec.analog[i])
        elif 'FDR  C' in lbl:
            feederChannels['Vc'] = np.array (rec.analog[i])
    elif 'I-branch' in lbl:
        for pv in pvnames:
            if pvChannels[pv]['ModelSuffix'] > 0:
                wpMatch = 'MODELS WP' + str(pvChannels[pv]['ModelSuffix'])
                angMatch = 'MODELS ANG' + str(pvChannels[pv]['ModelSuffix'])
                vMatch = 'MODELS MAG' + str(pvChannels[pv]['ModelSuffix'])
                iMatch = 'MODELS IRMS' + str(pvChannels[pv]['ModelSuffix'])
            else:
                wpMatch = 'MODELS WP'
                angMatch = 'MODELS ANG'
                vMatch = 'MODELS MAG'
                iMatch = 'MODELS IRMS'
            if pv+'A' in lbl:
                pvChannels[pv]['Ia'] = np.array (rec.analog[i])
            elif pv+'B' in lbl:
                pvChannels[pv]['Ib'] = np.array (rec.analog[i])
            elif pv+'C' in lbl:
                pvChannels[pv]['Ic'] = np.array (rec.analog[i])
            elif wpMatch in lbl:
                pvChannels[pv]['wp'] = np.array (rec.analog[i])
            elif angMatch in lbl:
                pvChannels[pv]['ang'] = np.array (rec.analog[i])
            elif vMatch in lbl:
                pvChannels[pv]['Vmag'] = np.array (rec.analog[i])
            elif iMatch in lbl:
                pvChannels[pv]['Imag'] = np.array (rec.analog[i])
        if 'FDR  A' in lbl:
            feederChannels['Ia'] = np.array (rec.analog[i])
        elif 'FDR  B' in lbl:
            feederChannels['Ib'] = np.array (rec.analog[i])
        elif 'FDR  C' in lbl:
            feederChannels['Ic'] = np.array (rec.analog[i])
        if 'FAULTA' in lbl:
            faultChannels['Ia'] = np.array (rec.analog[i])
        elif 'FAULTB' in lbl:
            faultChannels['Ib'] = np.array (rec.analog[i])
        elif 'FAULTC' in lbl:
            faultChannels['Ic'] = np.array (rec.analog[i])
    elif 'V-branch' in lbl:
        for pv in pvnames:
            if pv+'A' in lbl:
                pvChannels[pv]['Va'] = np.array (rec.analog[i])
            elif pv+'B' in lbl:
                pvChannels[pv]['Vb'] = np.array (rec.analog[i])
            elif pv+'C' in lbl:
                pvChannels[pv]['Vc'] = np.array (rec.analog[i])

nrows = 2 + npv
#print (pvnames)
#for pv in pvnames:
#    print (pvChannels[pv])

#quit()
fig, ax = plt.subplots(nrows, 2, sharex = 'col', figsize=(8,2*nrows), constrained_layout=True)
fig.suptitle ('Case ' + atp_base)

ax[0,0].set_title ('Feeder Current')
ax[0,0].set_ylabel ('kA')
ax[0,0].plot(t, 0.001 * feederChannels['Ia'], label='A', color='r')
ax[0,0].plot(t, 0.001 * feederChannels['Ib'], label='B', color='g')
ax[0,0].plot(t, 0.001 * feederChannels['Ic'], label='C', color='b')
ax[0,0].grid()

ax[0,1].set_title ('Feeder Voltage')
ax[0,1].set_ylabel ('kV')
ax[0,1].plot(t, 0.001 * feederChannels['Va'], label='A', color='r')
ax[0,1].plot(t, 0.001 * feederChannels['Vb'], label='B', color='g')
ax[0,1].plot(t, 0.001 * feederChannels['Vc'], label='C', color='b')
ax[0,1].grid()

ax[1,0].set_title ('Fault Current')
ax[1,0].set_ylabel ('kA')
ax[1,0].plot(t, 0.001 * faultChannels['Ia'], label='A', color='r')
ax[1,0].plot(t, 0.001 * faultChannels['Ib'], label='B', color='g')
ax[1,0].plot(t, 0.001 * faultChannels['Ic'], label='C', color='b')
ax[1,0].grid()

ax[1,1].set_title ('FLL Frequency')
ax[1,1].set_ylabel ('rad/s')
for pv in pvnames:
    ax[1,1].plot(t, pvChannels[pv]['wp'], label=pv)
ax[1,1].grid()
ax[1,1].legend()

i = 2
for pv in pvnames:
    ax[i,0].set_title (pv + ' Current')
    ax[i,0].set_ylabel ('kA')
    ax[i,0].plot(t, 0.001 * pvChannels[pv]['Ia'], label='A', color='r')
    ax[i,0].plot(t, 0.001 * pvChannels[pv]['Ib'], label='B', color='g')
    ax[i,0].plot(t, 0.001 * pvChannels[pv]['Ic'], label='C', color='b')
    ax[i,0].grid()

    ax[i,1].set_title (pv + ' Voltage')
    ax[i,1].set_ylabel ('kV')
    ax[i,1].plot(t, 0.001 * pvChannels[pv]['Va'], label='A', color='r')
    ax[i,1].plot(t, 0.001 * pvChannels[pv]['Vb'], label='B', color='g')
    ax[i,1].plot(t, 0.001 * pvChannels[pv]['Vc'], label='C', color='b')
    ax[i,1].grid()

    i += 1

ax[nrows-1,0].set_xlabel ('Seconds')
ax[nrows-1,1].set_xlabel ('Seconds')

if len(png_name) > 0:
    plt.savefig(png_name)
else:
    plt.show()
