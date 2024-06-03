# Imports
import numpy as np
import pandas as pd
import scipy.signal as signal
from scipy.optimize import fsolve, minimize


class load_data:
    '''
    Class that handles the data

    Provides intuitive access to the different axes and properties (e.g. self.time instead of data[:, 0])
    '''

    def __init__(self, file, element, prominence=0.2, baseline_end=True):
        '''
        Load the data and perform a first calibration

        ### ARGUMENTS:
        - file: path to the data file that will be loaded
        - prominence (default=0.2): prominence threshold for the peak detection. \\
            Prominence is the effective height of a peak -> from lowest point to highest point
        - baseline_end (default=True): boolean to choose whether the baseline correction should be calculated from the last data points of the spectrum \\
            This must be set to false if the actual signal reaches the border of the measurment window
        '''
        # Select element and read the mass dictionary
        global ELEMENT, MASS_DICT, MASS_ELEMENT
        ELEMENT = element
        MASS_DICT = np.load('masses.npy', allow_pickle=True).item()
        MASS_ELEMENT = MASS_DICT[ELEMENT + "1-"]

        # Read data
        self.file = file
        load = np.load(file)
        #load = np.loadtxt(file, delimiter=',', skiprows=1, usecols=(1, 2))
        time = load[:, 0] * 1e6    # us
        self.voltage = -load[time>=0, 1]
        self.time = time[time>=0]

        # Find peaks
        self.peaks, properties = signal.find_peaks(self.voltage, prominence=prominence, height=3/4*prominence)
        ## Identify atom and dimer
        ### Prepare local datastructure
        atom = np.zeros(len(self.peaks))
        dimer = np.zeros(len(self.peaks))
        self.calibrate()    # Estimated calibration for identifying the atom and dimer using default parameters
        ### Identify the candidate peaks -> peaks nearby 1 element mass and 2 element masses
        atom_options = np.abs(self.mass_element[self.peaks] - 1) < 0.25
        dimer_options = np.abs(self.mass_element[self.peaks] - 2) < 0.25
        ### Find the corresponding peak prominences
        atom[atom_options] = properties['prominences'][atom_options]
        dimer[dimer_options] = properties['prominences'][dimer_options]
        ### The most prominenent peak is likely the atom or the dimer
        self.atom_peak = self.peaks[atom.argmax()]
        self.dimer_peak = self.peaks[dimer.argmax()]

        # Baseline correction
        number = int(len(self.time)/10)  # Number of data points to consider for the baseline
        baseline = np.average(self.voltage[-number:])
        self.voltage -= baseline
        self.norm = self.voltage / np.sum(self.voltage)

        # Mass calibration based on atom and dimer
        ## Find the exact solution of the system of equations:
        ##  a*(ToF_atom - k)**2 - 1*m_Co = 0
        ##  a*(ToF_dimer - k)**2 - 2*m_Co = 0
        ToF = np.array([self.time[self.atom_peak], self.time[self.dimer_peak]]) # Create time vector
        solve = lambda x: x[0] * (ToF - x[1])**2 - np.array([1., 2.])*MASS_ELEMENT  # Define system of equations
        G, t_off = fsolve(solve, x0=[0.09949062, 0.23745731])
        self.p0 = [G, t_off]
        self.calibrate(G, t_off)
        
        return

    def calibrate(self, G=0.09949062, t_off = 0.23745731):
        '''
        Performs a mass calibration, i.e., convert the time axis into a mass axis

        ### ARGUMENTS:
        - G (default=0.09548259): First order coefficient of the Taylor expansion
        - t_off (default = 0.23805761): Time offset <- Inability to locate the exact extraction timing
        '''
        self.mass = G * (self.time - t_off)**2
        self.mass_element = self.mass / MASS_ELEMENT
        return

    def optimise(self, threshold=0.001):
        '''
        Performs an optimisation routine (minimise Chi^2) to determine the optimal calibration parameters

        ### ARGUMENTS:
        - p0 (default=[0.09548259, 0.23805761]): The initial guess for the calibration parameters
        - threshold (default=0.001): Threshold for ignoring a peak: \\
            Ignoring the peak should improve the chi^2 by more than the threshold
        '''

        def chi2_G(G, t_off, calibration_peaks, calibration_mass):
            '''
            Calibrates the spectrum for the given parameters and calculates the corresponding Chi^2

            ### ARGUMENTS:
            - G: the variable G calibration parameter
            - t_off: The fixed time offset
            - calibration_peaks: the peak indices that will be considered during the optimisation
            - calibration_mass: the target (exact) mass that should correspond to each peak, e.g., the atom peak should have exactly 1*m_element
            '''
            self.calibrate(G, t_off)
            chi2 = np.sum((self.mass[calibration_peaks] - calibration_mass)**2 / calibration_mass)
            return chi2
        
        def chi2_t(t_off, G, calibration_peaks, calibration_mass):
            '''
            Calibrates the spectrum for the given parameters and calculates the corresponding Chi^2

            ### ARGUMENTS:
            - t_off: The variable time offset
            - G: the fixed G calibration parameter
            - calibration_peaks: the peak indices that will be considered during the optimisation
            - calibration_mass: the target (exact) mass that should correspond to each peak, e.g., the atom peak should have exactly 1*m_element

            ### RETURNS:
            - G_opt: the optimal G calibration parameter
            - t_opt: the optimal time offset parameter
            '''
            self.calibrate(G, t_off)
            chi2 = np.sum((self.mass[calibration_peaks] - calibration_mass)**2 / calibration_mass)
            return chi2
        
        # Prepare calibration data
        ## Characterise each peak
        result, _ = self.characterise()
        peak_names = result[:, 0]
        ## Filter the type of cluster used as calibration data
        mask = [name.startswith(ELEMENT) and name.endswith('-') for name in peak_names] # Only the pure clusters
        ## Compile the calibration data
        calibration_mass = [MASS_DICT[x] for x in peak_names[mask]]
        calibration_peaks = self.peaks[mask]

        # Prepare G optimisation
        [G0, t0] = self.p0
        to_del = np.zeros(len(calibration_peaks), dtype=bool)
        opt = minimize(chi2_G, x0=G0, args=(t0, calibration_peaks, calibration_mass))
        benchmark = opt.fun
        G_opt = opt.x
        print('m = a(t-k)^2 \
              \na0 = ' + str(G_opt) + 'u/us2 \
              \nk0 = ' + str(t0) + 'us \
              \n chi2 = ' + str(benchmark))

        # Iteratively delete all peaks and check if it improves the chi2 more than the threshold
        ## If it does, the peak was not well characterised; if not undelete the peak and continue
        to_del = np.zeros(len(calibration_peaks), dtype=bool)
        for i, peak in enumerate(calibration_peaks):
            # Never delete the atom and dimer
            if peak == self.atom_peak or peak == self.dimer_peak:
                continue
            # Delete
            to_del[i] = True
            test_peaks = np.delete(calibration_peaks, to_del)
            test_mass = np.delete(calibration_mass, to_del)
            # Minimise Chi2
            opt = minimize(chi2_G, x0=G_opt, args=(t0, test_peaks, test_mass))
            opt_chi2 = opt.fun
            # Delete or retrieve the peak
            if np.abs(opt_chi2 - benchmark) > threshold:
                print('deleted index: ' + str(i))
                benchmark = opt_chi2    # Update the benchmark
                G_opt = opt.x   # Update the optimal parameter
            else:
                to_del[i] = False

        print('\nAfter \'a\' optimisation \
              \na0 = ' + str(G_opt) + 'u/us2 \
              \nk0 = ' + str(t0) + 'us \
              \n chi2 = ' + str(benchmark) + '\
              \n')
        
        # Fix G and repeat for t_off
        opt = minimize(chi2_t, x0=t0, args=(G_opt, calibration_peaks, calibration_mass))
        benchmark = opt.fun
        t_opt = opt.x
        print('m = a(t-k)^2 \
              \na0 = ' + str(G_opt) + 'u/us2$ \
              \nk0$= ' + str(t_opt) + 'us\
              \n chi2 = ' + str(benchmark) + '\
              \n')

        # Iteratively delete all peaks and check if it improves the chi2 more than the threshold
        ## If it does, the peak was not well characterised; if not undelete the peak and continue
        to_del = np.zeros(len(calibration_peaks), dtype=bool)
        for i, _ in enumerate(calibration_peaks):
            # Never delete the atom and dimer
            if peak == self.atom_peak or peak == self.dimer_peak:
                continue
            # Delete
            to_del[i] = True
            test_peaks = np.delete(calibration_peaks, to_del)
            test_mass = np.delete(calibration_mass, to_del)
            # Minimise Chi2
            opt = minimize(chi2_t, x0=t_opt, args=(G_opt, test_peaks, test_mass))
            opt_chi2 = opt.fun
            # Delete or retrieve the peak
            if np.abs(opt_chi2 - benchmark) > threshold:
                print('deleted index: ' + str(i))
                benchmark = opt_chi2    # Update the benchmark
                t_opt = opt.x   # Update the optimal parameter
            else:
                to_del[i] = False

        print('m = a(t-k)^2 \
              \na0 = ' + str(G_opt) + 'u/us2$ \
              \nk0$= ' + str(t_opt) + 'us \
              \n chi2 = ' + str(benchmark) + '\
              \n')
        
        return G_opt[0], t_opt[0]
    
    def characterise(self, precision=0.01):
        '''
        Characterise the peaks

        ### ARGUMENTS:
        - precision (default = 0.01): the precision with which the measured mass must overlap the actual mass in order to be characterised

        ### RETURNS:
        - matched_elements: array containing the characterised elements corresponding to each peak
        - matched_similarity: array containing the percentile similarity between meased mass and a material. \\
            similarity is defined as m1/m2, where m2>m1
        '''

        # Prepare data structure
        matched_elements = []
        matched_similarity = []
        df = pd.DataFrame()
        df["Mass (amu)"] = self.mass[self.peaks]
        df["Mass"] = self.mass_element[self.peaks]
        df["Time (us)"] = self.time[self.peaks]

        # Check every peak
        for i, peak in enumerate(self.peaks):
            # Calculate the similarity with each material in the mass dictionary
            mass = self.mass[peak]
            similarity = np.minimum(mass, list(MASS_DICT.values())) / np.maximum(mass, list(MASS_DICT.values()))
            # Compare the similarities to the precision
            ## Find best match
            if True in (1-similarity < precision):
                index = similarity.argmax()
                name = list(MASS_DICT.keys())[index]
                matched_elements.append(name)
                matched_similarity.append(similarity[index])
            else:
                matched_elements.append('')
                matched_similarity.append(0)
            ## Add other matches to a general table
            if True in (similarity>(1-precision)):
                # Find all names and similarities where the element is considered a match
                mask = similarity>(1-precision)
                names = np.array(list(MASS_DICT.keys()))[mask]
                similarities = similarity[mask]
                # Sort the similarities: most similar (largest value) first
                sort_index = np.argsort(similarities)[::-1]
                similarities = similarities[sort_index]
                names = names[sort_index]
                # Add to columns
                for j, (n, s) in enumerate(zip(names, similarities)):
                    df.loc[i, 'Element ' + str(j)] = n
                    df.loc[i, "Similarity " + str(j)] = s
        
        # Create a nice dataframe for viewing
        max_result = np.empty((len(self.peaks), 2), dtype=object)
        max_result[:, 0] = matched_elements
        max_result[:, 1] = matched_similarity
        return max_result, df