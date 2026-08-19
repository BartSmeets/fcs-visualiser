import numpy as np
import streamlit as st
import toml

# Your imports
from analysis.ir import filter, integrated_signals, target_mass
from app import sidebar
from app.data_io import gen_csv, get_all_data
from app.plotting import plot_on_off_difference
from app.state import get_difference_state

# --------------------------------------------------------------------------
# Setup / session state
# --------------------------------------------------------------------------

st.set_page_config(
    page_title="Mass Integration Viewer",
    page_icon="https://static-00.iconduck.com/assets.00/python-icon-512x509-pb65l7gl.png",
    layout="wide",
)
st.write("# FCS Visualiser")

with open('defaults.toml', 'r') as f:
    defaults = toml.load(f)

state = get_difference_state(defaults)
state.files_df = get_all_data(state)
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
# Mass definition
# ============================================================

col1, col2 = st.columns(2)

with col1:
    st.subheader("Main")
    main_mass = st.number_input(
        "Mass (m/z)",
        value=state.intmass.main_mass,
        key="main_mass_input",
    )
    state.intmass.main_mass = main_mass

    max_main = st.number_input(
        "Maximum number of mains",
        min_value=1,
        value=state.intmass.main_num,
        key="main_num_input",
    )
    state.intmass.main_num = int(max_main)

with col2:
    st.subheader("Messenger")
    messenger_mass = st.number_input(
        "Mass (m/z)",
        value=state.intmass.messenger_mass,
        key="messenger_mass_input",
    )
    state.intmass.messenger_mass = messenger_mass

    max_messenger = st.number_input(
        "Maximum number of messengers",
        min_value=1,
        value=state.intmass.messenger_num,
        key="messenger_num_input",
    )
    state.intmass.messenger_num = int(max_messenger)

target_masses = target_mass(state)
with st.expander("Masses"):
    st.write(target_masses)

# ============================================================
# Boxcar settings
# ============================================================

with st.expander("Boxcar Settings"):
    st.write(state.boxcar.description)
    col1, col2 = st.columns(2)

    with col1:

        bxtype = st.selectbox(
            "Boxcar type",
            ["width", "resolution"],
            disabled=False
        )
        state.boxcar.bxtype = bxtype

        bxwidth = st.number_input(
            "Boxcar width (m/z)",
            value=state.boxcar.bxwidth,
            disabled=False
        )
        state.boxcar.bxwidth = bxwidth

        bxresmulti = st.number_input(
            "Resolution multiplier",
            value=state.boxcar.bxresmulti,
            disabled=False
        )
        state.boxcar.bxresmulti = bxresmulti

        bxtolerance = st.number_input(
            "Mass fit tolerance",
            value=state.boxcar.bxtolerance,
            disabled=False
        )
        state.boxcar.bxtolerance = bxtolerance

        showgates = st.checkbox(
            "Show gates",
            value=state.boxcar.showgates,
            disabled=False
        )
        state.boxcar.showgates = showgates

    with col2:

        bgtype = st.selectbox(
            "Background type",
            ["none", "offset", "range"],
            disabled=False
        )
        state.boxcar.bgtype = bgtype

        bgoffset = st.number_input(
            "Background offset",
            value=state.boxcar.bgoffset,
            disabled=False
        )
        state.boxcar.bgoffset = bgoffset

        bgaverage = st.checkbox(
            "Average background",
            value=state.boxcar.bgaverage,
            disabled=False
        )
        state.boxcar.bgaverage = bgaverage

        bgmultiplier = st.number_input(
            "Background multiplier",
            value=state.boxcar.bgmultiplier,
            disabled=False
        )
        state.boxcar.bgmultiplier = bgmultiplier

        bgrange_text = st.number_input(
            "Background range stop",
            value=5000,
            disabled=False
        )
        state.boxcar.bgrange = range(int(bgrange_text))

# ============================================================
# Integration
# ============================================================

run_button = st.button("Run Integration")

if run_button and state.directory.exists():
    state.target_masses = target_masses          # freeze the masses used
    state.ioff, state.ion = integrated_signals(state, target_masses)

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
        options=list(valid_masses),   # only offer masses that actually have data
        default=list(valid_masses),
    )

    idx = [int(np.where(np.asarray(state.target_masses) == m)[0][0]) 
           for m in selected]
    fig = plot_on_off_difference(
        sorted(state.files_df.wave.unique()),
        state.ioff[idx, :],
        state.ion[idx, :],
        selected,
        mode,
    )
    st.plotly_chart(fig, width='stretch')

    csv = gen_csv(state)

    st.download_button(
        "Download CSV",
        csv,
        "integrated_masses.csv",
        "text/csv"
    )