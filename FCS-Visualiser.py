# Imports
import configparser
import streamlit as st
import tkinter as tk
from tkinter import filedialog
import glob
from modules.calibration import load_data
import modules
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
if  defaults.read('defaults.ini') == []:
    modules.setup(defaults)
    


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
    st.session_state['data_loc'] = []
if 'dataframe' not in st.session_state:
    st.session_state['dataframe'] = pd.DataFrame({'time': [],
                                                'mass': [],
                                                'mass_element': [],
                                                'voltage': [],
                                                'name': []})
    

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
def gen_df(data_directory, first=False):
    init_param = [st.session_state['a'], st.session_state['k']]
    data = load_data(data_directory, 'Co', init_param, prominence=st.session_state['prominence'])
    if first:
        st.session_state['a'], st.session_state['k'] = data.optimise(threshold=0.001)
        data.calibrate(st.session_state['a'], st.session_state['k'])
        characterisation, table = data.characterise()
        characterisation = characterisation[:, 0]
        st.session_state['table'] = table
        st.session_state['characterisation'] = characterisation
        st.session_state['peaks'] = data.peaks
    else:
        data.calibrate(st.session_state['a'], st.session_state['k'])  
        
    df = pd.DataFrame({'time': data.time,
                       'mass': data.mass,
                       'mass_element': data.mass_element,
                       'voltage': data.voltage,
                       'name': [data_directory[directory_length+6:]]*len(data.time)})
    return df

directory_length = len(st.session_state['directory'])
selected_data = st.multiselect("Select Data", 
                               [file_name[directory_length+6:] for file_name in all_files])
if selected_data != []:
    for i, data in enumerate(selected_data):
        selected_data[i] = all_files[0][:directory_length+6] + data

if (selected_data != st.session_state['data_loc'] or
    prominence != st.session_state['prominence']):   # New data selected
    st.session_state['data_loc'] = selected_data
    st.session_state['prominence'] = prominence

    for i, data in enumerate(selected_data):
        if i == 0:
            st.session_state['dataframe'] = gen_df(data, True)
        else:
            st.session_state['dataframe'] = pd.concat([st.session_state['dataframe'], gen_df(data)])
      


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
            xaxis=dict(showgrid=True))
        
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

    if spectrum_type == 'time':
        fig = px.line(st.session_state['dataframe'], x='time', y='voltage', color='name')
        prepare_axes('time (us)', 'accumulated voltage (V)')
        show_peak_lines(spectrum_type)
    elif spectrum_type == 'mass':
        fig = px.line(st.session_state['dataframe'], x='mass', y='voltage', color='name')
        prepare_axes('mass (amu)', 'accumulated voltage (V)')
        show_peak_lines(spectrum_type)
    else:
        fig = px.line(st.session_state['dataframe'], x='mass_element', y='voltage', color='name')
        prepare_axes('mass (Co)', 'accumulated voltage (V)')
        show_peak_lines(spectrum_type)
    
    if pointer:
        fig.add_vline(pointer_value, line_dash="dash", line_color="red")
    
    return fig

    
if selected_data != []:
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
        with st.container(border = True):
            pointer = st.toggle('Pointer')
            pointer_value = st.number_input('Pointer',
                                            st.session_state['dataframe'][spectrum_type].iloc[0], 
                                            st.session_state['dataframe'][spectrum_type].iloc[-1], 
                                            label_visibility='collapsed')  
    with col1:
        fig = generate_fig()
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












