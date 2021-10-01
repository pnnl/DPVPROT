# Copyright (C) 2018-2021 Battelle Memorial Institute
# file: T400L.py
""" Represents the T400L relay data and functions

Paragraph.
for official use only

Public Functions:
    :main: description
"""

import sys
from comtrade import Comtrade
import numpy as np
import math
from scipy import signal

class T400L:
    def __init__(self):
        # factory default settings
        self.VMIN=0.03           # overcurrent minimum pickup, eq. 2.8
        self.VSTARTP = 15.0      # starting threshold for the 3 phase and 3 ground loops
        self.VSTARTG = self.VSTARTP / math.sqrt(3.0)
        self.VSTARTF = 1.1       # for the margin, mentioned below eq. 2.1 of the manual, Zx=VSTARTF*Z1MAG
        self.rest_offset = 100.0 # creates offset on TD32 restraining torque, paragraph below figure 2.9
        self.secmarg_oc = 0.004  # security margin for OC21, figure 2.16
        self.spu = 1.0           # used to pass spu*RPP or spu*RPG for TD21
        self.start_thresh = 0.001
        self.FID_WINDOW = 0.002  # the time after first START when we consider changing the fault type
        self.VST_THRESH = 0.95   # used to accept faulted phase identifications after the predominant one
        self.RAW_THRESH = 0.95   # used to accept faulted phase identifications after the predominant one
        # relay settings from Comtrade HDR files
        self.CTRW=80
        self.CTRX=80
        self.PTR=300.00
        self.VNOM=115
        self.Z1MAG=3.72
        self.Z1ANG=73.10
        self.Z0MAG=2.21
        self.Z0ANG=67.70
        self.LL=10.00
        self.TWLPT=55.00
        self.XC=0.00
        self.TP50P=0.30
        self.TD32ZF=0.20
        self.TD32ZR=0.20
        self.TD21MP=0.70
        self.TD21MG=0.65
        self.TP67P=0.30
        self.TP67G=0.30
        self.q46_pu=0.10
        self.q47_pu=0.10
        self.NFREQ=60.0

        self.haveDigitalOutputs = False

    def update_settings (self, dict):
        for key,val in dict.items():
            if key in dir(self):
                setattr (self, key, val)
            else:
                print ('Setting {:s} not found in T400L'.format (key))

    def make_td21_rt (self, VLOOP, ILOOP, ncy, m):
        vdel = VLOOP - m * self.Z1MAG * ILOOP
        vr = np.zeros (vdel.size)
        vr[ncy:] = vdel[:-ncy]
        return vr

    def make_td21_trip (self, OP, RT, VT):
        condition_1 = np.ones(OP.size) * (np.absolute(OP) > np.absolute(RT))
        condition_2 = np.ones(OP.size) * (np.sign(OP * RT) < 0)
        condition_3 = np.ones(OP.size) * (np.absolute(OP) > np.absolute(VT))
        return np.logical_and (condition_1, np.logical_and (condition_2, condition_3))

    def supervise_21_trip (self, P21, P32, POC):
        return np.logical_and (P21, np.logical_and (P32, POC))

    def construct_relay_model (self):
        # restrain thresholds
        self.RPP = self.VNOM * math.sqrt(2.0) * np.ones(self.npt)
        self.RPG = self.VNOM * math.sqrt(2.0/3.0) * np.ones(self.npt)
        # predicting the starting voltages and times
        self.VSTAG = np.absolute(self.DVA) + self.VSTARTF * self.Z1MAG * np.absolute(self.DIZA0)
        self.VSTBG = np.absolute(self.DVB) + self.VSTARTF * self.Z1MAG * np.absolute(self.DIZB0)
        self.VSTCG = np.absolute(self.DVC) + self.VSTARTF * self.Z1MAG * np.absolute(self.DIZC0)
        self.VSTAB = np.absolute(self.DVAB) + self.VSTARTF * self.Z1MAG * np.absolute(self.DIZAB)
        self.VSTBC = np.absolute(self.DVBC) + self.VSTARTF * self.Z1MAG * np.absolute(self.DIZBC)
        self.VSTCA = np.absolute(self.DVCA) + self.VSTARTF * self.Z1MAG * np.absolute(self.DIZCA)
        # predict the loop starting signals
        self.PSTAG = np.ones(self.npt) * (self.VSTAG > self.VSTARTG)
        self.PSTBG = np.ones(self.npt) * (self.VSTBG > self.VSTARTG)
        self.PSTCG = np.ones(self.npt) * (self.VSTCG > self.VSTARTG)
        self.PSTAB = np.ones(self.npt) * (self.VSTAB > self.VSTARTP)
        self.PSTBC = np.ones(self.npt) * (self.VSTBC > self.VSTARTP)
        self.PSTCA = np.ones(self.npt) * (self.VSTCA > self.VSTARTP)
        # predict the overall START signal
        istarts = [np.argmax(self.PSTAG > 0),
                   np.argmax(self.PSTBG > 0),
                   np.argmax(self.PSTCG > 0),
                   np.argmax(self.PSTAB > 0),
                   np.argmax(self.PSTBC > 0),
                   np.argmax(self.PSTCA > 0)]
        idx1 = self.npt - self.ncy - 1
        for idx in istarts:
            if (idx > 0) and (idx < idx1):
                idx1 = idx
        idx2 = idx1 + self.ncy
