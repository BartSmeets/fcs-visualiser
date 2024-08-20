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

toggle = st.toggle('Run/Stop', value=False)

with st.container(border=True):
    st.header('Primary Scope')
    placeholder = st.empty()
    placeholder.plotly_chart(st.session_state['fig1'])

while toggle:
    time.sleep(3.2)
    fig = st.session_state['fig1']
    scope1 = st.session_state['scope1']
    data1 = scope.read('CH1', scope1)
    fig.data[0].x = data1[:, 0]
    fig.data[0].y = data1[:, 1]
    placeholder.plotly_chart(fig, use_container_width=True)

    