import numpy as np
import streamlit as st
import toml

# Your imports
from analysis.ir import filter, integrated_signals
from app import sidebar
from app.data_io import gen_csv, get_all_data
from app.plotting import plot_on_off_difference
from app.state import IntegrationMassSettings, get_state

# --------------------------------------------------------------------------
# Setup / session state
# --------------------------------------------------------------------------

st.set_page_config(
    page_title="Mass Integration Viewer",
    page_icon="https://static-00.iconduck.com/assets.00/python-icon-512x509-pb65l7gl.png",
    layout="wide",
)
st.write("# IR Spectroscopy Quicky")

with open('defaults.toml', 'r') as f:
    defaults = toml.load(f)

state = get_state(defaults)
state.files_df = get_all_data(state)
state.intmass = IntegrationMassSettings()
# ============================================================
# Streamlit UI
# ============================================================

sidebar.directory(state)
sidebar.calibration(state)

folder = st.text_input(
    "Data folder",
    value= state.directory,
    disabled=True
)

with st.expander("Files"):
    st.dataframe(state.files_df)
refresh = st.button("🔄 Refresh folder")

# ============================================================
# Integration settings
# ============================================================

with st.expander("Integration Settings"):
    col1, col2 = st.columns(2)

    with col1:
        window = st.number_input(
            "Search Window (m/z)",
            value=1.0,
            disabled=False
        )

    with col2:

        max_half_width = st.number_input(
            "Max Half Width (m/z)",
            value=1.0,
            disabled=False
        )

# ============================================================
# Integration
# ============================================================

run_button = st.button("Run Integration")

if run_button and state.directory.exists():
    state.ioff, state.ion, state.target_masses = integrated_signals(state, window, max_half_width)

if state.ioff is not None:
    if not st.toggle("difference | depletion mode", value=False):
        mode = "diff"
    else:
        mode = "depl"

    # Filter
    col1, col2 = st.columns(2)
    with col1:
        m_threshold = st.number_input("Minimum integral value",
                                      min_value=0.0,
                                      value=0.0)
    with col2:
        cv_threshold = st.number_input("Maximum std/mean value",
                                       min_value=0.0,
                                       value=0.5)
    valid_masses = filter(state, m_threshold, cv_threshold)

    selected = st.multiselect(
        "Masses to show",
        options=list(np.round(valid_masses, 2)),   # only offer masses that actually have data
        default=list(np.round(valid_masses, 2)),
    )

    idx = [int(np.where(np.asarray(np.round(state.target_masses, 2)) == m)[0][0]) 
           for m in selected]
    fig = plot_on_off_difference(
        sorted(state.files_df.wave.unique()),
        state.ioff[idx, :],
        state.ion[idx, :],
        selected,
        mode,
    )
    st.plotly_chart(fig, width='stretch')

    csv = gen_csv(state, idx)

    st.download_button(
        "Download CSV",
        csv,
        "integrated_masses.csv",
        "text/csv"
    )