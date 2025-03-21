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
    page_icon="https://static-00.iconduck.com/assets.00/python-icon-512x509-pb65l7gl.png")
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
if 'prominence' not in st.session_state:
    st.session_state['prominence'] = 1
if 'a' not in st.session_state:
    st.session_state['a'] = defaults['calibration']['a']
if 'k' not in st.session_state:
    st.session_state['k'] = defaults['calibration']['k']
if 'data' not in st.session_state:
    st.session_state['data'] = []
if 'old_data' not in st.session_state:
    st.session_state['old_data'] = []
if 'calibration_data' not in st.session_state:
    st.session_state['calibration_data'] = None
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
    directory_length = len(st.session_state['directory'])
    file_location = st.session_state['directory'] + "//*" + file_extension
    all_files = glob.glob(file_location)
    	

# Data Selection
# Define data structure
def gen_df(): 
    init_param = [st.session_state['a'], st.session_state['k']]
    st.session_state['dataframe'] = pd.DataFrame({'time': [],
                                                'mass': [],
                                                'mass_element': [],
                                                'voltage': [],
                                                'norm': [],
                                                'name': []})  
    for name in st.session_state['data']:
        directory = all_files[0][:directory_length+6] + name
        data = load_data(directory, 'Co', init_param, prominence=st.session_state['prominence'], lam=lam, multiplier=multiplier, baseline_data=st.session_state['baseline'])
        try:
            data = load_data(directory, 'Co', init_param, prominence=st.session_state['prominence'], lam=lam, multiplier=multiplier, baseline_data=st.session_state['baseline'])
            df = pd.DataFrame({'time': data.time,
                        'mass': data.mass,
                        'mass_element': data.mass_element,
                        'voltage': data.voltage,
                        'norm': data.norm,
                        'name': [name]*len(data.time)})
        except OSError:
            return
        
        if name == st.session_state['data'][0]:
            characterisation, table = data.characterise()
            characterisation = characterisation[:, 0]
            st.session_state['table'] = table
            st.session_state['characterisation'] = characterisation
            st.session_state['peaks'] = data.peaks
            st.session_state['calibration_data'] = data

        if hasattr(data, 'baseline'):
            df['baseline'] = data.baseline
           
        st.session_state['dataframe'] = pd.concat([st.session_state['dataframe'], df])
            
# Prominence Slider and Calibration Parameters
def optimise():
    st.session_state['a'], st.session_state['k'] = st.session_state['calibration_data'].optimise(
            st.session_state['a'], st.session_state['k'], threshold=0.001)
    try:
        st.session_state['a'], st.session_state['k'] = st.session_state['calibration_data'].optimise(
            st.session_state['a'], st.session_state['k'], threshold=0.001)
    except ValueError:
        st.warning('No peaks detected for optimisation')
    except AttributeError:
        st.warning('No data selected')

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


with st.sidebar:
    # Peak Detection and Mass Calibration
    with st.container(border=True):
        dummy = np.arange(1, 10, 1)
        prominence_steps = np.concatenate((dummy/1000, dummy/100, dummy/10, dummy, dummy*10))

        st.write("## Peak Detection & Mass Calibration")
        st.session_state['prominence'] = st.select_slider("Peak Prominence", options=prominence_steps, value=1)
        st.write('### Mass Calibration')
        st.write('$m = a(t-k)^2$')

        col1, col2 = st.columns(2)
        with col1:
            st.session_state['a'] = st.number_input("a", min_value=0.0, step=1e-8, value=st.session_state['a'], format='%.8f')
            st.button('Auto-Calibrate', on_click=optimise, disabled=True)
                
        with col2:
            st.session_state['k'] = st.number_input("k", step=1e-8, value=st.session_state['k'], format='%.8f')
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
        
    def show_peak_lines(index):
        if peak_detection or show_tag:
            for i, peak in enumerate(st.session_state['peaks']):
                dataframe = st.session_state['dataframe']
                x_axis = dataframe[index]
                x_axis = x_axis[dataframe['name'] == dataframe['name'].iloc[0]]
                if 'Ar' in st.session_state['characterisation'][i] and show_tag:
                    fig.add_vline(x_axis.iloc[peak], line_dash="dash", line_color='blue', opacity=0.25)
                elif peak_detection:
                    fig.add_vline(x_axis.iloc[peak], line_dash='dot', line_color='grey', opacity=0.25)
    
    if normalise:
        y_axis = 'norm'
    else:
        y_axis = 'voltage'
    
    if spectrum_type == 'time':
        fig = px.line(st.session_state['dataframe'], x='time', y=y_axis, color='name')
        prepare_axes('time (us)', 'accumulated voltage (V)')
        show_peak_lines(spectrum_type)
    elif spectrum_type == 'mass':
        fig = px.line(st.session_state['dataframe'], x='mass', y=y_axis, color='name')
        prepare_axes('mass (amu)', 'accumulated voltage (V)')
        show_peak_lines(spectrum_type)
    else:
        fig = px.line(st.session_state['dataframe'], x='mass_element', y=y_axis, color='name')
        prepare_axes('mass (Co)', 'accumulated voltage (V)')
        show_peak_lines(spectrum_type)
    
    if pointer:
        fig.add_vline(pointer_value, line_dash="dash", line_color="red")
    
    return fig

    
if st.session_state['data'] != []:
    ## Input
    col1, col2 = st.columns([3, 1])
    with col2:
        SPECTRUM_DICT = {'Time': 'time',
                         'Mass (amu)': 'mass',
                         'Mass (Co)': 'mass_element'}
        spectrum_type = st.selectbox('Spectrum Type', ['Time', 'Mass (amu)', 'Mass (Co)'])
        spectrum_type = SPECTRUM_DICT[spectrum_type]
        peak_detection = st.toggle('Peak Detection')
        show_tag = st.toggle('Show Tag')
        normalise = st.toggle('Normalise')

        with st.container(border = True):
            pointer = st.toggle('Pointer')
            pointer_value = st.number_input('Pointer',
                                            st.session_state['dataframe'][spectrum_type].iloc[0], 
                                            st.session_state['dataframe'][spectrum_type].iloc[-1], 
                                            label_visibility='collapsed')  
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












