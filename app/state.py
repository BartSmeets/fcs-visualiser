"""
Application state for the FCS Visualiser

A single AppState instance lives in st.session_state['app_state'] and is passed to functions that need it.

"""

from dataclasses import dataclass, field

import pandas as pd
import plotly.express as px
import streamlit as st


def _empty_dataframe() -> pd.DataFrame:
    return pd.DataFrame({"time": [], "mass": [], "voltage": [], "name": []})
 
 
def _empty_figure():
    return px.line([])


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


def get_state(defaults: dict) -> AppState:
    """
    Return the single AppState for this session, creating it on first run.
    
    """
    if "app_state" not in st.session_state:
        st.session_state["app_state"] = AppState(
            directory=defaults["directory"],
            a=defaults["calibration"]["a"],
            k=defaults["calibration"]["k"],
        )
    return st.session_state["app_state"]