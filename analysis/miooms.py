
import inspect
import sys

import matplotlib.pyplot as plt
import numpy as np
from pylab import *
from scipy.optimize import curve_fit

line="------------------------------"
sigmatofwhm=2*np.sqrt(2*np.log(2))

class printf:
    def __init__(self, format, *args):
        sys.stdout.write(format % args)

def lorentzian( x, x0, amp, gam , back):
    return back + abs(amp) * gam**2 / ( gam**2 + ( x - x0 )**2)

# def gaussian( x, x0, amp, gam , back):
#     return back + (abs(amp)/(sqrt(2*math.pi)*gam)) * exp (-( x - x0 )**2/2*gam**2)

def gaussian(x, x0, amp,sigma,back):
    """ Return a Gaussian with amplitude amp and standard deviation sigma. """
    c = np.sqrt(2 * np.pi)
    return back + amp *np.exp(-0.5 * ((x-x0) / sigma)**2) / sigma / c


########################################
# mass spectrum function
########################################
def tofparams_from_masses(mass1, mass2, time1, time2):
    alpha=(mass1+mass2-2*sqrt(mass1*mass2))/pow(time1-time2,2)
    t0=time1-sqrt(mass1/alpha)
    return alpha,t0
    
########################################
# from an array of m/z values find the closest element for a target mass and return the index
########################################
def find_closest(A, target,Verbose):
    if(Verbose):
        print(line)
        print('Function call: ',inspect.currentframe().f_code.co_name)    
    
    #A must be sorted
    if(A[0]>A[-1]):
        if Verbose:
            print("Array not sorted!")
        B=-A
        target=-target
    else:
        B=A
        
    idx = B.searchsorted(target)
    if(Verbose):
        print("B\t",B)
        print("\t target, idx",target, idx)
    if (Verbose):
        idx = np.clip(idx, 1, len(A)-1)
        print(idx)
        left = B[idx-1]
        right = B[idx]
        print(left,right)
       
        idx -= target - left < right - target
        print(idx)
    if(Verbose):
        print('End function call: ',inspect.currentframe().f_code.co_name)
        print(line)
    return idx

########################################
# from an array of m/z values find the two closest elements for two masses and return the indices
########################################
def find_indices_for_mass_range(mass1,mass2,mz,Verbose):
    if(Verbose):
        print(line)
        print('Function call: ',inspect.currentframe().f_code.co_name)
    masses=mass1,mass2
    index=[]
    i=0
    for mass in masses:
        index.append(find_closest(mz,mass,Verbose))

        if(Verbose):        
            printf("\t index: %d\t mass: %.3f\t closest mass: %.3f\t array size: %d\n",index[i], mass,mz[index[i]],mz.size)
        i=i+1
    a,b = (min(index[0],index[1]),max(index[0],index[1]))
    
    if(Verbose):
        print('a,b',a,b)
        print('End function call: ',inspect.currentframe().f_code.co_name)
        print(line)
    return a,b

########################################
# from an array of m/z values (mz) and matching mass spectrum (ms) find the exact mass of the peak position 
# by fitting a Gaussian or Lorentzian finction.
#
# Returns the fit values of the function
#   popt[0],popt[1],popt[2],popt[3]
#   x0, amp, gam , back
########################################
def find_exactmass(masstarget,mz,ms,massmargin,Verbose):
    ################
    # select small margin to feed to fitting procedure
    ################
    if(Verbose):
        print(line)
        print('Function call: ',inspect.currentframe().f_code.co_name)
    TrulyVerbose=Verbose
    masslo=masstarget-massmargin
    masshi=masstarget+massmargin
    
    a,b = find_indices_for_mass_range(masslo,masshi,mz,Verbose)
    if (TrulyVerbose):
        print("\t a, masslo, b, masshi",a, mz[a],b,mz[b])
        
        print("\t mzsize",len(mz))
        print("\t mz",mz)

    ##############################################################
    # Fit first a Gaussian, if necessary a Lorentzian to peaks
    ##############################################################
    
    xData  = mz[a:b]
    yData=ms[a:b]
    if Verbose:
        print('xData',xData)
        print('yData',yData)
    yData = yData / max(yData)
    
    # Initial guess of the parameters (you must find them some way!)
    amp_guess= yData.max()
    x0_guess= xData[yData.argmax()]
    b_guess=yData.mean()
    width_guess=xData[yData.argmax()]/800.
    pguess = [ x0_guess, amp_guess, width_guess, b_guess]
    
    # Fit the data
    try:
        if Verbose :
            print('\t Fitting a Gaussian')
        popt, pcov = curve_fit(gaussian, xData, yData, p0 = pguess)
        
        perr = np.sqrt(np.diag(pcov))
        if Verbose :
            printf('\t Gaussian fit result: center= %.2f\t%.4f\n',popt[0], perr[0])
        if(perr[0]>0.01): raise ValueError('Covariance too high, fit probably failed')
        
    except:
        if Verbose :
            printf('\t Uh-oh, Lorentzian needed....\n')
        popt, pcov = curve_fit(lorentzian, xData, yData, p0 = pguess)
        perr = np.sqrt(np.diag(pcov))
        if Verbose :
            printf('\t Lorentzian fit result: center= %.2f\t%.4f\n',popt[0], perr[0])
        if(perr[0]>0.01): raise ValueError('Covariance still too high, fit probably failed')
        

    else:
        if Verbose :
            printf('\t Fitting success for %.1f\n ',x0_guess)
 
        
    finally:
        if Verbose :
            f, (ax)=plt.subplots(1, 1, sharey=False, facecolor='w')
            plt.plot(xData,yData,label='exp')
            plt.plot(xData,gaussian(xData,popt[0],popt[1],popt[2],popt[3]),label='fit')
            plt.legend()

            print('End function call: ',inspect.currentframe().f_code.co_name)
            print(line)
        return(popt) 
        #popt[0],popt[1],popt[2],popt[3]
        #x0, amp, gam , back
        
