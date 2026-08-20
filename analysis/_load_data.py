import numpy as np
from pybaselines import Baseline

LAM = 1e12

class Data:
    '''
    Class that handles the data

    Provides intuitive access to the different axes and properties (e.g. self.time instead of data[:, 0])
    '''

    def __init__(self, file: str, init_param: list[float, float]):
        """
        Load the data and perform a first calibration

        Parameters
        ----------
        file: str
            File location
        init_param: list
            Initial parameter

        """

        # Read data
        self.file = file
        load = np.load(file)
        #load = np.loadtxt(file, delimiter=',', skiprows=1, usecols=(1, 2))
        time = load[:, 0] * 1e6    # us
        self.voltage = -load[time>=0, 1]
        self.time = time[time>=0]
        self.mass = self.calibrate(*init_param)

        baseline_fitter = Baseline(x_data=self.mass)
        baseline = baseline_fitter.imodpoly(self.voltage, poly_order=3)[0]

        self.voltage -= baseline


    def calibrate(self, G: float, t_off: float):
        """
        Performs a mass calibration, i.e., convert the time axis into a mass axis

        Parameters
        ----------
        G: float
            Coefficient
        t_off: float
            Time offset <- Inability to locate the exact extraction timing
        
        """
        mass = G * (self.time - t_off)**2
        return mass
