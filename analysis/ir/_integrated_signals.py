import numpy as np
import streamlit as st
from scipy.integrate import trapezoid
from scipy.signal import find_peaks

from app.state import AppState

from .._load_data import Data


def get_integrated_signals(spec, mass_axis, target_mass,
                            search_window=0.5, max_half_width=50):
    """
    Locate and integrate a targeted peak across all wave/scan rows.
    Replacement for miooms.get_integrated_signals_dataframe.

    Parameters
    ----------
    spec : ndarray, shape (n_waves, n_mass_points)
        Mass spectra, one row per IR wavelength/scan.
    mass_axis : ndarray, shape (n_mass_points,)
        Mass axis shared by all rows in `spec`.
    target_mass : float
        Expected mass position of the peak.
    boxcar : int, optional
        Boxcar-average window (points) applied to each row before peak
        finding/integration. 1 = no smoothing.
    search_window : float, optional
        +/- tolerance (mass units) around `target_mass` for the apex search.
    max_half_width : int, optional
        Cap (points) on how far integration bounds may extend from apex.

    Returns
    -------
    integrated : ndarray, shape (n_waves,)
        Integrated peak area per wave. NaN where no peak was found.
    apex_mass : ndarray, shape (n_waves,)
        Located apex mass per wave. NaN where no peak was found.

    Raises
    ------
    ValueError
        If the target mass is not found in ANY wave.

    """
    n_waves = spec.shape[0]
    integrated = np.full(n_waves, np.nan)
    apex_mass = np.full(n_waves, np.nan)

    for i in range(n_waves):
        y = spec[i, :]  # Spectrum at a given wavenumber

        # Design mask for search/integration window
        mask = (mass_axis >= target_mass - search_window) & \
               (mass_axis <= target_mass + search_window)
        if not np.any(mask):
            continue

        # Find true peak corresponding to target
        idx_range = np.where(mask)[0]
        y_local = y[idx_range]
        peaks, props = find_peaks(y_local, prominence=max(np.ptp(y_local) * 0.02, 1e-12))
        if len(peaks) == 0:
            apex_local = np.argmax(y_local)
        else:
            apex_local = peaks[np.argmax(props["prominences"])]
        apex_idx = idx_range[apex_local]

        # Walk outward to half max for integration bounds
        left = apex_idx
        while (left > 0
               and left > apex_idx - max_half_width
               and y[left] > y[apex_idx]/2):
            left -= 1

        right = apex_idx
        imax = len(y)
        while (right < imax - 1
               and right < apex_idx + max_half_width
               and y[right] > y[apex_idx]):
            right += 1

        integrated[i] = trapezoid(y[left:right + 1], mass_axis[left:right + 1])
        apex_mass[i] = mass_axis[apex_idx]

    if np.all(np.isnan(integrated)):
        raise ValueError(f"target mass {target_mass} not found in any wave")

    return integrated, apex_mass


def integrated_signals(state: AppState, targets: list, window: float, max_half_width: int):
    """
    Integrate the IR on and off signals at given mass positions.
    Careful, with and without IR is related to the configuration of the scopes!

    First, the FCS data is converted into the shape that an import from FELIX's `.h5` files would be.
    Then, `get_integrated_signals` locates the (possibly shifted) peak apex for each
    target mass and integrates it, per wave, for both the IR-on and IR-off spectra.

    Parameters
    ----------
    state: AppState
        AppState containing at least `files_df`, `a` and `k`
    targets: list
        List or array containing the mass coordinates of the peaks that you want to integrate
    window: float
        Full width of the search window
    max_half_width: int
        Maximum number of datapoints for finding the half maximum

    Returns
    -------
    ioff: Array, shape=(len(targets), n_waves)
        Array containing the integrated signals without IR
    ion: Array, shape=(len(targets), n_waves)
        Array containing the integrated signals with IR

    """
    df = state.files_df
    wavelengths = sorted(df.wave.unique())
    n_waves = len(wavelengths)

    lookup = (
        df[df["onoff"].isin(["ir", "noir"])]
        .drop_duplicates(subset=["wave", "onoff"], keep="first")
        .set_index(["wave", "onoff"])["file"]
        .to_dict()
    )

    progress = st.progress(0)

    spec_off = spec_on = None
    data_on = data_off = None

    # Build datastructure
    ## This was previously to match FELIX's datastructure since I wrapped their solver.
    ## Now it may not be neccessary anymore, but don't know don't care
    for i, wave in enumerate(wavelengths):
        progress.progress((i + 1) / n_waves)

        on_filename = lookup[(wave, "ir")]
        off_filename = lookup[(wave, "noir")]

        data_on = Data(on_filename, [state.a, state.k])
        data_off = Data(off_filename, [state.a, state.k])

        if spec_off is None:
            spec_off = np.zeros((n_waves, len(data_off.mass)))
            spec_on = np.zeros((n_waves, len(data_on.mass)))

        spec_off[i, :] = data_off.voltage
        spec_on[i, :] = data_on.voltage

    # Integrate
    ioff = np.full((len(targets), n_waves), np.nan)
    ion = np.full((len(targets), n_waves), np.nan)
    for i, mass in enumerate(targets):
        try:
            ioff[i, :], _ = get_integrated_signals(
                spec_off, data_off.mass, mass,
                search_window=window/2, max_half_width=max_half_width)
            ion[i, :], _ = get_integrated_signals(
                spec_on, data_on.mass, mass,
                search_window=window/2, max_half_width=max_half_width)
        except ValueError:
            print(f"{mass} does not exist")

    return ioff, ion