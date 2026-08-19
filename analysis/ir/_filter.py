"""
Filter the stable and physical signals.

"""
import numpy as np

from app.state import AppState


def filter(state: AppState, m_threshold: float, cv_threshold: float):
    """
    Filter the stable and physical signals, based on thresholds.

    The target masses are masked twice:
    1) to remove nans `nan_mask`
    2) to guarantee stability `cv_mask`, 
        which looks at the signal intensity
        and the std / intensity ratio

    Parameters
    ----------
    state: AppState
        AppState containing at least `ioff`, `ion` and `target_masses`
    m_threshold: float
        minimum signal intensity (of the integral)
    cv_threshold: float
        maximum ratio of std / mean

    Returns
    -------
    valid_masses: ndarray
        array of the masses that pass the filter    
    
    """
    used_masses = np.asarray(state.target_masses)
    nan_mask = (~np.isnan(state.ioff).any(axis=1) & ~np.isnan(state.ioff).any(axis=1))
    valid_masses = used_masses[nan_mask]

    cv = np.std(state.ioff[nan_mask], axis=1)/np.mean(state.ioff[nan_mask], axis=1)
    print("cv", cv)        
    cv_mask = (np.mean(state.ioff[nan_mask], axis=1) > m_threshold) & (cv < cv_threshold)
    print("cv after mask", valid_masses[cv_mask])

    valid_masses = valid_masses[cv_mask]
    return valid_masses