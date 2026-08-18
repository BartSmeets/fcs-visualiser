from pathlib import Path

import streamlit as st

from app.data_io import gen_df
from app.folder_dialog import select_folder
from app.state import AppState


def directory(state: AppState):
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

        state.directory = Path(st.text_input("Directory", value = state.directory))


def calibration(state: AppState):
    with st.sidebar, st.container(border=True):
        st.write("### Mass Calibration")
        st.write("$m = a(t-k)^2$")
    
        col1, col2 = st.columns(2)
        with col1:
            state.a = st.number_input(
                "a", min_value=0.0, step=1e-8, value=state.a, format="%.8f"
            )
        with col2:
            state.k = st.number_input("k", step=1e-8, value=state.k, format="%.8f")
        st.button("Apply", on_click=gen_df, args=(state,))