#        print (istarts, idx1, idx2)
#        print ('START active from {:.4f}s to {:.3f}s'.format (self.t[idx1], self.t[idx2]))
        self.PSTART = np.zeros (self.npt)
        self.PSTART[idx1:idx2] = 1
        # suppress the starting signals outside of the one-cycle window
        self.PSTAG = self.PSTAG * self.PSTART
        self.PSTBG = self.PSTBG * self.PSTART
        self.PSTCG = self.PSTCG * self.PSTART
        self.PSTAB = self.PSTAB * self.PSTART
        self.PSTBC = self.PSTBC * self.PSTART
        self.PSTCA = self.PSTCA * self.PSTART

        # calculate the raw TD32 operating quantities early, to (future) assist in fault identification as the manual describes
        self.RAW32AG=-self.DVA*self.DIZA0
        self.RAW32BG=-self.DVB*self.DIZB0
        self.RAW32CG=-self.DVC*self.DIZC0
        self.RAW32AB=-self.DVAB*self.DIZAB
        self.RAW32BC=-self.DVBC*self.DIZBC
        self.RAW32CA=-self.DVCA*self.DIZCA
        self.RAW32MAX = np.maximum(self.RAW32AG, np.maximum(self.RAW32BG, np.maximum(self.RAW32CG, np.maximum(self.RAW32AB, np.maximum(self.RAW32BC, self.RAW32CA)))))
        raw_thresh = self.RAW_THRESH * self.RAW32MAX

        # perform a fault identification based on starting signals
        # for now, choose fault type based on comparing VSTART operating quantities to the highest of them,
        #  and disable any changes after an adjustable time, FID_WINDOW
        self.PFSAG = np.zeros(self.npt)
        self.PFSBG = np.zeros(self.npt)
        self.PFSCG = np.zeros(self.npt)
        self.PFSAB = np.zeros(self.npt)
        self.PFSBC = np.zeros(self.npt)
        self.PFSCA = np.zeros(self.npt)
        self.VSTMAX = np.maximum(self.VSTAG, np.maximum(self.VSTBG, np.maximum(self.VSTCG, np.maximum(self.VSTAB, np.maximum(self.VSTBC, self.VSTCA)))))
        vst_thresh = self.VST_THRESH * self.VSTMAX
        FSAG = 0.0
        FSBG = 0.0
        FSCG = 0.0
        FSAB = 0.0
        FSBC = 0.0
        FSCA = 0.0
        idxWindow = idx1 + round(self.FID_WINDOW / self.dt)
        print ('FID idx1={:d}, idx2={:d}, idxWindow={:d}, FID_WINDOW={:.6f}, dt={:.6f}'.format (idx1, idx2, idxWindow, self.FID_WINDOW, self.dt))
        for i in range(idx1, idx2+1):  # FS can only be positive while START is positive
            if i < idxWindow:
                if self.PSTAG[i] > 0.0 and self.VSTAG[i] >= vst_thresh[i]:
                    FSAG = 1.0
                if self.PSTBG[i] > 0.0 and self.VSTBG[i] >= vst_thresh[i]:
                    FSBG = 1.0
                if self.PSTCG[i] > 0.0 and self.VSTCG[i] >= vst_thresh[i]:
                    FSCG = 1.0
                if self.PSTAB[i] > 0.0 and self.VSTAB[i] >= vst_thresh[i]:
                    FSAB = 1.0
                if self.PSTBC[i] > 0.0 and self.VSTBC[i] >= vst_thresh[i]:
                    FSBC = 1.0
                if self.PSTCA[i] > 0.0 and self.VSTCA[i] >= vst_thresh[i]:
                    FSCA = 1.0
            self.PFSAG[i] = FSAG
            self.PFSBG[i] = FSBG
            self.PFSCG[i] = FSCG
            self.PFSAB[i] = FSAB
            self.PFSBC[i] = FSBC
            self.PFSCA[i] = FSCA

        ########## TD32 Equations for SynchroWave Event, but use predicted instead of actual FSAG
        ########## TD32A
        print ('rest_offset', self.rest_offset)
        self.TD32OA=self.RAW32AG*self.PFSAG
        self.TD32RFA=(self.rest_offset + self.DIZA0*self.DIZA0*self.TD32ZF)*self.PSTART
        self.TD32RRA=(-self.rest_offset - self.DIZA0*self.DIZA0*self.TD32ZR)*self.PSTART
        ##########  TD32B
        self.TD32OB=self.RAW32BG*self.PFSBG
        self.TD32RFB=(self.rest_offset + self.DIZB0*self.DIZB0*self.TD32ZF)*self.PSTART
        self.TD32RRB=(-self.rest_offset - self.DIZB0*self.DIZB0*self.TD32ZR)*self.PSTART
        ##########  TD32C
        self.TD32OC=self.RAW32CG*self.PFSCG
        self.TD32RFC=(self.rest_offset + self.DIZC0*self.DIZC0*self.TD32ZF)*self.PSTART
        self.TD32RRC=(-self.rest_offset - self.DIZC0*self.DIZC0*self.TD32ZR)*self.PSTART
        ##########  self.TD32AB
        self.TD32OAB=self.RAW32AB*self.PFSAB
        self.TD32RFAB=(self.rest_offset + self.DIZAB*self.DIZAB*self.TD32ZF)*self.PSTART
        self.TD32RRAB=(-self.rest_offset - self.DIZAB*self.DIZAB*self.TD32ZR)*self.PSTART
        ##########  self.TD32BC
        self.TD32OBC=self.RAW32BC*self.PFSBC
        self.TD32RFBC=(self.rest_offset + self.DIZBC*self.DIZBC*self.TD32ZF)*self.PSTART
        self.TD32RRBC=(-self.rest_offset - self.DIZBC*self.DIZBC*self.TD32ZR)*self.PSTART
        ##########  self.TD32CA
        self.TD32OCA=self.RAW32CA*self.PFSCA
        self.TD32RFCA=(self.rest_offset + self.DIZCA*self.DIZCA*self.TD32ZF)*self.PSTART
        self.TD32RRCA=(-self.rest_offset - self.DIZCA*self.DIZCA*self.TD32ZR)*self.PSTART

        ##########  self.TD21 Equations for SynchroWave Event
        ##########  Operate for AG, BG, CG Loops
        self.TD21OAG=(self.DVA-self.DIZA0*self.TD21MG*self.Z1MAG)*self.PFSAG  # was PSTAG, etc.
        self.TD21OBG=(self.DVB-self.DIZB0*self.TD21MG*self.Z1MAG)*self.PFSBG
        self.TD21OCG=(self.DVC-self.DIZC0*self.TD21MG*self.Z1MAG)*self.PFSCG
        ##########  Operate for AB, BC, CA Loops
        self.TD21OAB=(self.DVAB-self.DIZAB*self.TD21MP*self.Z1MAG)*self.PFSAB
        self.TD21OBC=(self.DVBC-self.DIZBC*self.TD21MP*self.Z1MAG)*self.PFSBC
        self.TD21OCA=(self.DVCA-self.DIZCA*self.TD21MP*self.Z1MAG)*self.PFSCA

        # construct the TD21 restraint and tripping quantities
        self.TD21RAB = self.make_td21_rt (self.VAB, self.IAB, self.ncy, self.TD21MP)
        self.TD21RBC = self.make_td21_rt (self.VBC, self.IBC, self.ncy, self.TD21MP)
        self.TD21RCA = self.make_td21_rt (self.VCA, self.ICA, self.ncy, self.TD21MP)
        self.TD21RAG = self.make_td21_rt (self.VA, self.IA0, self.ncy, self.TD21MG)
        self.TD21RBG = self.make_td21_rt (self.VB, self.IB0, self.ncy, self.TD21MG)
        self.TD21RCG = self.make_td21_rt (self.VC, self.IC0, self.ncy, self.TD21MG)
        self.P21AB = self.make_td21_trip (self.TD21OAB, self.TD21RAB, self.spu*self.RPP)
        self.P21BC = self.make_td21_trip (self.TD21OBC, self.TD21RBC, self.spu*self.RPP)
        self.P21CA = self.make_td21_trip (self.TD21OCA, self.TD21RCA, self.spu*self.RPP)
        self.P21AG = self.make_td21_trip (self.TD21OAG, self.TD21RAG, self.spu*self.RPG)
        self.P21BG = self.make_td21_trip (self.TD21OBG, self.TD21RBG, self.spu*self.RPG)
        self.P21CG = self.make_td21_trip (self.TD21OCG, self.TD21RCG, self.spu*self.RPG)

        # integrating the TD32 operating and restraining torques
        self.I32OA = self.dt * np.cumsum (self.TD32OA)
        self.I32OB = self.dt * np.cumsum (self.TD32OB)
        self.I32OC = self.dt * np.cumsum (self.TD32OC)
        self.I32RFA = self.dt * np.cumsum (self.TD32RFA)
        self.I32RFB = self.dt * np.cumsum (self.TD32RFB)
        self.I32RFC = self.dt * np.cumsum (self.TD32RFC)
        self.I32RRA = self.dt * np.cumsum (self.TD32RRA)
        self.I32RRB = self.dt * np.cumsum (self.TD32RRB)
        self.I32RRC = self.dt * np.cumsum (self.TD32RRC)
        self.I32OAB = self.dt * np.cumsum (self.TD32OAB)
        self.I32OBC = self.dt * np.cumsum (self.TD32OBC)
        self.I32OCA = self.dt * np.cumsum (self.TD32OCA)
        self.I32RFAB = self.dt * np.cumsum (self.TD32RFAB)
        self.I32RFBC = self.dt * np.cumsum (self.TD32RFBC)
        self.I32RFCA = self.dt * np.cumsum (self.TD32RFCA)
        self.I32RRAB = self.dt * np.cumsum (self.TD32RRAB)
        self.I32RRBC = self.dt * np.cumsum (self.TD32RRBC)
        self.I32RRCA = self.dt * np.cumsum (self.TD32RRCA)
        # predict the directional signals
        self.P32FAG = np.ones(self.npt) * (self.I32OA > self.I32RFA) * self.PFSAG # PSTART
        self.P32FBG = np.ones(self.npt) * (self.I32OB > self.I32RFB) * self.PFSBG # PSTART
        self.P32FCG = np.ones(self.npt) * (self.I32OC > self.I32RFC) * self.PFSCG # PSTART
        self.P32FAB = np.ones(self.npt) * (self.I32OAB > self.I32RFAB) * self.PFSAB # PSTART
        self.P32FBC = np.ones(self.npt) * (self.I32OBC > self.I32RFBC) * self.PFSBC # PSTART
        self.P32FCA = np.ones(self.npt) * (self.I32OCA > self.I32RFCA) * self.PFSCA # PSTART
        self.P32RAG = np.ones(self.npt) * (self.I32OA < self.I32RRA) * self.PFSAG # PSTART
        self.P32RBG = np.ones(self.npt) * (self.I32OB < self.I32RRB) * self.PFSBG # PSTART
        self.P32RCG = np.ones(self.npt) * (self.I32OC < self.I32RRC) * self.PFSCG # PSTART
        self.P32RAB = np.ones(self.npt) * (self.I32OAB < self.I32RRAB) * self.PFSAB # PSTART
        self.P32RBC = np.ones(self.npt) * (self.I32OBC < self.I32RRBC) * self.PFSBC # PSTART
        self.P32RCA = np.ones(self.npt) * (self.I32OCA < self.I32RRCA) * self.PFSCA # PSTART
        self.P32FA = np.logical_or (np.logical_or (self.P32FAG, self.P32FAB), self.P32FCA)
        self.P32FB = np.logical_or (np.logical_or (self.P32FBG, self.P32FAB), self.P32FBC)
        self.P32FC = np.logical_or (np.logical_or (self.P32FCG, self.P32FBC), self.P32FCA)
        self.P32RA = np.logical_or (np.logical_or (self.P32RAG, self.P32RAB), self.P32RCA)
        self.P32RB = np.logical_or (np.logical_or (self.P32RBG, self.P32RAB), self.P32RBC)
        self.P32RC = np.logical_or (np.logical_or (self.P32RCG, self.P32RBC), self.P32RCA)

        # integrate the overcurrent signal and pickup from self.PSTART
        self.IOCAB = self.dt * np.cumsum(np.absolute(self.DIZAB)*self.PSTART) # self.PSTAB, etc.
        self.IOCBC = self.dt * np.cumsum(np.absolute(self.DIZBC)*self.PSTART)
        self.IOCCA = self.dt * np.cumsum(np.absolute(self.DIZCA)*self.PSTART)
        self.IOCAG = self.dt * np.cumsum(np.absolute(self.DIZA0)*self.PSTART)
        self.IOCBG = self.dt * np.cumsum(np.absolute(self.DIZB0)*self.PSTART)
        self.IOCCG = self.dt * np.cumsum(np.absolute(self.DIZC0)*self.PSTART)
        pup = self.VNOM*self.VMIN/(1-self.TD21MP)/self.Z1MAG
        pug = self.VNOM*self.VMIN/(1-self.TD21MG)/self.Z1MAG/math.sqrt(3.0)
        self.IOCPUP = self.dt * np.cumsum(np.ones(self.npt)*pup*self.PSTART) + self.secmarg_oc
        self.IOCPUG = self.dt * np.cumsum(np.ones(self.npt)*pug*self.PSTART) + self.secmarg_oc
        # predict the OC21 supervision signals
        self.POCAB = np.ones(self.npt) * (self.IOCAB > self.IOCPUP) * self.PSTART
        self.POCBC = np.ones(self.npt) * (self.IOCBC > self.IOCPUP) * self.PSTART
        self.POCCA = np.ones(self.npt) * (self.IOCCA > self.IOCPUP) * self.PSTART
        self.POCAG = np.ones(self.npt) * (self.IOCAG > self.IOCPUG) * self.PSTART
        self.POCBG = np.ones(self.npt) * (self.IOCBG > self.IOCPUG) * self.PSTART
        self.POCCG = np.ones(self.npt) * (self.IOCCG > self.IOCPUG) * self.PSTART

        # predict the supervised TD21 trip signals
        self.S21AB = self.supervise_21_trip (self.P21AB, self.P32FAB, self.POCAB)
        self.S21BC = self.supervise_21_trip (self.P21BC, self.P32FBC, self.POCBC)
        self.S21CA = self.supervise_21_trip (self.P21CA, self.P32FCA, self.POCCA)
        self.S21AG = self.supervise_21_trip (self.P21AG, self.P32FAG, self.POCAG)
        self.S21BG = self.supervise_21_trip (self.P21BG, self.P32FBG, self.POCBG)
        self.S21CG = self.supervise_21_trip (self.P21CG, self.P32FCG, self.POCCG)

    # backfill missing signals for plotting, in the case of 1-MHz COMTRADE data
    def save_signals (self):
        if self.sigs is None:
            self.sigs = {}
        if 'TRIP' not in self.sigs:
            ground_trip = np.logical_or (np.logical_or (self.S21AG, self.S21BG), self.S21CG)
            phase_trip = np.logical_or (np.logical_or (self.S21AB, self.S21BC), self.S21CA)
            self.sigs['TRIP'] = np.logical_or (ground_trip, phase_trip)
        if 'START' not in self.sigs:
            self.sigs['START'] = self.PSTART
            self.sigs['EVNTPKP'] = np.zeros (self.npt)
            self.sigs['FL'] = np.zeros (self.npt)
            self.sigs['ILREMI'] = np.zeros (self.npt)
            self.sigs['VILEMI'] = np.zeros (self.npt)
            self.sigs['TD32FA'] = self.P32FA
            self.sigs['TD32FB'] = self.P32FB
            self.sigs['TD32FC'] = self.P32FC
            self.sigs['TD32RA'] = self.P32RA
            self.sigs['TD32RB'] = self.P32RB
            self.sigs['TD32RC'] = self.P32RC
            self.sigs['OC21AG'] = self.POCAG
            self.sigs['OC21BG'] = self.POCBG
            self.sigs['OC21CG'] = self.POCCG
            self.sigs['OC21AB'] = self.POCAB
            self.sigs['OC21BC'] = self.POCBC
            self.sigs['OC21CA'] = self.POCCA
            self.sigs['TD21AG'] = self.P21AG
            self.sigs['TD21BG'] = self.P21BG
            self.sigs['TD21CG'] = self.P21CG
            self.sigs['TD21AB'] = self.P21AB
            self.sigs['TD21BC'] = self.P21BC
            self.sigs['TD21CA'] = self.P21CA
            # we now try to replicate the fault identification logic
            self.sigs['FSAG'] = self.PFSAG  # was PFSAG, etc.
            self.sigs['FSBG'] = self.PFSBG
            self.sigs['FSCG'] = self.PFSCG
            self.sigs['FSAB'] = self.PFSAB
            self.sigs['FSBC'] = self.PFSBC
            self.sigs['FSCA'] = self.PFSCA
            self.sigs['FS3P'] = np.logical_and (self.PFSAB, np.logical_and (self.PFSBC, self.PFSCA))
            self.sigs['AGFLT'] = self.PSTAG
            self.sigs['BGFLT'] = self.PSTBG
            self.sigs['CGFLT'] = self.PSTCG
            self.sigs['ABFLT'] = self.PSTAB
            self.sigs['BCFLT'] = self.PSTBC
            self.sigs['CAFLT'] = self.PSTCA
            self.sigs['TD21P'] = np.logical_or (self.S21AB, np.logical_or (self.S21BC, self.S21CA))
            self.sigs['TD21G'] = np.logical_or (self.S21AG, np.logical_or (self.S21BG, self.S21CG))
            self.sigs['TD32F'] = np.logical_or (self.P32FA, np.logical_or (self.P32FB, self.P32FC))

    def load_comtrade (self, rec):
        self.t = np.array(rec.time)
        self.dt = self.t[1] - self.t[0]
        self.ncy = int (1 / 60.0 / self.dt + 0.5)
        self.npt = self.t.size

        self.chan = {}  # TODO - should we keep chan and sigs with this object?
        for i in range(rec.analog_count):
            lbl = rec.analog_channel_ids[i]
            ratio = self.PTR
            if 'I' in lbl:
                ratio = self.CTRW
            if 'k' in (rec.cfg.analog_channels[i]).uu:
                ratio /= 1000.0
            self.chan[lbl] = np.array (rec.analog[i]) / ratio
        self.sigs = {}
        if rec.status_count > 0:
            self.haveDigitalOutputs = True
        for i in range(rec.status_count):
            lbl = rec.status_channel_ids[i]
            self.sigs[lbl] = np.array (rec.status[i])

        # loop replica currents and voltages
        if 'DVA' in self.chan:  # 10-kHz data
            self.DVA = self.chan['DVA']
            self.DVB = self.chan['DVB']
            self.DVC = self.chan['DVC']
            self.VA = self.chan['VA']
            self.VB = self.chan['VB']
            self.VC = self.chan['VC']
            self.I0 = (self.chan['IA'] + self.chan['IB'] + self.chan['IC']) / 3.0
            self.IA0 = self.chan['IA']-self.I0
            self.IB0 = self.chan['IB']-self.I0
            self.IC0 = self.chan['IC']-self.I0
            self.DVAB = self.chan['DVA']-self.chan['DVB']
            self.DVBC = self.chan['DVB']-self.chan['DVC']
            self.DVCA = self.chan['DVC']-self.chan['DVA']
            self.VAB = self.chan['VA']-self.chan['VB']
            self.VBC = self.chan['VB']-self.chan['VC']
            self.VCA = self.chan['VC']-self.chan['VA']
            self.DIZAB = self.chan['DIZA']-self.chan['DIZB']
            self.DIZBC = self.chan['DIZB']-self.chan['DIZC']
            self.DIZCA = self.chan['DIZC']-self.chan['DIZA']
            self.IAB = self.chan['IA']-self.chan['IB']
            self.IBC = self.chan['IB']-self.chan['IC']
            self.ICA = self.chan['IC']-self.chan['IA']
            self.DIZA0 = self.chan['DIZA']-self.chan['DIZ0']
            self.DIZB0 = self.chan['DIZB']-self.chan['DIZ0']
            self.DIZC0 = self.chan['DIZC']-self.chan['DIZ0']
        else: # 1-MHz data only has the phase currents and voltages
            q = 65
            tfault = 0.05

            self.VA = self.my_decimate (self.chan['VA'], q) # / self.PTR
