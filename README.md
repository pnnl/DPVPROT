# Distributed Photovoltaic Protection (DPVProt) Modeling Tools

The code package includes several important functions for design and analysis of new grid protection schemes, for scenarios of distributed photovoltaic (DPV) generation approaching 100% of the peak feeder load, i.e., high-penetration DPV.

- Convert distribution feeder models, used by planning engineers, to electromagnetic transient (EMT) models that produce waveforms for advanced relay algorithms.
- Visualize the results of protection scheme operation.
- Tools to determine distance relay settings on distribution systems.
- Tools to predict the performance of time-domain, incremental distance relay algorithms.

## ATP Materials

The Alternative Transients Program (ATP) was used in development of this project. Some of the script files
written to support ATP do not function in the version published to this repository, including:

- AtpLoopCaps.py
- AtpLoopFaults.py
- AtpReduction.py
- CheckReducedFaults.py
- CheckReducedLoads.py
- ConvertPL4.py

Functional versions of these files could be made available to licensed ATP users; 
please ask the [European EMTP Users Group](https://www.emtp.org) for information about ATP licensing.

There are other script files on this repository that make reference to ATP, but they do not disclose ATP Materials.
Examples of this include the use of "ATP" or "Atp" in function names, variable names, or file names. The scripts that
load simulation data from ATP are actually loading files in standard COMTRADE format.

## License

See [License](license.txt)

## Notice

This material was prepared as an account of work sponsored by an agency of the United States Government.  Neither the United States Government nor the United States Department of Energy, nor Battelle, nor any of their employees, nor any jurisdiction or organization that has cooperated in the development of these materials, makes any warranty, express or implied, or assumes any legal liability or responsibility for the accuracy, completeness, or usefulness or any information, apparatus, product, software, or process disclosed, or represents that its use would not infringe privately owned rights.
Reference herein to any specific commercial product, process, or service by trade name, trademark, manufacturer, or otherwise does not necessarily constitute or imply its endorsement, recommendation, or favoring by the United States Government or any agency thereof, or Battelle Memorial Institute. The views and opinions of authors expressed herein do not necessarily state or reflect those of the United States Government or any agency thereof.

    PACIFIC NORTHWEST NATIONAL LABORATORY
                operated by
                 BATTELLE
                 for the
     UNITED STATES DEPARTMENT OF ENERGY
      under Contract DE-AC05-76RL01830

Copyright 2021, Battelle Memorial Institute