########################################
# from an array of m/z values (mz) and matching mass spectrum (ms) find the exact mass of a given mass target 
# (using find exact mass) and integrated over a given width.

########################################
def integrate_massgate(ms,mz,mass,boxcar,Verbose,label):
    if(Verbose):
        print(line)
        print('Function call: ',inspect.currentframe().f_code.co_name)  

    mlo=float(mass)-0.5*boxcar.bxwidth
    mhi=float(mass)+0.5*boxcar.bxwidth
    i=0
    index=[]
    if(Verbose):
         printf("\t mlo-mhi= %.3f - %.3f\n",mlo,mhi)
    # find the indices
    for gateedge in mlo,mhi:
        index.append(find_closest(mz,gateedge,False))
        i=i+1
    a,b = (min(index[0],index[1]),max(index[0],index[1]))

    
    if(boxcar.showgates):
        #printf("\t a,b \t%d\t%d\t%.3f\t%.3f\twidth%.1f\n",a,b, mz[a],mz[b],width)
        plotrange=range(a-10*(b-a),b+10*(b-a))
        f, (ax)=plt.subplots(1, 1, sharey=False, facecolor='w',figsize=(4,3), dpi= 100)
        plt.rc('font', family='sans-serif') 
        plt.rc('font', serif='Geneva') 
        f.canvas.header_visible = False
        plt.rcParams.update({'font.size': 9})
        plt.tight_layout();
        ax.plot(mz[plotrange],ms[:,plotrange].mean(axis=0),label=label)
        ax.legend()
        ax.text(0.99, 0.85, 'Fit mass: %.3f' %mass, horizontalalignment='right',
                            verticalalignment='top', 
                            transform=ax.transAxes)
        ax.scatter(mz[a:b],ms[:,a:b].mean(axis=0))
         
    if boxcar.bgtype=='offset':
        offset=boxcar.bgoffset
        mlo=float(mass-offset)-0.5*boxcar.bxwidth*boxcar.bgmultiplier
        mhi=float(mass-offset)+0.5*boxcar.bxwidth*boxcar.bgmultiplier
        index=[]
        i=0
        for mass in mlo,mhi:
            index.append(find_closest(mz,mass,False))
            i=i+1  
        c,d = (min(index[0],index[1]),max(index[0],index[1]))
        if(Verbose):
            print('\t c,d: ',c,d)
            cdmin=np.where(ms[:,c:d].mean(axis=0) == ms[:,c:d].mean(axis=0).min())[0]
        if(boxcar.showgates):
            ax.scatter(mz[c:d],ms[:,c:d].mean(axis=0))  
            #print(max(a,b,c,d))
            ax.set_xlim(mz[min(a,b,c,d)-10],mz[max(a,b,c,d)+10])
        if(boxcar.bgaverage):
            return ms[:,a:b].sum(axis=1)-ms[:,c:d].sum(axis=1).mean(axis=0)/boxcar.bgmultiplier
        else:
            return ms[:,a:b].sum(axis=1)-ms[:,c:d].sum(axis=1)/boxcar.bgmultiplier 
    if boxcar.bgtype=='range':
        return ms[:,a:b].mean(axis=1)-ms[:,boxcar.bgrange].mean(axis=1)
    else:
        return ms[:,a:b].sum(axis=1)
    if(Verbose):
    
        print('End function call: ',inspect.currentframe().f_code.co_name)  
        print(line)
  
    
########################################################
def get_integrated_signals_dataframe(allms,mz,masstarget,Verbose,boxcar,label):
    if(len(allms.shape)==3):
        toggle=True
        allir=allms[:,1,:]
        allref=allms[:,0,:]
    if(len(allms.shape)==2):
        toggle=False
        allir=allms

    massmargin=0.1
    massmargin=boxcar.bxtolerance
    DeepVerbose=Verbose
    #Verbose=False
    peakfit=find_exactmass(masstarget,mz,-allir.mean(axis=0),massmargin,DeepVerbose)
    mass=peakfit[0]
    width=sigmatofwhm*peakfit[2]
    massresolution=peakfit[0]/width
    
    if(Verbose):
        printf('Found mass: %.2f\t with width: %.2f\tResolution: %.1f\n',mass,width,massresolution)
    

    if(Verbose):
        print("mass gates","%f" % mass)
    ########################################################
    signal=np.zeros(shape=(allms.shape[0]))
    reference=np.zeros(shape=(allms.shape[0]))
    signal=integrate_massgate(allir,mz,mass,boxcar,Verbose,label)
    if(toggle):
        reference=integrate_massgate(allir,mz,mass,boxcar,Verbose,label) 
    return(signal,reference)