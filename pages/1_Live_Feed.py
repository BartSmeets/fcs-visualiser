import streamlit as st
import modules.johanpackage.scope as scope
import plotly.graph_objects as go
import time


if 'scope1' not in st.session_state:
    try:
        scope1 = scope.initialise("MDO34_Primary","MDO34_SN_Primary")
        st.session_state['scope1'] = scope1
    except:
        st.warning("Couldn't connect with the primary scope")
if 'fig1' not in st.session_state:
    st.session_state['fig1'] = go.Figure()
    st.session_state['fig1'].add_trace(go.Scatter(x=[], y=[], mode='lines'))
    st.session_state['fig1'].update_layout(
            xaxis=dict(showgrid=True))
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

with st.sidebar:
    st.toggle('Run/Stop', key='run')
    col1, col2 = st.columns(2)
    with col1:
        st.number_input('x$_{min}$', key='x_min')
        st.number_input('y$_{min}$', key='y_min')
    with col2:
        st.number_input('x$_{max}$', key='x_max')
        st.number_input('y$_{max}$', key='y_max')

with st.container(border=True):
    st.header('Primary Scope')
    placeholder = st.empty()
    placeholder.plotly_chart(st.session_state['fig1'])

while st.session_state['run']:
    time.sleep(3.2)
    fig = st.session_state['fig1']
    try:
        scope1 = st.session_state['scope1']
    except KeyError:
        st.error("Couldn't connect to Primary Scope")
        break
    else:
        data1 = scope.read('CH1', scope1)
        fig.data[0].x = data1[:, 0] * 1e6
        fig.data[0].y = data1[:, 1] * 1e3
        fig.update_layout(
            yaxis_range=[st.session_state['y_min'], st.session_state['y_max']], 
            xaxis_range=[st.session_state['x_min'], st.session_state['x_max']])
        placeholder.plotly_chart(fig, use_container_width=True)

    