"""
Application state for the FCS Visualiser

A single AppState instance lives in st.session_state['app_state'] and is passed to functions that need it.

"""

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


def _empty_dataframe() -> pd.DataFrame:
    return pd.DataFrame({"time": [], "mass": [], "voltage": [], "name": []})
 
 
def _empty_figure():
    return px.line([])


@dataclass
class BoxcarSettings:
    bxtype: str = 'width'
    bxwidth: float = 1.0
    bxresmulti: float = 2.0
    bxtolerance: float = 1.0
    showgates: bool = False

    bgtype: str = 'none'
    bgrange: range = range(5000)
    bgoffset: float = -1.2
    bgaverage: bool = False
    bgmultiplier: float = 0.5

    description: str = (
        "Boxcar type: Defines how the integration window around the selected mass is determined.\n"
        "Boxcar width (m/z): Width of the signal integration window used to extract ion intensity.\n\n"
        "Resolution multiplier: Scales the automatically calculated boxcar width when using resolution-based gating.\n\n"
        "Mass fit tolerance: Maximum allowed mass deviation when matching peaks to the target m/z.\n\n"
        "Show gates: Displays the signal and background integration regions on the spectrum.\n\n"
        "Background type: Selects the method used for baseline/background subtraction (none, offset, or range).\n\n"
        "Background offset: Distance (in m/z) between the signal gate and the offset background gate.\n\n"
        "Average background: Uses the average background across all scans instead of a scan-by-scan background value.\n\n"
        "Background multiplier: Sets the width of the background gate relative to the signal gate and scales the subtraction accordingly.\n\n"
        "Background range stop: Upper limit of the user-defined background region when using range-based background subtraction."
    )


@dataclass
class IntegrationMassSettings:
    main_mass: float = 58.933
    main_num: int = 40
    messenger_mass: float = 18
    messenger_num: int = 2


@dataclass
class AppState:
    directory: str
    a: float
    k: float

    data: list[str] = field(default_factory=list)
    old_data: list[str] = field(default_factory=list)

    baseline: str | None = None
    lam: float = 1e9
    multiplier: float = 1.0

    dataframe: pd.DataFrame = field(default_factory=_empty_dataframe)
    figure: object = field(default_factory=_empty_figure)

    boxcar: BoxcarSettings | None = None
    intmass: IntegrationMassSettings | None = None
    files_df = None
    target_masses = None
    ioff = None
    ion = None


def get_home_state(defaults: dict) -> AppState:
    """
    Return the single AppState for this session, creating it on first run.
    
    """
    if "home_state" not in st.session_state:
        st.session_state["home_state"] = AppState(
            directory=Path(defaults["directory"]),
            a=defaults["calibration"]["a"],
            k=defaults["calibration"]["k"],
        )
    return st.session_state["home_state"]


def get_difference_state(defaults: dict) -> AppState:
    """
    Return the single AppState for this session, creating it on first run.
    
    """
    state = AppState(
            directory=defaults["directory"],
            a=defaults["calibration"]["a"],
            k=defaults["calibration"]["k"],
            boxcar = BoxcarSettings(),
            intmass = IntegrationMassSettings(),
        )
    if "difference_state" not in st.session_state:
        st.session_state["difference_state"] = state
    return st.session_state["difference_state"]