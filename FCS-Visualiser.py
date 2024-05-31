import streamlit as st
import streamlit.components.v1 as components
import tkinter as tk
from tkinter import filedialog
import glob
from lib.calibration import load_data
import numpy as np
import pandas as pd 
import mpld3
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="FCS Visualiser",
    page_icon="https://static-00.iconduck.com/assets.00/python-icon-512x509-pb65l7gl.png",
)

if 'directory' not in st.session_state:
    st.session_state['directory'] = r'R:/CLASS/LAB/FCS/DATA/'
if 'prominence' not in st.session_state:
    st.session_state['prominence'] = 0.5
if 'a' not in st.session_state:
    st.session_state['a'] = 0.09949062
if 'k' not in st.session_state:
    st.session_state['k'] = 0.23745731
selected_data = None
loaded_data = None
file_extension = "*.npy"


# Title
st.write("# FCS Visualiser")

# Select Data Directory
def select_folder():
    root = tk.Tk()
    root.attributes('-topmost', True)
    root.withdraw()
    path = filedialog.askdirectory(title='Select Directory', initialdir=st.session_state['directory'], parent=root)
    root.destroy()
    return path

with st.sidebar:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Select Directory"):
            selected = select_folder()
            if selected != '':
                st.session_state['directory'] = selected
    with col2:
        if st.button("Refresh Files"):
            file_location = st.session_state['directory'] + "//*" + file_extension
            all_files = glob.glob(file_location)
    st.session_state['directory'] = st.text_input("Directory", value=st.session_state['directory'])

file_location = st.session_state['directory'] + "//*" + file_extension
all_files = glob.glob(file_location)

dummy = np.arange(1, 10, 1)
prominence_steps = np.concatenate((dummy/1000, dummy/100, dummy/10, dummy, dummy*10))
selected_data = st.selectbox("Select Data", all_files)

if selected_data != None:
    loaded_data = load_data(selected_data, 'Co', prominence=st.session_state['prominence'])
    st.session_state['a'], st.session_state['k'] = loaded_data.optimise(threshold=0.001)
    result, df = loaded_data.characterise()

with st.sidebar:
    with st.container(border=True):
        st.write("## Peak Detection & Mass Calibration")
        st.session_state['prominence'] = st.select_slider("Peak Prominence", options=prominence_steps, value=st.session_state['prominence'])
        st.write('### Mass Calibration')
        st.write('$m = a(t-k)^2$')

        col1, col2 = st.columns(2)
        with col1:
            st.session_state['a'] = st.number_input("a", min_value=0.0, step=1e-8, value=st.session_state['a'], format='%.8f')
        with col2:
            st.session_state['k'] = st.number_input("k", min_value=0.0, step=1e-8, value=st.session_state['k'], format='%.8f')

        if st.button('Auto-Calibrate'):
            st.session_state['a'], st.session_state['k'] = loaded_data.optimise(threshold=0.001)

st.write('## Time Spectrum')
if loaded_data != None:
    fig = plt.figure()
    plt.plot(loaded_data.time, loaded_data.voltage)
    plt.grid(alpha=0.25)
    plt.xlabel('time (us)')
    plt.ylabel('accumulated voltage (V)')
    
    fig_html = mpld3.fig_to_html(fig)
    components.html(fig_html, height=500)

st.write('## Mass Spectrum')
if loaded_data != None:
    fig = plt.figure()
    plt.plot(loaded_data.mass_element, loaded_data.voltage)
    plt.grid(alpha=0.25)
    plt.xlabel('mass (Co)')
    plt.ylabel('accumulated voltage (V)')
    fig_html = mpld3.fig_to_html(fig)
    components.html(fig_html, height=500)

max_columns = 9

st.write('## Table')
pd.set_option('display.max_rows', None)
pd.options.display.float_format = '{:,.5f}'.format
st.dataframe(df.iloc[:, :max_columns])












