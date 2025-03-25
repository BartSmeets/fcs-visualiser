# Imports
import configparser
import toml
import streamlit as st
import tkinter as tk
from tkinter import filedialog
import glob
from modules.calibration import load_data
import modules
import numpy as np
import pandas as pd 
import plotly.express as px
import os.path

# Page Config
st.set_page_config(
    page_title="FCS Visualiser",
    page_icon="https://static-00.iconduck.com/assets.00/python-icon-512x509-pb65l7gl.png",
    layout='wide')
st.write("# FCS Visualiser")
try:
    with open('defaults.toml', 'r') as f:
        defaults = toml.load(f)
except OSError:
    modules.setup()
    with open('defaults.toml', 'r') as f:
        defaults = toml.load(f)

# Initialise session states
if 'directory' not in st.session_state:
    st.session_state['directory'] = defaults['directory']
if 'a' not in st.session_state:
    st.session_state['a'] = defaults['calibration']['a']
if 'k' not in st.session_state:
    st.session_state['k'] = defaults['calibration']['k']
if 'data' not in st.session_state:
    st.session_state['data'] = []
if 'old_data' not in st.session_state:
    st.session_state['old_data'] = []
if 'baseline' not in st.session_state:
    st.session_state['baseline'] = None
if 'dataframe' not in st.session_state:
    st.session_state['dataframe'] = pd.DataFrame({'time': [],
                                                'mass': [],
                                                'mass_element': [],
                                                'voltage': [],
                                                'norm': [],
                                                'name': []})
if 'figure' not in st.session_state:
    st.session_state['figure'] = px.line([])

file_extension = "*.npy"

# Folder selection in sidebar
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
    ## Select Directory
    with col1:
        if st.button("Select Directory"):
            selected = select_folder()
            if selected != '':
                st.session_state['directory'] = selected
    ## Refresh Files
    with col2:
        if st.button("Refresh Files"):
            file_location = st.session_state['directory'] + "//*" + file_extension
            all_files = glob.glob(file_location)
    ## Print/Edit Directory
    st.session_state['directory'] = st.text_input("Directory", value=st.session_state['directory'])
    directory_length = len(st.session_state['directory'])
    file_location = st.session_state['directory'] + "//*" + file_extension
    all_files = glob.glob(file_location)    # Load files
    	

# Data Selection
# Define data structure
def gen_df(): 
    init_param = [st.session_state['a'], st.session_state['k']]
    st.session_state['dataframe'] = pd.DataFrame({'time': [],
                                                'mass': [],
                                                'voltage': [],
                                                'name': []})  
    for name in st.session_state['data']:
        directory = all_files[0][:directory_length+6] + name
        try:
            data = load_data(directory, init_param)
            df = pd.DataFrame({'time': data.time,
                        'mass': data.mass,
                        'voltage': data.voltage,
                        'name': [name]*len(data.time)})
        except OSError:
            return

        if st.session_state['baseline'] is not None:
            data.baseline_correction(lam, multiplier, st.session_state['baseline'])
            df['baseline'] = data.baseline
           
        st.session_state['dataframe'] = pd.concat([st.session_state['dataframe'], df])

# Save Data
def save():
    for name in st.session_state['data']:
        # Initialise filename
        directory = all_files[0][:directory_length+6]
        name = name[:-4] + '_adj'
        clean_name = name
        i = 0
        ## Find unique file name
        while os.path.isfile(directory + name + '.npy'):
            name = clean_name + '_' + str(i)
            i += 1

        # Select data from dataframe
        df = st.session_state['dataframe']
        df = df[df['name'] == df['name']]
        to_save = df[['time', 'voltage']]
        to_save.loc[:, 'time'] *= 1e-6
        to_save.loc[:, 'voltage'] = -to_save['voltage']
        np.save(directory + name + '.npy', to_save.to_numpy())

# Mass Calibration
with st.sidebar:
    with st.container(border=True):
        st.write('### Mass Calibration')
        st.write('$m = a(t-k)^2$')

        # Show and apply a and k parameters
        col1, col2 = st.columns(2)
        with col1:
            st.session_state['a'] = st.number_input("a", min_value=0.0, step=1e-8, value=st.session_state['a'], format='%.8f')
        with col2:
            st.session_state['k'] = st.number_input("k", step=1e-8, value=st.session_state['k'], format='%.8f')
        # Apply Button
        st.button('Apply', on_click=gen_df)

    # Baseline Correction
    with st.container(border=True):
        st.write("## Baseline Correction")
        options = ['No selection']
        options = [file_name[directory_length+6:] for file_name in all_files]
        options.insert(0, 'No selection')
        baseline = st.selectbox("Baseline File", options)
        if baseline == 'No selection':
            st.session_state['baseline'] = None
        else:
            baseline = all_files[0][:directory_length+6] + baseline
            st.session_state['baseline'] = baseline

        multiplier = st.number_input('Multiplier', value=1.)
        lam = 10**st.select_slider(r'$\lambda$ ($10^{x}$)', np.arange(0, 12.1, 1), value=9)
        col1, col2 = st.columns(2)
        with col1:
            st.button('Apply', key=1, on_click=gen_df)
        with col2:
            st.button('Save', on_click=save)

# Actual data selection
st.session_state['data'] = st.multiselect("Select Data", [file_name[directory_length+6:] for file_name in all_files])

if st.session_state['data'] != st.session_state['old_data']:
    st.session_state['old_data'] = st.session_state['data']
    gen_df()

# Plot
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
    if spectrum_type == 'time':
        fig = px.line(st.session_state['dataframe'], x='time', y='voltage', color='name')
        prepare_axes('time (us)', 'accumulated voltage (V)')
    # Mass Spectrum
    elif spectrum_type == 'mass':
        fig = px.line(st.session_state['dataframe'], x='mass', y='voltage', color='name')
        prepare_axes('mass (amu)', 'accumulated voltage (V)')
    
    # Add Pointer
    if pointer:
        fig.add_vline(pointer_value, line_dash="dash", line_color="red")
    
    return fig


# Visualise Data
if st.session_state['data'] != []:
    
    ## Inputs (X-axis)
    col1, col2 = st.columns([3, 1])
    with col2:
        SPECTRUM_DICT = {'Time': 'time',
                         'Mass': 'mass'}
        spectrum_type = st.radio('Spectrum Type', ['Mass','Time'])
        spectrum_type = SPECTRUM_DICT[spectrum_type]

        with st.container(border = True):
            pointer = st.toggle('Pointer')
            pointer_value = st.number_input('Pointer',
                                            st.session_state['dataframe'][spectrum_type].iloc[0], 
                                            st.session_state['dataframe'][spectrum_type].iloc[-1], 
                                            label_visibility='collapsed')  
    ## Figure
    with col1:
        fig = generate_fig()
        st.session_state['figure'] = fig
        st.plotly_chart(fig)

    # Table
    st.write('## Table')

    max_columns = 9
    pd.set_option('display.max_rows', None)
    pd.options.display.float_format = '{:,.5f}'.format
    try:
        st.dataframe(st.session_state['table'].iloc[:, :max_columns])
    except:
        pass












