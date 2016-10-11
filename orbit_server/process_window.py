import os
import accelerometers
import numpy as np
from matplotlib.mlab import find as find_index_by_true
from scipy.optimize import curve_fit
from scipy.signal import fftconvolve
from scipy.stats import mode
import matplotlib.pyplot as plt 

def normalise_signals(data_window, signal_delta_time_s):

    # to np arrays
    for k, vs in data_window.items():
        if k.lower() == 'x' or k.lower() == 'y' or k.lower() == 'z':
            data_window[k] = accelerometers[""]["accel_convert_map_np"](np.array(vs))

    # to ENU
    east_axis_match = re.match(axis_regex, rotational_east_axis)
    north_axis_match = re.match(axis_regex, rotational_north_axis)
    up_axis_match = re.match(axis_regex, rotational_up_axis)

    east_sign = east_axis_match.group(1)
    east_axis = east_axis_match.group(2)
    north_sign = north_axis_match.group(1)
    north_axis = north_axis_match.group(2)
    up_sign = up_axis_match.group(1)
    up_axis = up_axis_match.group(2)

    normalised_data_window = {}

    # to baseline
    normalised_data_window['east'] = data_window[east_axis.lower()] - np.mean(data_window[east_axis.lower()])
    normalised_data_window['north'] = data_window[north_axis.lower()] - np.mean(data_window[north_axis.lower()])
    normalised_data_window['up'] = data_window[up_axis.lower()] - np.mean(data_window[up_axis.lower()])

    # to signs
    if east_sign == '-': normalised_data_window['east'] *= -1
    if north_sign == '-': normalised_data_window['north'] *= -1
    if up_sign == '-': normalised_data_window['up'] *= -1

    # to corrected time
    corrected_time_start_s = data_window['t'][0] / 1000
    # the endpoint is false in order to recreate a half-open interval
    # num is the number of time values to generate in addition to the start value
    # so a half open interval will discount the number by 1
    # thus giving us exactly num number of time values    
    corrected_time_values_s = np.linspace(
        start=corrected_time_start_s,
        stop=corrected_time_start_s + len(data_window['t']) * signal_delta_time_s,
        num=len(data_window['t']),
        endpoint=False
    )

    normalised_data_window['time'] = corrected_time_values_s

    return normalised_data_window

def parabolic(f, x):
    
    xv = 1/2. * (f[x-1] - f[x+1]) / (f[x-1] - 2 * f[x] + f[x+1]) + x
    yv = f[x] - 1/4. * (f[x-1] - f[x+1]) * (xv - x)
    return (xv, yv)

def freq_from_autocorr(signal, sampling_rate):
    
    corr = fftconvolve(signal, signal[::-1], mode='full')
    corr = corr[len(corr)//2:]
    d = np.diff(corr)
    start = find_index_by_true(d > 0)[0]
    peak = np.argmax(corr[start:]) + start
    px, py = parabolic(corr, peak)
    return sampling_rate / px