@echo off
if %1% EQU 1 (
rem TOC without PV
copy /y buslist_nopv.dat buslist.dat
python ..\code\ScalePV.py 0 1
copy /y TOCRelays.dss UtilityRelays.dss
)

if %1% EQU 2 (
rem TOC with 100% PV
copy /y buslist_toc.dat buslist.dat
python ..\code\ScalePV.py 1.0 1
copy /y TOCRelays.dss UtilityRelays.dss
)

if %1% EQU 3 (
rem Distance without PV
copy /y buslist_nopv.dat buslist.dat
python ..\code\ScalePV.py 0 1
copy /y DistanceRelays.dss UtilityRelays.dss
)

if %1% EQU 4 (
rem Distance with 100% PV
copy /y buslist_dist.dat buslist.dat
python ..\code\ScalePV.py 1.0 3
copy /y DistanceRelaysPV.dss UtilityRelays.dss
)

if %1% EQU 5 (
rem TD21 without PV
copy /y buslist_nopv.dat buslist.dat
python ..\code\ScalePV.py 0 1
copy /y TD21Relays.dss UtilityRelays.dss
)

if %1% EQU 6 (
rem TD21 with 100% PV
copy /y buslist_dist.dat buslist.dat
python ..\code\ScalePV.py 1.0 3
copy /y TD21RelaysPV.dss UtilityRelays.dss
)

python ..\code\runfaults.py DgProtFdr

type events.out

python ..\code\RelayPerformance.py