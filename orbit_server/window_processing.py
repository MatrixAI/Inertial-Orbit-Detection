from scipy.optimize import curve_fit
from scipy.signal import fftconvolve
from scipy.stats import mode
from scipy.interpolate import interp1d
from matplotlib.mlab import find as find_index_by_true
import os
import accelerometers
import rotation_mapping
import numpy as np
import matplotlib.pyplot as plt 
import logging

def create_analyse_rotation_process(time_delta_ms, orientation, sensor_type):

    # these will be used for sampling interpolation, frequency estimation, and sine wave regression
    time_delta_s = time_delta_ms / 1000
    sampling_rate = 1000 / time_delta_ms

    def analyse_rotation_process(data_window):
        
        logging.info("Starting Window Processing Child Process {}", os.getpid())
        
        # normalise the raw acceleration data to linearly spaced & interpolated data with the given orientation
        norm_data_window = normalise_signals(data_window, time_delta_s, orientation, sensor_type)
        # frequency needs to be estimated before curve fitting
        frequencies = estimate_frequency(norm_data_window, sampling_rate)
        # non-linear curve fit of a sine curve
        wave_properties = fit_sine_waves(norm_data_window, frequencies)
        # use the acceleration and jerk to vote on the rotational direction
        rotation_direction = estimate_rotation_direction(norm_data_window, frequencies, wave_properties)

        return (norm_data_window, frequencies, wave_properties, rotation_direction)

    return analyse_rotation_process

def create_analyse_rotation_process_callback(channel):

    def analyse_rotation_process_callback():
        pass

    return analyse_rotation_process_callback

def normalise_signals(data_window, time_delta_s, orientation, sensor_type):

    # to np arrays
    for k, vs in data_window.items():
        if k.lower() == 'x' or k.lower() == 'y' or k.lower() == 'z':
            data_window[k] = accelerometers.accel_sensors[sensor_type]["accel_convert_map_np"](np.array(vs))

    # we will convert the milliseconds into just seconds
    norm_data_window = {
        "time":  None
        "east":  None,
        "north": None,
        "up":    None
    }

    # subtracting the mean will set 0 to the center of the rotational orbit
    # it's just a translation of the entire curve downwards
    norm_data_window["east"] = 
        data_window[orientation["east"]["axis"]] -  np.mean(data_window[orientation["east"]["axis"]])
    norm_data_window["north"] = 
        data_window[orientation["north"]["axis"]] - np.mean(data_window[orientation["north"]["axis"]])
    norm_data_window["up"] = 
        data_window[orientation["up"]["axis"]] -    np.mean(data_window[orientation["up"]["axis"]])

    # flip values according to the given signs
    if orientation["east"]["sign"]  == '-': norm_data_window['east']  *= -1
    if orientation["north"]["sign"] == '-': norm_data_window['north'] *= -1
    if orientation["up"]["sign"]    == '-': norm_data_window['up']    *= -1

    # we now have a set of acceleration samples, but they are irregularly time-spaced because 
    # the game controller may be a soft realtime system
    # in order to normalise into regularly time-spaced samples, we need to use interpolation
    # on the acceleration data, and acquire the new interpolated samples from a corrected time set

    # we will be using seconds from now
    time_values_s = data_window["t"] / 1000

    # the endpoint is false in order to recreate a half-open interval
    # num is the number of time values to generate in addition to the start value
    # so a half open interval will discount the number by 1
    # thus giving us exactly num number of time values    
    corrected_time_values_s = np.linspace(
        start    = time_values_s[0],
        stop     = time_values_s[0] + len(time_values_s) * time_delta_s,
        num      = len(time_values_s),
        endpoint = False
    )

    # use linear interpolation and allow a bit of extrapolation 
    # since the corrected time could be a bit larger than the sampled time
    for axis in ["east", "north", "up"]:
        interpolated_f = interp1d(
            norm_data_window[axis], 
            time_values_s, 
            bounds_error=False,
            fill_value="extrapolate"
        )
        norm_data_window[axis]  = interpolated_f(corrected_time_values_s)

    norm_data_window['time']  = corrected_time_values_s

    return norm_data_window

def estimate_frequency(norm_data_window, sampling_rate):

    # the inferred frequency is also the rotations per second
    inferred_freq_east  = freq_from_autocorr(norm_data_window['east'],  sampling_rate)
    inferred_freq_north = freq_from_autocorr(norm_data_window['north'], sampling_rate)
    inferred_freq_up    = freq_from_autocorr(norm_data_window['up'],    sampling_rate)

    return {
        "east": inferred_freq_east,
        "north": inferred_freq_north,
        "up": inferred_freq_up
    }

