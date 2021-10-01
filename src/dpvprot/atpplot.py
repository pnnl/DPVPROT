# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: atpplot.py
""" Demonstrate plotting 6 channels from ATP-generated COMTRADE file.

Paragraph.

Public Functions:
    :main: does the work
"""

import sys
import matplotlib.pyplot as plt
from comtrade import Comtrade

#print (plt.gcf().canvas.get_supported_filetypes())
#quit()

atp_base = sys.argv[1]

rec = Comtrade()
print (atp_base + '.cfg')
rec.load(atp_base + '.cfg', atp_base + '.dat')
print('Analog', rec.analog_count, rec.analog_channel_ids)
print('Status', rec.status_count, rec.status_channel_ids)
print('File Name', rec.filename) 
print('Station', rec.station_name)
print('N', rec.total_samples)

fig, ax = plt.subplots(1, 1, sharex = 'col')
for i in range(rec.analog_count):
	ax.plot(rec.time, rec.analog[i], label=rec.analog_channel_ids[i][:6])
ax.set_title (rec.station_name)
ax.set_ylabel ('Volts')
ax.set_xlabel ('Seconds')
ax.grid()
ax.legend()
plt.show()
#plt.savefig('test.png')