#            print ('Decimating 1-MHz data', self.npt, self.ncy, self.dt, self.VA.size)
            self.rs = 256
            self.ncy = self.rs
            self.npt = self.VA.size
            self.dt *= q
            self.t = np.linspace (0.0, self.dt * (self.npt - 1), self.npt)
#            print ('Now at 15.36 kHz', self.npt, self.ncy, self.dt, self.t.size)
            self.VB = self.my_decimate (self.chan['VB'], q) # / self.PTR
            self.VC = self.my_decimate (self.chan['VC'], q) # / self.PTR
            self.IA = self.my_decimate (self.chan['IAW'], q) # / self.CTRW
            self.IB = self.my_decimate (self.chan['IBW'], q) # / self.CTRW
            self.IC = self.my_decimate (self.chan['ICW'], q) # / self.CTRW
            # construct the incremental and replica signals as for ATP
            self.VAB = self.VA - self.VB
            self.VBC = self.VB - self.VC
            self.VCA = self.VC - self.VA
            self.IAB = self.IA - self.IB
            self.IBC = self.IB - self.IC
            self.ICA = self.IC - self.IA
            self.I0 = (self.IA + self.IB + self.IC) / 3.0
            self.IA0 = self.IA - self.I0
            self.IB0 = self.IB - self.I0
            self.IC0 = self.IC - self.I0
            self.make_incremental_signals (tfault)
            # backfill the channels for plotting
            self.chan['DIZA'] = self.DIZA
            self.chan['DIZB'] = self.DIZB
            self.chan['DIZC'] = self.DIZC
            self.chan['DIZ0'] = self.DIZ0
            self.chan['DVA'] = self.DVA
            self.chan['DVB'] = self.DVB
            self.chan['DVC'] = self.DVC

        self.construct_relay_model ()
        self.save_signals ()

    def get_incremental(self, x, lookback, a, b):
        n = x.shape[0]
        d = np.zeros (n)
        for i in range(lookback, n):
            d[i] = x[i] - x[i-lookback]

        y = signal.lfilter (b, a, d)

        return y # d

    def make_incremental_signals(self, tfault):
        td21_cycles = 1
        lookback = td21_cycles * self.rs

        b, a = signal.butter (2, 1.0 / 64.0, btype='lowpass', analog=False)
