# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: Design.py
""" Checking the T400L filter parameters.

For official use only.

Public Functions:
    :main: does the work
"""

import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

fs = 11520 # 1 / 5e-6
fs = 1 / 5e-6
k = 4343

num_s = np.array ([k*k*k*k])
den_s = np.array([1, 4*k, 6*k*k, 4*k*k*k, k*k*k*k])

num_z, den_z = signal.bilinear (num_s, den_s, fs)

print ('fs', fs)
print ('num-s', num_s)
print ('den-s', den_s)
print ('num-z', num_z)
print ('den-z', den_z)

# design the channel filter
#k = 4343
#b_s = np.array ([k*k*k*k])
#a_s = np.array([1, 4*k, 6*k*k, 4*k*k*k, k*k*k*k])
#b_z, a_z = signal.bilinear (b_s, a_s, fs)
#print ('fs', fs)
#print ('b_z', b_z)
#print ('a_z', a_z)

#cb, ca = signal.cheby2 (N=4, rs=5, Wn=300, btype='lowpass', analog=True, output='ba')
#print (cb)
#print (ca)

#num_s = ca
#den_s = cb
#num_z, den_z = signal.bilinear (num_s, den_s, fs)

wz, hz = signal.freqz(num_z, den_z, worN=2048)
ws, hs = signal.freqs(num_s, den_s, worN=fs*wz)

plt.semilogx(wz*fs/(2*np.pi), 20*np.log10(np.abs(hz).clip(1e-15)), label='Digital')
plt.semilogx(wz*fs/(2*np.pi), 20*np.log10(np.abs(hs).clip(1e-15)), label='Analog')
plt.legend()
plt.xlabel('Frequency [Hz]')
plt.ylabel('Magnitude [dB]')
plt.grid()
plt.show()
