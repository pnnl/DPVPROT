@echo off
if %1% EQU 1 (
rem TOC without PV
python -c "fp=open('setnumber.inc','w');print('set number=1000',file=fp);fp.close()"
copy /y buslist_nopv.dat buslist.dat
copy /y TOCRelays.dss UtilityRelays.dss
python CreatePV.py 0.0 0.4 1
)

if %1% EQU 2 (
rem TOC with 100% PV, cat I
python -c "fp=open('setnumber.inc','w');print('set number=15000',file=fp);fp.close()"
copy /y buslist_toc.dat buslist.dat
copy /y TOCRelays.dss UtilityRelays.dss
python CreatePV.py 100.0 0.4 1
)

if %1% EQU 7 (
rem TOC with 100% PV, cat II
python -c "fp=open('setnumber.inc','w');print('set number=15000',file=fp);fp.close()"
copy /y buslist_toc.dat buslist.dat
copy /y TOCRelays.dss UtilityRelays.dss
python CreatePV.py 100.0 0.4 2
)

if %1% EQU 8 (
rem TOC with 100% PV, cat IIIr
python -c "fp=open('setnumber.inc','w');print('set number=15000',file=fp);fp.close()"
copy /y buslist_toc.dat buslist.dat
copy /y TOCRelays.dss UtilityRelays.dss
python CreatePV.py 100.0 0.4 4
)

if %1% EQU 3 (
rem Distance without PV
python -c "fp=open('setnumber.inc','w');print('set number=5000',file=fp);fp.close()"
copy /y buslist_nopv.dat buslist.dat
copy /y DistanceRelays.dss UtilityRelays.dss
python CreatePV.py 0.0 0.4 1
)

if %1% EQU 4 (
rem Distance with 100% PV, cat II
python -c "fp=open('setnumber.inc','w');print('set number=15000',file=fp);fp.close()"
copy /y buslist_dist.dat buslist.dat
copy /y DistanceRelaysPV.dss UtilityRelays.dss
python CreatePV.py 100.0 0.4 2
)

if %1% EQU 5 (
rem TD21 without PV
python -c "fp=open('setnumber.inc','w');print('set number=5000',file=fp);fp.close()"
copy /y buslist_nopv.dat buslist.dat
copy /y TD21Relays.dss UtilityRelays.dss
python CreatePV.py 0.0 0.4 1
)

if %1% EQU 6 (
rem TD21 with 100% PV, cat II
python -c "fp=open('setnumber.inc','w');print('set number=15000',file=fp);fp.close()"
copy /y buslist_dist.dat buslist.dat
copy /y TD21RelaysPV.dss UtilityRelays.dss
python CreatePV.py 100.0 0.4 2
)

python ..\code\runfaults.py IEEE8500

type events.out

python ..\code\RelayPerformance.py