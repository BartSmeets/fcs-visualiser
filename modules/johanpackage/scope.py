"""
Functions to control the MDO34 Scope
"""

import pyvisa
import numpy as np
import configparser
from struct import unpack 

configfn = "channelassignments.ini"
configchn = configparser.ConfigParser()
configchn.read(configfn)
rm = pyvisa.ResourceManager()
res = rm.list_resources()

def findport_scope(portnu, snnu):
    '''
    Function to look whether scope port is available

    ### ARGUMENTS:
    - portnu: port number
    - snnu: serial number

    ### RETURNS:
    - foundport: string of the port name
    '''
    # List comprehension to find all strings containing the port number
    foundport=[string for string in res if portnu in string]
    
    # If only one occurence is found, update foundport
    if len(foundport) == 1:
        foundport=str(foundport[0])
        # Check if serial number matches
        scope = rm.open_resource(foundport)
        idn=scope.query("*IDN?")
        if snnu in idn:
            print("The scope with serial number " + snnu + " was found")
        else:
            print("WARNING: Scope with serial number  " + snnu + " was NOT found. But since there is only one scope found, I am using:")
            print(idn)
        scope.close()

    # If multiple occurences are found
    elif len(foundport)>1:
        # Try if any of the ports matches the serial number
        for port in foundport:
            try:
                scope = rm.open_resource(port)
                idn = scope.query("*IDN?")
                # Port matches serial number
                if snnu in idn:                    
                    foundport = port
                    scope.close()
                    break
                scope.close()
                # Print a warning message
            except pyvisa.errors.VisaIOError:
                print("WARNING!! I am failing to connect to " + port + 
                        ", maybe there is still an old scope listed in the resource list, I am trying the next device")
        # Raise error if after trying all ports no match is found
        if foundport != port:
            raise IndexError("WARNING: Scope with serial number " + snnu + " was NOT found. \
                            \n And since there are multiple scopes connected, I cannot just act like I don't care and connect to another scope. \
                            \n Check the scopes' serial numbers in the file \"channelassignments.ini\". \
                            \n Compare those with the one listed in the Help->About menu of the scope.")
    
    # If no occurence is found
    else:
        # Raise error
        raise ValueError("No ports named " + portnu + " found.")
        
    # Print and return the result
    print("Using port " + foundport+" \n")
    return foundport


def initialise(port,SN):
    '''
    Initialise scope object

    ### ARGUMENTS:
    - port: port
    - SN: serial number

    ### RETRUNS:
    - scope: scope object
    '''

    # Initialise scope
    sn=configchn.get("PORTS",SN)
    scopePort=configchn.get("PORTS",port)
    foundscopePort=findport_scope(scopePort,sn)
    scope = rm.open_resource(foundscopePort)
    print(scope.query("*IDN?"))

    # Initialise settings
    triggersourcechannel=configchn.get("SCOPE","Trigger"+port[5:])
    scope.write('TRIGGER:A:EDGE:SOURCE ' + triggersourcechannel)    # Source channel for the A edge trigger
    scope.write('HORizontal:DELay:MODe OFF')    # No horizontal delay
    scope.write('HORizontal:POSition 10')   # Horizontal position in %
    scope.write(':HEAD 0')  # Header off
    return scope


def read(channel,scope):
    """
    Reads the scope

    ### ARGUMENTS:
    - channel: scope channel
    - scope: scope object

    ### RETURNS:
    - numpy array of (time, volts)
    """

    # Specify the format and location of the transferred waveform data
    scope.write(':DATA:SOUrce ' + channel)  # Selects the channel
    scope.write(':DATA:WIDTH 1')    # Width in byte per point
    scope.write('DATa:Stop 10000000')   # Set the number of data points to the maximum record length
    scope.write(':DATA:ENC RPB')    # Encoding format

    # Information needed to interpret the waveform data point
    ymult = float(scope.query(':WFMPRE:YMULT?'))    # vertical scale multiplying factor
    yzero = float(scope.query(':WFMPRE:YZERO?'))    # vertical offset of the source waveform
    yoff = float(scope.query(':WFMPRE:YOFF?'))  # vertical position of the source waveform in digitising levels (25 digitising levels per vertical division)
    t_scale = float(scope.query(':WFMPRE:XINCR?'))    # horizontal point spacing in time
    wfm_record = int(scope.query('wfmoutpre:nr_pt?'))   # Number of data points
    t_sub = float(scope.query('wfmoutpre:xzero?')) # time coordinate of first data point
    pre_trig_record = int(scope.query('wfmoutpre:pt_off?')) # Checks if DATA:SOURCE is on or displayed -> generates error if false, 0 if true

    # Transfer waveform data
    bin_wave=scope.query_binary_values('curve?', datatype='b', container=np.array)

    # Interpret waveform data
    ## X-axis: time
    total_time = t_scale * wfm_record
    t_start = (-pre_trig_record * t_scale) + t_sub
    t_stop = t_start + total_time
    ## Y-axis: volts
    ADC_wave = bin_wave # [headerlen:-1] header is off
    ADC_wave = np.array(unpack('%sB' % len(ADC_wave),ADC_wave))
    Volts = (ADC_wave - yoff) * ymult  + yzero
    ## Match dimensions: Exactly one time mark for every datapoint
    scaled_time = np.arange(t_stop-t_scale*len(Volts), t_stop,t_scale)
    
    return(np.transpose([scaled_time,Volts]))


def runstop(runstop,scope):
    '''
    Runs or stops the scope depending on the command

    ### ARGUMENTS:
    - runstop: command (either 'run' or something else, in which case 'stop')
    '''

    # Check command and message scope
    if runstop.upper()=='RUN':
        scope.write(':ACQUIRE:STATE RUN')
    else:
        scope.write(':ACQUIRE:STATE STOP')
    return


def setMicPdiv(micpdiv,scope):
    '''
    Set the horizontal time scale (us per div)

    ### ARGUMENTS:
    - micpdiv: target time scale (us per div)
    - scope: scope object
    '''

    # Message scope
    scope.write(':HOR:SCA '+str(micpdiv)+"E-6")
    return


def getMicPdiv(scope):
    '''
    Read the horizontal time scale (us per div)

    ### ARGUMENTS:
    - scope: scope object
    '''

    # Read scope
    micpdiv=scope.query(':HOR:SCA?')
    micpdiv=float(micpdiv)*1.e6 # s to us
    return micpdiv


def setSampleMode(scope):
    '''
    Set scope to manual mode

    ### ARGUMENTS:
    - scope: scope object
    '''

    # Message scope
    scope.write(':ACQUIRE:MODE SAMPLE')
    return


def setNumAvg(switchaverage,scope):
    '''
    Set the number of averages

    ### ARGUMENTS:
    - switchaverage: the number of averages for the scope to take
    - scope: scope object
    '''

    # Check if sampling mode is requested
    if switchaverage > 1:
        # Message scope
        scope.write(':ACQUIRE:MODE AVERAGE') 
        scope.write(':ACQUIRE:NUMAVG '+str(switchaverage))
    else:
        setSampleMode(scope)
    return