#        print ('LP', b, a)
        self.DVA = self.get_incremental (self.VA, lookback, a, b)
        self.DVB = self.get_incremental (self.VB, lookback, a, b)
        self.DVC = self.get_incremental (self.VC, lookback, a, b)
        self.DVAB = self.DVA - self.DVB
        self.DVBC = self.DVB - self.DVC
        self.DVCA = self.DVC - self.DVA
#        print ('lookback, DVA size, first, last', lookback, self.DVA.size, self.DVA[0], self.DVA[-1], self.DVA)

        self.DIA = self.get_incremental (self.IA, lookback, a, b)
        self.DIB = self.get_incremental (self.IB, lookback, a, b)
        self.DIC = self.get_incremental (self.IC, lookback, a, b)

        d10 = math.cos(math.radians(self.Z1ANG))
        d11 = math.sin(math.radians(self.Z1ANG)) / 2.0 / math.pi / self.NFREQ
        ddtIa = np.diff (self.DIA, prepend=0.0) / self.dt
        ddtIb = np.diff (self.DIB, prepend=0.0) / self.dt
        ddtIc = np.diff (self.DIC, prepend=0.0) / self.dt

#        print ('DIA size={:d}, ddtIa size={:d}, dt={:.6f}, d10={:.4f}, d11={:.6f}'.format (self.DIA.size, ddtIa.size, self.dt, d10, d11))
        self.DIZA = d10 * self.DIA + d11 * ddtIa
        self.DIZB = d10 * self.DIB + d11 * ddtIb
        self.DIZC = d10 * self.DIC + d11 * ddtIc

        self.DIZAB = self.DIZA - self.DIZB
        self.DIZBC = self.DIZB - self.DIZC
        self.DIZCA = self.DIZC - self.DIZA

        d00 = math.cos(math.radians(self.Z0ANG))
        d01 = math.sin(math.radians(self.Z0ANG)) / 2.0 / math.pi / self.NFREQ
        rat = self.Z0MAG / self.Z1MAG
