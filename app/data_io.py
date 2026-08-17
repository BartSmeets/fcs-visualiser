"""Data loading and saving for the FCS Visualiser.
 
Functions here take an AppState instance explicitly rather than reaching into
st.session_state, which keeps them testable outside of a running Streamlit
session (e.g. construct an AppState and call gen_df(state) in plain pytest).
"""
 
import glob
import os

import pandas as pd
import streamlit as st

from analysis import Data

from .state import AppState

FILE_EXTENSION = "*.npy"


def list_data_files(directory: str) -> list[str]:
    """Return full paths of all data files in `directory`."""
    return glob.glob(os.path.join(directory, FILE_EXTENSION))


def basename(path: str) -> str:
    return os.path.basename(path)


def full_path(state: AppState, name: str) -> str:
    """Rebuild a full path from a filename shown in the UI."""
    return os.path.join(state.directory, name)


def gen_df(state: AppState) -> None:
    """Rebuild state.dataframe from the currently selected files."""
    init_param = [state.a, state.k]
    rows = []
 
    for name in state.data:
        path = full_path(state, name)
        try:
            data = Data(path, init_param)
        except OSError:
            st.warning(f"Could not read '{name}' — skipping.")
            continue
 
        df = pd.DataFrame(
            {
                "time": data.time,
                "mass": data.mass,
                "voltage": data.voltage,
                "name": [name] * len(data.time),
            }
        )
 
        if state.baseline is not None:
            data.baseline_correction(state.lam, state.multiplier, state.baseline)
            df["baseline"] = data.baseline
 
        rows.append(df)
 
    state.dataframe = (
        pd.concat(rows, ignore_index=True)
        if rows
        else pd.DataFrame({"time": [], "mass": [], "voltage": [], "name": []})
    )