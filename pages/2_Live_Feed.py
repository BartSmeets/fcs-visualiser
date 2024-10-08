import streamlit as st
import modules.johanpackage.scope as scope
import plotly.graph_objects as go
import time
from scipy.signal import find_peaks, peak_widths
import numpy as np

# Initialise Session State
if 'scope1' not in st.session_state:
    try:
        scope1 = scope.initialise("MDO34_Primary","MDO34_SN_Primary")
        st.session_state['scope1'] = scope1
    except:
        st.warning("Couldn't connect with the primary scope")
if 'scope2' not in st.session_state:
    try:
        scope2 = scope.initialise("MDO34_Secondary","MDO34_SN_Secondary")
        st.session_state['scope2'] = scope2
    except:
        st.warning("Couldn't connect with the secondary scope")
if 'fig1' not in st.session_state:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[], y=[], mode='lines'))
    fig.update_layout(xaxis=dict(showgrid=True))
    st.session_state['fig1'] = fig
if 'run' not in st.session_state:
    st.session_state['run'] = False
if 'x_min' not in st.session_state:
    st.session_state['x_min'] = -20
if 'x_max' not in st.session_state:
    st.session_state['x_max'] = 180
if 'y_min' not in st.session_state:
    st.session_state['y_min'] = -200
if 'y_max' not in st.session_state:
    st.session_state['y_max'] = 0
if 'R_toggle' not in st.session_state:
    st.session_state['R_toggle'] = False
if 'target' not in st.session_state:
    st.session_state['target'] = 0.0
if 'avg' not in st.session_state:
    st.session_state['avg'] = np.zeros(5)
if 'lf_baseline' not in st.session_state:
    st.session_state['lf_baseline'] = 0.0

# Define Reading Function
def output(scope_str, fig_frame, R_frame):
    # Initialise
    time.sleep(3.2) # Wait until all data in the 32 avg is new
    fig = st.session_state['fig1']

    # Read Data
    try:
        scope_obj = st.session_state[scope_str]
    except KeyError:
        if scope_str == 'scope1':
            st.error("Couldn't connect to the primary scope")
        else:
            st.error("Couldn't connect to the secondary scope")
        return False
    else:
        data = scope.read('CH1', scope_obj)

        # Generate figure
        fig.data[0].x = data[:, 0] * 1e6    # us
        fig.data[0].y = data[:, 1] * 1e3 - st.session_state['lf_baseline']  # mV
        fig.update_layout(
            yaxis_range=[st.session_state['y_min'], st.session_state['y_max']], 
            xaxis_range=[st.session_state['x_min'], st.session_state['x_max']])
        fig_frame.plotly_chart(fig, use_container_width=True)
        
        # Calculate Resolution
        if st.session_state['R_toggle']:
            # Extract data
            x_data = data[:, 0]*1e6 # us
            y_data = -data[:,1]*1e3 - st.session_state['lf_baseline']   # mV
            # Find Peaks
            peaks, _ = find_peaks(y_data, prominence=10)
            ## Calculate which peak is closest to target
            diff = np.abs(x_data[peaks] - st.session_state['target'])
            try:
                the_chosen_one = peaks[np.argmin(diff)]
            except ValueError:
                R_frame.error('No Peaks found')
            ## Calcualte peak width (in index number...)
            _, _, lips, rips = peak_widths(y_data, peaks=[the_chosen_one])
            delta = x_data[int(rips[0])] - x_data[int(lips[0])] # Convert peak width to time units
            # Calculate Resolution
            R = st.session_state['target'] / (2*delta)
            st.session_state['avg'] = np.append(st.session_state['avg'], R)
            st.session_state['avg'] = np.delete(st.session_state['avg'], 0)
            avg = np.average(st.session_state['avg'])
            R_frame.success(f'Resolution = {R:.1f} \
                             \nAverage (5 cycles) = {avg:.1f}')

        return True


# Side Bar
with st.sidebar:
    # Standard Settings
    st.toggle('Run/Stop', key='run')
    col1, col2 = st.columns(2)
    with col1:
        st.number_input('x$_{min}$', key='x_min')
        st.number_input('y$_{min}$', key='y_min')
    with col2:
        st.number_input('x$_{max}$', key='x_max')
        st.number_input('y$_{max}$', key='y_max')
    st.number_input('Baseline (mV)', key='lf_baseline')
    
    # Resolution
    with st.container(border=True):
        st.header('Resolution')
        st.toggle('Toggle Resolution', key='R_toggle')
        st.number_input('At what time?', min_value=0.0, key='target')

# Primary Scope
with st.container(border=True):
    # Initialise
    st.header('Primary Scope')
    figure = st.empty()
    success = st.empty()
    figure.plotly_chart(st.session_state['fig1'])
# Secondary Scope
with st.container(border=True):
    # Initialise
    st.header('Secondary Scope')
    figure2 = st.empty()
    success2 = st.empty()
    figure2.plotly_chart(st.session_state['fig1'])


# Run Live Feed
while st.session_state['run']:
    if not output('scope1', figure, success) and not output('scope2', figure2, success2):
        break


    