#        print ('d00={:.4f}, d01={:.6f}, Z0/Z1={:.4f}'.format (d00, d01, rat))
        self.DI0 = (self.DIA + self.DIB + self.DIC) / 3.0
        ddtI0 = np.diff (self.DI0, prepend=0.0) / self.dt
        self.DIZ0 = (d10 - rat * d00) * self.DI0 + (d11 - rat * d01) * ddtI0
        self.DIZA0 = self.DIZA - self.DIZ0
        self.DIZB0 = self.DIZB - self.DIZ0
        self.DIZC0 = self.DIZC - self.DIZ0

    def my_decimate(self, x, q):
        if q == 65:  # downsampling 1 MHz signals to 256 samples per 60-Hz cycle
            return signal.decimate (signal.decimate(x, 5), 13)
        elif q <= 13:
            return signal.decimate (x, q)
        else:
            return signal.decimate (x, q, ftype='fir', n=None)

    def load_atp(self, t, fs, tfault, va, vb, vc, ia, ib, ic):
        self.rs = 256
        self.ncy = self.rs
        fq = fs / self.rs / 60.0
        dt = t[1] - t[0]
        q = int(fq+0.5)
        tstart = tfault - 3.0 / 60
        tend = tfault + 5.0 / 60
        nstart = int(tstart / dt + 0.5)
        nend = int(tend / dt - 0.5)
        twindow = t[nstart:nend]

        # window and downsample the ATP signals, 3 cycles before to 5 cycles after the actual fault time
        self.t = twindow[::q] - tfault
        self.dt = dt * q
        self.npt = self.t.size
        #   print ('{:d} {:d} {:.8f}'.format (self.npt, self.rs, self.dt))
        self.VA = self.my_decimate (va[nstart:nend], q) / self.PTR
        #   print ('t size, first, last', self.t.size, self.t[0], self.t[-1], self.t)
        #   print ('VA size', self.VA.size, self.VA)
        #   print ('{:d} {:f} {:f} {:d} {:f} {:f} {:d} {:d}'.format (self.rs, dt, fq, q, tstart, tend, nstart, nend))
        self.VB = self.my_decimate (vb[nstart:nend], q) / self.PTR
        self.VC = self.my_decimate (vc[nstart:nend], q) / self.PTR
        self.IA = self.my_decimate (ia[nstart:nend], q) / self.CTRW  # doesn't have I0 yet
        self.IB = self.my_decimate (ib[nstart:nend], q) / self.CTRW
        self.IC = self.my_decimate (ic[nstart:nend], q) / self.CTRW

        # process the others
        self.VAB = self.VA - self.VB
        self.VBC = self.VB - self.VC
        self.VCA = self.VC - self.VA
        self.IAB = self.IA - self.IB
        self.IBC = self.IB - self.IC
        self.ICA = self.IC - self.IA
        self.I0 = (self.IA + self.IB + self.IC) / 3.0
        self.IA0 = self.IA - self.I0
        self.IB0 = self.IB - self.I0
        self.IC0 = self.IC - self.I0

        self.make_incremental_signals (tfault)
        self.construct_relay_model ()

