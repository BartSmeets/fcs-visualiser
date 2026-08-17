"""
FCS Visualiser

Streamlit app for browsing, calibrating and plotting FCS data.

"""
import streamlit as st
import toml

import modules
from app.data_io import basename, gen_df, list_data_files
from app.folder_dialog import select_folder
from app.plotting import generate_fig
from app.state import get_state

FILE_EXTENSION = "*.npy"


# --------------------------------------------------------------------------
# Setup / session state
# --------------------------------------------------------------------------

st.set_page_config(
    page_title="FCS Visualiser",
    page_icon="https://static-00.iconduck.com/assets.00/python-icon-512x509-pb65l7gl.png",
    layout="wide",
)
st.write("# FCS Visualiser")

try:
    with open('defaults.toml', 'r') as f:
        defaults = toml.load(f)
except OSError:
    modules.setup()
    with open('defaults.toml', 'r') as f:
        defaults = toml.load(f)

state = get_state(defaults)

# --------------------------------------------------------------------------
# Sidebar: directory selection
# --------------------------------------------------------------------------

with st.sidebar:
    # Buttons
    col1, col2 = st.columns(2)
    ## Select Directory
    with col1:
        if st.button("Select Directory"):
            selected = select_folder(state.directory)
            if selected != '':
                state.directory = selected
    ## Refresh Files
    with col2:
        st.button("Refresh Files")

    state.directory = st.text_input("Directory", value = state.directory)

all_files = list_data_files(state.directory)
file_names = [basename(p) for p in all_files]
    	
# --------------------------------------------------------------------------
# TODO Sidebar: mass calibration + baseline correction
# --------------------------------------------------------------------------
 
# with st.sidebar:
#     with st.container(border=True):
#         st.write("### Mass Calibration")
#         st.write("$m = a(t-k)^2$")
 
#         col1, col2 = st.columns(2)
#         with col1:
#             state.a = st.number_input(
#                 "a", min_value=0.0, step=1e-8, value=state.a, format="%.8f"
#             )
#         with col2:
#             state.k = st.number_input("k", step=1e-8, value=state.k, format="%.8f")
#         st.button("Apply", on_click=gen_df, args=(state,))
 
#     with st.container(border=True):
#         st.write("## Baseline Correction")
 
#         options = ["No selection"] + file_names
#         baseline_choice = st.selectbox("Baseline File", options)
#         state.baseline = (
#             None if baseline_choice == "No selection" else full_path(state, baseline_choice)
#         )
 
#         state.multiplier = st.number_input("Multiplier", value=state.multiplier)
#         state.lam = 10 ** st.select_slider(
#             r"$\lambda$ ($10^{x}$)",
#             np.arange(0, 12.1, 1),
#             value=int(np.log10(state.lam)),
#         )
 
#         col1, col2 = st.columns(2)
#         with col1:
#             st.button("Apply", key="apply_baseline", on_click=gen_df, args=(state,))
#         with col2:
#             st.button("Save", on_click=save, args=(state,))


# --------------------------------------------------------------------------
# Data selection
# --------------------------------------------------------------------------

if "selected_files" not in st.session_state:
    st.session_state.selected_files = state.data

st.multiselect(
    "Select Data",
    file_names,
    key="selected_files",
)

state.data = st.session_state.selected_files

if state.data != state.old_data:
    state.old_data = state.data.copy()
    gen_df(state)

# --------------------------------------------------------------------------
# Plotting
# --------------------------------------------------------------------------
 
if state.data:
    col1, col2 = st.columns([3, 1])
 
    with col2:
        spectrum_dict = {"Time": "time", "Mass": "mass"}
        spectrum_label = st.radio("Spectrum Type", ["Mass", "Time"])
        spectrum_type = spectrum_dict[spectrum_label]
 
        axis_series = state.dataframe[spectrum_type]
        axis_min = float(axis_series.min())
        axis_max = float(axis_series.max())
 
        with st.container(border=True):
            pointer = st.toggle("Pointer")
            pointer_value = st.number_input(
                "Pointer",
                min_value=axis_min,
                max_value=axis_max,
                value=axis_min,
                label_visibility="collapsed",
            )
 
    with col1:
        fig = generate_fig(state, spectrum_type, pointer, pointer_value)
        state.figure = fig
        st.plotly_chart(fig, width='stretch')











