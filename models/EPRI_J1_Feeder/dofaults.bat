@echo off
if %1% EQU 1 (
rem TOC without PV
python -c "fp=open('setnumber.inc','w');print('set number=5000',file=fp);fp.close()"
copy /y buslist_nopv.dat buslist.dat
python ..\code\ScalePV.py 0 1
copy /y TOCRelays.dss UtilityRelays.dss
)

if %1% EQU 2 (
rem TOC with 100% PV
python -c "fp=open('setnumber.inc','w');print('set number=30000',file=fp);fp.close()"
copy /y buslist_toc.dat buslist.dat
python ..\code\ScalePV.py 1.0 3
copy /y TOCRelays.dss UtilityRelays.dss
)

if %1% EQU 7 (
rem TOC with 100% PV
python -c "fp=open('setnumber.inc','w');print('set number=5000',file=fp);fp.close()"
copy /y buslist_toc.dat buslist.dat
python ..\code\ScalePV.py 1.0 2
copy /y TOCRelays.dss UtilityRelays.dss
)

if %1% EQU 8 (
rem TOC with 100% PV
python -c "fp=open('setnumber.inc','w');print('set number=5000',file=fp);fp.close()"
copy /y buslist_toc.dat buslist.dat
python ..\code\ScalePV.py 1.0 1
copy /y TOCRelays.dss UtilityRelays.dss
)

if %1% EQU 3 (
rem Distance without PV
python -c "fp=open('setnumber.inc','w');print('set number=5000',file=fp);fp.close()"
copy /y buslist_nopv.dat buslist.dat
python ..\code\ScalePV.py 0 1
copy /y DistanceRelays.dss UtilityRelays.dss
)

if %1% EQU 4 (
rem Distance with 100% PV
python -c "fp=open('setnumber.inc','w');print('set number=30000',file=fp);fp.close()"
copy /y buslist_dist.dat buslist.dat
python ..\code\ScalePV.py 1.0 3
copy /y DistanceRelaysPV.dss UtilityRelays.dss
)

if %1% EQU 5 (
rem TD21 without PV
python -c "fp=open('setnumber.inc','w');print('set number=5000',file=fp);fp.close()"
copy /y buslist_nopv.dat buslist.dat
python ..\code\ScalePV.py 0 1
copy /y TD21Relays.dss UtilityRelays.dss
)

if %1% EQU 6 (
rem TD21 with 100% PV
python -c "fp=open('setnumber.inc','w');print('set number=30000',file=fp);fp.close()"
copy /y buslist_dist.dat buslist.dat
python ..\code\ScalePV.py 1.0 3
copy /y TD21RelaysPV.dss UtilityRelays.dss
)

python ..\code\runfaults.py J1

type events.out

python ..\code\RelayPerformance.py