import streamlit as st
from scipy.optimize import fsolve, curve_fit
from warnings import catch_warnings
import toml
from datetime import datetime
import plotly.express as px
import pandas as pd
import numpy as np


# Information
st.set_page_config(layout='wide')
st.write("# Manual Calibration Tool")


# Figure
def generate_fig():
    def prepare_axes(xlabel, ylabel):
        fig.update_layout(
            xaxis_title = xlabel,
            yaxis_title = ylabel,
            legend = dict(
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                orientation="h"),
            legend_title_text='',
            xaxis=dict(showgrid=True),
            uirevision=True)
    
    # Time Spectrum
    fig = px.line(st.session_state['dataframe'], x='time', y='voltage', color='name')
    prepare_axes('time (us)', 'accumulated voltage (V)')
    
    return fig

st.plotly_chart(generate_fig())


# Input
edited_df = st.data_editor(pd.DataFrame({'Time':[], 'Mass':[]}), num_rows="dynamic", width=500)

# Optimise
def optimise():
    y = np.array(edited_df['Mass'])
    x = np.array(edited_df['Time'])
    mask = ~np.logical_or(np.isnan(x),np.isnan(y))
    x = x[mask]
    y = y[mask]

    toFit = lambda x, a, k: a*(x-k)**2
    try:
        popt, pcov = curve_fit(toFit, x, y, p0=[0.09, 0.2])
    except:
        return 0, 0
    return popt[0], popt[1]
    

# Output
def apply(a, k):
    today = datetime.now()

    with open('defaults.toml', 'r') as f:
        defaults = toml.load(f)

    # Log new values
    defaults['logbook'][today.isoformat()] = {
        'a': float(a),
        'k': float(k)
        }

    # Store new values
    defaults['calibration']['a'] = float(a)
    defaults['calibration']['k'] = float(k)

    # Dump
    with open('defaults.toml', "w") as toml_file:
        toml.dump(defaults, toml_file)

    # Update Session State
    st.session_state['a'] = float(a)
    st.session_state['k'] = float(k)

# Print Output
with st.container(border=True):
    st.write('## Solution')
    with catch_warnings(record=True) as w:
        a, k = optimise()
    st.write("#### a = `%.5f` amu/μs$^{2}$" % a)
    st.write("#### k = `%.5f` μs" % k)
    st.button('Apply', on_click=lambda: apply(a, k))

# Show warning if applicable
if len(w) != 0:
    with st.container(border=True):
        for warning in w:
            st.write(warning)