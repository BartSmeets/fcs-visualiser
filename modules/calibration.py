# Imports
import numpy as np
import pandas as pd
import scipy.signal as signal
from scipy.optimize import fsolve, minimize
from scipy import sparse
from scipy.sparse.linalg import spsolve


class load_data:
    '''
    Class that handles the data

    Provides intuitive access to the different axes and properties (e.g. self.time instead of data[:, 0])
    '''

    def __init__(self, file, init_param):
        '''
        Load the data and perform a first calibration

        ### ARGUMENTS:
        - file: path to the data file that will be loaded
        - lam: smoothness parameter for baseline correction
        - 
        '''

        # Read data
        self.file = file
        load = np.load(file)
        #load = np.loadtxt(file, delimiter=',', skiprows=1, usecols=(1, 2))
        time = load[:, 0] * 1e6    # us
        self.voltage = -load[time>=0, 1]
        self.time = time[time>=0]
        self.calibrate(*init_param)
        
        return


    def calibrate(self, G, t_off):
        '''
        Performs a mass calibration, i.e., convert the time axis into a mass axis

        ### ARGUMENTS:
        - G: First order coefficient of the Taylor expansion
        - t_off: Time offset <- Inability to locate the exact extraction timing
        '''
        self.mass = G * (self.time - t_off)**2
        return

    
    def baseline_correction(self, lam=1e9, multiplier=1, baseline_data=None):
        # Baseline correction
        if baseline_data != None:
            def LSS(y, lam):
                '''
                Least Squares Smoothing
                '''
                size = len(y)
                D = sparse.diags([1, -2, 1], [0, -1, -2], shape=(size, size-2))   # Second order difference matrix
                D = lam * D.dot(D.transpose())
                I = sparse.identity(size)
                z = spsolve(I + D, y)
                return z
            
            baseline = np.load(baseline_data)
            baseline = -multiplier * baseline[time>=0, 1]
            self.baseline = LSS(baseline, lam)  # Smoothen Baseline Measurement
            self.voltage = self.voltage - self.baseline
            return