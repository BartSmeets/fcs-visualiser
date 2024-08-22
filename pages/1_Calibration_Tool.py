import streamlit as st
from scipy.optimize import fsolve
from warnings import catch_warnings

def system(x, t1, t2, m1, m2):
    eq1 = x[0]*(t1 - x[1])**2 - m1
    eq2 = x[0]*(t2 - x[1])**2 - m2
    return [eq1, eq2]


# Information
st.write("# Manual Calibration Tool")
st.write("This tool will solve the following system of equations:")
st.latex(r"\begin{cases}\
         m_{1} = a(t_{1} - k)^{2} \\ \
         m_{2} = a(t_{2} - k)^{2}, \
         \end{cases}")
st.write(r"where $t_{1}$ and $t_{2}$ are the times (μs) at which a peak is observed; and $m_{1}$ and $m_{2}$ are the masses (amu) that correspond to these times.")


# Input
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        t1 = st.number_input(r'$t_{1}$ (μs)', min_value=0.0, format='%.3f')
        m1 = st.number_input(r'$m_{1}$ (amu)', min_value=0.0, format='%.4f')
    with col2:
        t2 = st.number_input(r'$t_{2}$ (μs)', min_value=0.0, format='%.3f')
        m2 = st.number_input(r'$m_{2}$ (amu)', min_value=0.0, format='%.4f')

# Output
with st.container(border=True):
    st.write('## Solution')
    with catch_warnings(record=True) as w:
        a, k = fsolve(system, [st.session_state['a'], st.session_state['k']], args=(t1, t2, m1, m2))
    st.write("#### a = `%.5f` amu/μs$^{2}$" % a)
    st.write("#### k = `%.5f` μs" % k)

# Show warning if applicable
if len(w) != 0:
    with st.container(border=True):
        for warning in w:
            st.write(warning)