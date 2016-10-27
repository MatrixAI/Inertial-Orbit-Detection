from sine import sine
from scipy.optimize import curve_fit
from scipy.signal import fftconvolve
from scipy.stats import mode
from scipy.interpolate import interp1d
from matplotlib.mlab import find as find_index_by_true
import os
import accelerometers
import rotation_mapping
import graphing
import numpy as np
import logging
import pprint

def analyse_rotation_process(time_delta_ms, orientation, sensor_type, data_window, trace_id):

    logging.info("%d - Starting Window Processing at PID: %d", trace_id, os.getpid())

    logging.debug("%d - Data Window: \n%s", trace_id, str(data_window))

    # these will be used for sampling interpolation, frequency estimation, and sine wave regression
    time_delta_s = time_delta_ms / 1000
    sampling_rate = 1000 / time_delta_ms

    logging.debug("%d - Time Delta Seconds: \n%s", trace_id, pprint.pformat(time_delta_s))
    logging.debug("%d - Sampling Rate: \n%s", trace_id, pprint.pformat(sampling_rate))
    
    # normalise the raw acceleration data to linearly spaced & interpolated data with the given orientation
    norm_data_window = normalise_signals(data_window, time_delta_s, orientation, sensor_type)

    logging.debug("%d - Normalised Data Window: \n%s", trace_id, pprint.pformat(norm_data_window))

    # frequency needs to be estimated before curve fitting
    frequencies = estimate_frequency(norm_data_window, sampling_rate)

    logging.debug("%d - Frequencies: \n%s", trace_id, pprint.pformat(frequencies))

    # non-linear curve fit of a sine curve
    wave_properties = fit_sine_waves(norm_data_window, frequencies)

    logging.debug("%d - Wave Properties: \n%s", trace_id, pprint.pformat(wave_properties))

    # use the acceleration and jerk to vote on the rotational direction
    rotation_direction = estimate_rotation_direction(norm_data_window, frequencies, wave_properties)

    logging.debug("%d - Rotation Direction: \n%s", trace_id, pprint.pformat(rotation_direction))

    return (norm_data_window, frequencies, wave_properties, rotation_direction, time_delta_s, trace_id)

def analyse_rotation_process_callback(channel, graph, processed_package):

    (norm_data_window, frequencies, wave_properties, rotation_direction, time_delta_s, trace_id) = processed_package

    if rotation_direction == 1:
        print("%d - Clockwise Direction" % trace_id)
    elif rotation_direction == -1:
        print("%d - Anticlockwise Direction" % trace_id)
    else:
        print("%d - Unknown Direction" % trace_id)

    rps = (frequencies["east"] + frequencies["up"]) / 2

    print("%d - RPS East: %d" % (trace_id, frequencies["east"]))
    print("%d - RPS Up: %d" % (trace_id, frequencies["up"]))
    print("%d - RPS Average: %d" % (trace_id, rps))

    # non-blocking push into the channel
    # it will overwrite any old data if they haven't been collected
    channel.append((rps, rotation_direction, trace_id))

    if graph:
        graphing.display(graph, norm_data_window, frequencies, wave_properties, time_delta_s)

def normalise_signals(data_window, time_delta_s, orientation, sensor_type):

    # convert to np arrays and convert acceleration units to acceleration m/s^2
    for k, vs in data_window.items():
        if k == 't':
            data_window[k] = np.array(vs)
        else:
            data_window[k] = accelerometers.accel_sensors[sensor_type]["accel_convert_map_np"](np.array(vs))

    # we now have a set of acceleration samples, but they are irregularly 
    # time-spaced because the game controller is a soft realtime system
    # we will regularise the samples by first constructing a linear spaced 
    # set of time, that has the same length as the amount of data but uses 
    # the the desired time delta_s, then since the time samples have 
    # changed, we need to accordingly change the acceleration values via 
    # interpolation

    time_values_s = data_window["t"] / 1000

    # the endpoint is false in order to recreate a half-open interval
    # num is the number of time values to generate in addition to the start value
    # so a half open interval will discount the number by 1
    # thus giving us exactly num number of time values 
    regular_time_values_s = np.linspace(
        start    = time_values_s[0],
        stop     = time_values_s[0] + len(time_values_s) * time_delta_s,
        num      = len(time_values_s),
        endpoint = False
    )

    # time in norm_data_window will be in seconds, not milliseconds
    # for the purposes of orbit, we only care about 2D orbit, so we drop the north axis
    norm_data_window = {
        "time":  None,
        "east":  None,
        "up":    None
    }

    norm_data_window["time"]  = regular_time_values_s

    for axis in ["east", "up"]:

        # the east and up axis depends on fixed orientation of the controller during orbit
        norm_data_window[axis] = data_window[orientation[axis]["axis"]]
        
        # subtracting the mean will translate the curve to be centered at their rotational orbit
        norm_data_window[axis] -= np.mean(norm_data_window[axis])

        # flip values according to the given signs
        if orientation[axis]["sign"] == '-': norm_data_window[axis] *= -1

        # use linear interpolation and allow a bit of extrapolation 
        # extrapolation is because the corrected time could be a bit larger than the sampled time
        interpolated_f = interp1d(
            time_values_s, 
            norm_data_window[axis], 
            bounds_error=False,
            fill_value="extrapolate"
        )

        norm_data_window[axis] = interpolated_f(regular_time_values_s)

    return norm_data_window

def estimate_frequency(norm_data_window, sampling_rate):

    # the inferred frequency is also the rotations per second
    inferred_freq_east  = freq_from_autocorr(norm_data_window['east'],  sampling_rate)
    inferred_freq_up    = freq_from_autocorr(norm_data_window['up'],    sampling_rate)

    return {
        "east": inferred_freq_east,
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

def fit_sine_waves(norm_data_window, frequencies):

    # fix the sine function with the inferred frequency (scipy doesn't like partial functions)
    sine_with_freq_east  = lambda t, a, b, c: sine(frequencies["east"],  t, a, b, c)
    sine_with_freq_up    = lambda t, a, b, c: sine(frequencies["up"],    t, a, b, c)

    # fit the sine curve with a fixed frequency to the time values and the signal
    popt_east, pcov_east = curve_fit(
        sine_with_freq_east, 
        norm_data_window['time'], 
        norm_data_window['east']
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

    return rotational_direction