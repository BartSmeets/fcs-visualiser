"""
Function to integrate the signals at target masses.

This function wraps the data collection of the FCS to the analysis tools build for FELIX: `miooms.py`

"""
import numpy as np
import streamlit as st

from analysis import miooms
from app.state import AppState

from .._load_data import Data


def integrated_signals(state: AppState, targets: list):
    """
    Integrate the IR on and off signals at given mass positions. 
    Careful, with and without IR is related to the configuration of the scopes!

    Wrapper of `miooms.py`.
    First, the FCS data is converted into the shape that an import from FELIX's `.h5` files would be.
    Then, this data is provided to `miooms`.

    Paramters
    ---------
    state: AppState
        AppState containing at least `files_df`, `a` and `k`
    targets: list
        List or array containing the mass coordinates of the peaks that you want to integrate

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

    # Build an O(1) lookup of {(wave, onoff): filename} once, instead of
    # re-filtering the full dataframe (df[df.wave == wave] + two .loc masks)
    # on every iteration of the loop below.
    lookup = (
        df[df["onoff"].isin(["ir", "noir"])]
        .drop_duplicates(subset=["wave", "onoff"], keep="first")
        .set_index(["wave", "onoff"])["file"]
        .to_dict()
    )

    progress = st.progress(0)

    spec_off = spec_on = None
    data_on = data_off = None  # keep references for .mass after the loop

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
            ioff[i, :], _ = miooms.get_integrated_signals_dataframe(
                spec_off, data_off.mass, mass, False, state.boxcar, "")
            ion[i, :], _ = miooms.get_integrated_signals_dataframe(
                spec_on, data_on.mass, mass, False, state.boxcar, "")
        except UnboundLocalError:
            print(f"{mass} does not exist")

    return ioff, ion