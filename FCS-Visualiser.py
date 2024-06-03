# Imports
import configparser
import streamlit as st
import streamlit.components.v1 as components
import tkinter as tk
from tkinter import filedialog
import glob
from lib.calibration import load_data
import numpy as np
import pandas as pd 
import plotly.express as px

# Page Config
st.set_page_config(
    page_title="FCS Visualiser",
    page_icon="https://static-00.iconduck.com/assets.00/python-icon-512x509-pb65l7gl.png")
st.write("# FCS Visualiser")
defaults = configparser.ConfigParser()
defaults.read('defaults.ini')

# Initialise session states
if 'directory' not in st.session_state:
    st.session_state['directory'] = defaults.get('defaults', 'directory')
if 'prominence' not in st.session_state:
    st.session_state['prominence'] = 0.5
if 'a' not in st.session_state:
    st.session_state['a'] = float(defaults.get('defaults', 'a'))
if 'k' not in st.session_state:
    st.session_state['k'] = float(defaults.get('defaults', 'k'))
if 'data' not in st.session_state:
    st.session_state['data'] = None
if 'data_loc' not in st.session_state:
    st.session_state['data_loc'] = None
if 'table' not in st.session_state:
    st.session_state['table'] = None
if 'characterisation' not in st.session_state:
    st.session_state['characterisation'] = None

file_extension = "*.npy"


# Side Bar
def select_folder():
    root = tk.Tk()
    root.attributes('-topmost', True)
    root.withdraw()
    path = filedialog.askdirectory(title='Select Directory', initialdir=st.session_state['directory'], parent=root)
    root.destroy()
    return path

with st.sidebar:
    # Buttons
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
    	
    # Prominence Slider and Calibration Parameters
    with st.container(border=True):
        dummy = np.arange(1, 10, 1)
        prominence_steps = np.concatenate((dummy/1000, dummy/100, dummy/10, dummy, dummy*10))

        st.write("## Peak Detection & Mass Calibration")
        prominence = st.select_slider("Peak Prominence", options=prominence_steps, value=st.session_state['prominence'])
        st.write('### Mass Calibration')
        st.write('$m = a(t-k)^2$')

        col1, col2 = st.columns(2)
        with col1:
            st.session_state['a'] = st.number_input("a", min_value=0.0, step=1e-8, value=st.session_state['a'], format='%.8f')
        with col2:
            st.session_state['k'] = st.number_input("k", min_value=0.0, step=1e-8, value=st.session_state['k'], format='%.8f')
        if st.button('Auto-Calibrate'):
            try:
                st.session_state['a'], st.session_state['k'] = st.session_state['data'].optimise(threshold=0.001)
            except:
                st.warning('No data selected')

# Data Selection
directory_length = len(st.session_state['directory'])
selected_data = st.selectbox("Select Data", [file_name[directory_length:] for file_name in all_files])
selected_data = st.session_state['directory'] + selected_data

if (selected_data != st.session_state['data_loc'] or
    prominence != st.session_state['prominence']):   # New data selected
    st.session_state['data_loc'] = selected_data
    st.session_state['prominence'] = prominence
    st.session_state['data'] = load_data(selected_data, 'Co', prominence=st.session_state['prominence'])
    st.session_state['a'], st.session_state['k'] = st.session_state['data'].optimise(threshold=0.001)
      


# Plot
data = st.session_state['data']

def plot():
    if spectrum_type == 'Time':
        fig = px.line(x=data.time, y=data.voltage)
        fig.update_layout(
            xaxis_title = 'time (us)',
            yaxis_title = 'accumulated voltage (V)')
            
        if peak_detection or show_tag:
            for i, peak in enumerate(data.peaks):
                if 'Ar' in characterisation[i] and show_tag:
                    fig.add_vline(data.time[peak], line_dash="dash", line_color='blue', opacity=0.25)
                elif peak_detection:
                        fig.add_vline(data.time[peak], line_dash='dot', line_color='grey', opacity=0.25)
        
    elif spectrum_type == 'Mass (amu)':
        fig = px.line(x=data.mass, y=data.voltage)
        fig.update_layout(
            xaxis_title = 'mass (amu)',
            yaxis_title = 'accumulated voltage (V)')
        
        if peak_detection or show_tag:
            for i, peak in enumerate(data.peaks):
                if 'Ar' in characterisation[i] and show_tag:
                    fig.add_vline(data.mass[peak], line_dash="dash", line_color='blue', opacity=0.25)
                elif peak_detection:
                    fig.add_vline(data.mass[peak], line_dash='dot', line_color='grey', opacity=0.25)
    
    else:
        fig = px.line(x=data.mass_element, y=data.voltage)
        fig.update_layout(
            xaxis_title = 'mass (Co)',
            yaxis_title = 'accumulated voltage (V)')
        
        if peak_detection or show_tag:
            for i, peak in enumerate(data.peaks):
                if 'Ar' in characterisation[i] and show_tag:
                    fig.add_vline(data.mass_element[peak], line_dash="dash", line_color='blue', opacity=0.25)
                elif peak_detection:
                    fig.add_vline(data.mass_element[peak], line_dash='dot', line_color='grey', opacity=0.25)
    fig.update_layout(xaxis=dict(showgrid=True))
    return fig


if data != None:
    data.calibrate(st.session_state['a'], st.session_state['k'])  
    characterisation, table = data.characterise()
    characterisation = characterisation[:, 0]

    ## Input
    col1, col2 = st.columns([2, 1])
    with col2:
        spectrum_type = st.selectbox('Spectrum Type', ['Time', 'Mass (amu)', 'Mass (Co)'])
        peak_detection = st.toggle('Peak Detection')
        show_tag = st.toggle('Show Tag')
        fig = plot()
        with st.container(border = True):
            pointer = st.toggle('Pointer')
            if spectrum_type == 'Time':
                pointer_value = st.number_input('Pointer', data.time[0], data.time[-1], label_visibility='collapsed')
            elif spectrum_type == 'Mass (amu)':
                pointer_value = st.number_input('Pointer', data.mass[0], data.mass[-1], label_visibility='collapsed')
            else:
                pointer_value = st.number_input('Pointer', data.mass_element[0], data.mass_element[-1], label_visibility='collapsed')
        if pointer:
            fig.add_vline(pointer_value, line_dash="dash", line_color="red")
    with col1:
        st.plotly_chart(fig)

    # Table
    st.write('## Table')

    max_columns = 9
    pd.set_option('display.max_rows', None)
    pd.options.display.float_format = '{:,.5f}'.format
    try:
        st.dataframe(table.iloc[:, :max_columns])
    except:
        pass












