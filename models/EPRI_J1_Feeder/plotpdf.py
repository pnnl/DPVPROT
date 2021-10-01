#	Copyright (C) 2021 Battelle Memorial Institute

import numpy as np;
try:
  import matplotlib as mpl;
  import matplotlib.pyplot as plt;
  from matplotlib.pyplot import cm;
except:
  pass

print ('Loading text data')
flt = np.loadtxt ('J1_Mon_flt.csv', delimiter=',', skiprows=1)
fdr = np.loadtxt ('J1_Mon_fdr.csv', delimiter=',', skiprows=1)
xf1 = np.loadtxt ('J1_Mon_pv1xf.csv', delimiter=',', skiprows=1)
xf2 = np.loadtxt ('J1_Mon_pv2xf.csv', delimiter=',', skiprows=1)
xf3 = np.loadtxt ('J1_Mon_pv3xf.csv', delimiter=',', skiprows=1)
xf4 = np.loadtxt ('J1_Mon_pv4xf.csv', delimiter=',', skiprows=1)

print ('Array shapes are', flt.shape, fdr.shape, xf1.shape, xf2.shape, xf3.shape, xf4.shape)

t = flt[:,1]
iflt = flt[:,3]
ifdr = fdr[:,7]
ixf1 = xf1[:,8]
ixf2 = xf2[:,8]
ixf3 = xf3[:,8]
ixf4 = xf4[:,8]

# make a publication-quality plot
lsize = 9
plt.rc('font', family='serif')
plt.rc('xtick', labelsize=lsize)
plt.rc('ytick', labelsize=lsize)
plt.rc('axes', labelsize=lsize)
plt.rc('legend', fontsize=lsize)

pWidth = 5.0
pHeight = pWidth / 1.618
tmin = 0.0
tmax = 0.8
tticks = [0.0, 0.2, 0.4, 0.6, 0.8]

fig, ax = plt.subplots(1, 1, figsize=(pWidth, pHeight), constrained_layout=True)
ax.set_title ('SLGFb in First Zone - Feeder Breaker and Fault')
ax.plot (t, 0.001 * iflt, color='red', linestyle='solid', label='Flt')
ax.plot (t, 0.001 * ifdr, color='black', linestyle='dashed', label='Fdr')
ax.set_ylabel ('Current [kA]')
ax.set_xlim (tmin,tmax)
ax.set_xticks (tticks)
ax.set_xlabel ('Time [s]')
ax.legend (loc='best')
ax.grid()
plt.savefig ('j1caseFdr.pdf', dpi=300)
plt.show()

fig, ax = plt.subplots(1, 1, figsize=(pWidth, pHeight), constrained_layout=True)
ax.set_title ('SLGFb in First Zone - PV High-Side')
ax.plot (t, ixf1, color='green', linestyle='dotted', label='PV1')
ax.plot (t, ixf2, color='black', linestyle='dashed', label='PV2')
ax.plot (t, ixf3, color='red', linestyle='solid', label='PV3')
ax.plot (t, ixf4, color='blue', linestyle='dashdot', label='PV4')
ax.set_ylabel ('Current [A]')
ax.set_xlim (tmin,tmax)
ax.set_xticks (tticks)
ax.set_xlabel ('Time [s]')
ax.legend (loc='best')
ax.grid()
plt.savefig ('j1casePV.pdf', dpi=300)
plt.show()


