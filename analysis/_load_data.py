import numpy as np


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
        self.voltage -= np.mean(self.voltage[-100:])
        self.time = time[time>=0]
        self.mass = self.calibrate(*init_param)


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

    # TODO: baseline correction
    # def baseline_correction(self, lam=1e9, multiplier=1, baseline_data=None):
    #     # Baseline correction
    #     if baseline_data != None:
    #         def LSS(y, lam):
    #             '''
    #             Least Squares Smoothing
    #             '''
    #             size = len(y)
    #             D = sparse.diags([1, -2, 1], [0, -1, -2], shape=(size, size-2))   # Second order difference matrix
    #             D = lam * D.dot(D.transpose())
    #             I = sparse.identity(size)
    #             z = spsolve(I + D, y)
    #             return z
            
    #         baseline = np.load(baseline_data)
    #         baseline = -multiplier * baseline[time>=0, 1]
    #         self.baseline = LSS(baseline, lam)  # Smoothen Baseline Measurement
    #         self.voltage = self.voltage - self.baseline
    #         return