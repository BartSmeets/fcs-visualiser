import streamlit as st
import pandas as pd
import numpy as np
import json
import itertools as iter

def generate():
    ranges = [range(count + 1) for count in st.session_state['dict']['max count']]
    combinations = list(iter.product(*ranges))
    output_dict = dict()
    dump_elements = st.session_state['dict']['element'].to_json(orient='values')
    dump_counts = st.session_state['dict']['max count'].to_json(orient='values')
    general = {'elements': dump_elements, 
               'max_count': dump_counts}

    for combination in combinations:
        mass = 0
        name = ''
        for element, count in zip(st.session_state['dict']['element'], combination):
            mass += count * element_dict.loc[element_dict['Symbol'] == element, 'AtomicMass'].values[0]
            name += (element + str(count))
        output_dict[name] = mass

    with open('dictionary.json', 'w') as file:
        list_of_dicts = [general, {'masses':output_dict}]
        json.dump(list_of_dicts, file, indent=4)

    
    return output_dict

with open('dictionary.json', 'r') as file:
    dictionary = json.load(file)
element_dict = pd.read_csv('PubChemElements_all.csv', usecols=['Symbol', 'AtomicMass'])


st.write('# Dictionary')

elements = dictionary['elements']
max_count = dictionary['max_count']

if 'dict' not in st.session_state:
    st.session_state['dict'] = pd.DataFrame()
    st.session_state['dict']['element'] = elements
    st.session_state['dict']['max count'] = max_count

st.session_state['dict'] = st.data_editor(st.session_state['dict'])

with st.sidebar:
    with st.container(border=True):
        st.write('### Add or Delete Row')
        col1, col2 = st.columns(2)
        with col1:
            def add_row():
                st.session_state['dict'].loc[len(st.session_state['dict'].index)] = ['H','0']
            st.button("➕", on_click=add_row)
        with col2:
            def del_row():
                try:
                    st.session_state['dict'] = st.session_state['dict'].drop(st.session_state['dict'].index[-1])
                except IndexError:
                    print('Cannot do that')
            st.button("➖", on_click=del_row)
    if st.button("Save"):
            molecules = generate()
            pass    # Work in Progress
            


        

