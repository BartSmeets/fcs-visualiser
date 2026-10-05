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

    intmass: IntegrationMassSettings | None = None
    files_df = None
    target_masses = None
    ioff = None
    ion = None


def get_state(defaults: dict) -> AppState:
    """
    Return the single AppState for this session, creating it on first run.
    
    """
    if "state" not in st.session_state:
        st.session_state["state"] = AppState(
            directory=Path(defaults["directory"]),
            a=defaults["calibration"]["a"],
            k=defaults["calibration"]["k"],
        )
    return st.session_state["state"]