import subprocess
import sys

ckt_name = 'IEEE8500'
src_path = '../code/'

uv_cats = [1, 2, 3]
pv_pcts = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
scale = 0.4

pw0 = subprocess.Popen ('copy /y TOCRelays.dss UtilityRelays.dss', shell=True)
pw0.wait()

for cat in [2, 3]: # uv_cats:
    for pct in pv_pcts:
        if pct == 0:
            pw0 = subprocess.Popen ('copy /y buslist_nopv.dat buslist.dat', shell=True)
        else:
            pw0 = subprocess.Popen ('copy /y buslist_toc.dat buslist.dat', shell=True)
        pw0.wait()
        casetitle = 'pv_{:d}_cat{:d}'.format (pct, cat)
        cmdline1 = 'python CreatePV.py {:.2f} {:.2f} {:d}'.format (float(pct), scale, cat)
        cmdline2 = 'python {:s}runfaults.py {:s}'.format (src_path, ckt_name)
        cmdline3 = 'copy /y events.out {:s}.out'.format (casetitle)
        pw1 = subprocess.Popen (cmdline1, shell=True)
        pw1.wait()
        print ('**************', casetitle)
        pw2 = subprocess.Popen (cmdline2, shell=True)
        pw2.wait()
        pw3 = subprocess.Popen (cmdline3, shell=True)
        pw3.wait()

cat = 3
for pct in pv_pcts:
    if pct == 0:
        pw0 = subprocess.Popen ('copy /y DistanceRelays.dss UtilityRelays.dss', shell=True)
        pw0.wait()
        pw0 = subprocess.Popen ('copy /y buslist_nopv.dat buslist.dat', shell=True)
        pw0.wait()
    else:
        pw0 = subprocess.Popen ('copy /y DistanceRelaysPV.dss UtilityRelays.dss', shell=True)
        pw0.wait()
        pw0 = subprocess.Popen ('copy /y buslist_dist.dat buslist.dat', shell=True)
        pw0.wait()
    casetitle = 'pv_{:d}_cat{:d}_dist'.format (pct, cat)
    cmdline1 = 'python CreatePV.py {:.2f} {:.2f} {:d}'.format (float(pct), scale, cat)
    cmdline2 = 'python {:s}runfaults.py {:s}'.format (src_path, ckt_name)
    cmdline3 = 'copy /y events.out {:s}.out'.format (casetitle)
    pw1 = subprocess.Popen (cmdline1, shell=True)
    pw1.wait()
    print ('**************', casetitle)
    pw2 = subprocess.Popen (cmdline2, shell=True)
    pw2.wait()
    pw3 = subprocess.Popen (cmdline3, shell=True)
    pw3.wait()