def freq_from_autocorr(signal, sampling_rate):
    
    corr = fftconvolve(signal, signal[::-1], mode='full')
    corr = corr[len(corr)//2:]
    d = np.diff(corr)
    start = find_index_by_true(d > 0)[0]
    peak = np.argmax(corr[start:]) + start
    px, py = parabolic(corr, peak)
    return sampling_rate / px

def parabolic(f, x):
    
    xv = 1/2. * (f[x-1] - f[x+1]) / (f[x-1] - 2 * f[x] + f[x+1]) + x
    yv = f[x] - 1/4. * (f[x-1] - f[x+1]) * (xv - x)
    return (xv, yv)

def fit_sine_waves(norm_data_window, frequencies)

    # fix the sine function with the inferred frequency (scipy doesn't like partial functions)
    sine_with_freq_east  = lambda t, a, b, c: sine(frequencies["east"],  t, a, b, c)
    sine_with_freq_north = lambda t, a, b, c: sine(frequencies["north"], t, a, b, c)
    sine_with_freq_up    = lambda t, a, b, c: sine(frequencies["up"],    t, a, b, c)

    # fit the sine curve with a fixed frequency to the time values and the signal
    popt_east, pcov_east = curve_fit(
        sine_with_freq_east, 
        norm_data_window['time'], 
        norm_data_window['east']
    )
    popt_north, pcov_north = curve_fit(
        sine_with_freq_north, 
        norm_data_window['time'], 
        norm_data_window['north']
    )
    popt_up, pcov_up = curve_fit(
        sine_with_freq_up, 
        norm_data_window['time'], 
        norm_data_window['up']
    )

    return {
        "east": {
            "popt": popt_east,
            "pcov": pcov_east
        },
        "north": {
            "popt": popt_north,
            "pcov": pcov_north 
        },
        "up": {
            "popt": popt_up,
            "pcov": pcov_up
        }
    }

def estimate_rotation_direction(norm_data_window, frequencies, wave_properties):

    # we only need the east and up data to detect rotation

    # we need to use the fitted functions to get the approximated acceleration vector values
    fitted_east_sine = lambda ts: sine(
        frequencies["east"], 
        ts, 
        wave_properties["east"]["popt"][0], 
        wave_properties["east"]["popt"][1], 
        wave_properties["east"]["popt"][2]
    )
    fitted_up_sine = lambda ts: sine(
        frequencies["up"], 
        ts, 
        wave_properties["up"]["popt"][0], 
        wave_properties["up"]["popt"][1], 
        wave_properties["up"]["popt"][2]
    )
    
    # zip up the east and up accelerations into vectors for every time instant from the fitted sine function
    # creates an array of [[East Accel, Up Accel], [East Accel, Up Accel], ...]
    acceleration_vectors = list(
        zip(
            fitted_east_sine(norm_data_window['time']), 
            fitted_up_sine(norm_data_window['time'])
        )
    )

    # acquire the change in acceleration vector for each time interval
    # relies on element-wise subtraction of left shifted and right shifted acceleration_vectors
    acceleration_vector_deltas = np.subtract(acceleration_vectors[1:], acceleration_vectors[:-1])

    # map the acceleration_vector_deltas to directions
    acceleration_vector_delta_directions = []
    for signs in np.sign(acceleration_vector_deltas):
        acceleration_vector_delta_directions.append(
            rotation_mapping.accel_vector_delta_direction_mapping[tuple(signs)]
        )

    # map the acceleration_vectors to positions
    acceleration_vector_positions = []
    for signs in np.sign(acceleration_vectors):
        acceleration_vector_positions.append(
            rotation_mapping.accel_vector_position_mapping[tuple(signs)]
        )

    # zip up the directions with the positions
    # for example: [ ['NE', 'LB'], [ 'SW', 'RT'], ... ]
    # then produce a list of inferred rotational directions
    # for example: [ 1, 1, 1, 0, -1, -1, 1] where 1: C, -1: AC and 0: ?
    rotational_directions = []
    for dir_and_pos in zip(acceleration_vector_delta_directions, acceleration_vector_positions):
        rotational_directions.append(
            rotation_mapping.accel_vector_direction_and_position_mapping.get(dir_and_pos, 0)
        )

    # most common direction (vote on the majority inferred rotational direction)
    rotational_direction = mode(rotational_directions)[0][0]