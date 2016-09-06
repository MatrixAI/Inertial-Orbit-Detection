#!/usr/bin/env python3

import os
import csv 
import sys
import serial
import re
import time
import numpy as np
import matplotlib.pyplot as plt 
from copy import deepcopy
from functools import partial
from matplotlib.mlab import find as find_index_by_true
from scipy.optimize import curve_fit
from scipy.signal import fftconvolve
from multiprocessing import Pool 

# these are acquired from http://www.freetronics.com.au/pages/am3x-quickstart-guide
# these will be used to vertically normalise the acceleration readings to the 0-axis
# these can be tuned from outside too
# assume 1.5 g mode
VOLTAGE_BASE = 1.65
VOLTAGE_MAX = 5
VOLTAGE_PER_G = 0.8
GRAVITY = 9.8
ACCELERATION_UNIT_MAX = 1023
def acceleration_conversion (acceleration_unit):
    acceleration_voltage = acceleration_unit / (ACCELERATION_UNIT_MAX / VOLTAGE_MAX)
    acceleration = ((acceleration_voltage - VOLTAGE_BASE) / VOLTAGE_PER_G) * GRAVITY
    return acceleration
ACCELERATION_MAX = acceleration_conversion(ACCELERATION_UNIT_MAX)
acceleration_conversion_map = np.vectorize(acceleration_conversion)

# Assume our local reference frame for the device is ENU oriented.
# This is marked on the device with X and Y and Z arrows.
#
# East  is X
# North is Y
# Up    is Z
#
# We only care about East and Up for our rotational game.
# 
# By default, you should use this:
# 
# rotational_east_axis == '+x'
# rotational_up_axis == '+z'

device_path = sys.argv[1]
baud_rate = int(sys.argv[2])
rotational_east_axis = sys.argv[3] # this needs to be '+x'
rotational_north_axis = sys.argv[4] # this needs to be '+y'
rotational_up_axis = sys.argv[5] # this needs to be '+z'
time_window_ms = int(sys.argv[6])
delta_time_ms = int(sys.argv[7])

delta_time_s = delta_time_ms / 1000
sampling_rate = 1000 / delta_time_ms

message_regex = re.compile('^Time.(\d+).X.(\d+).Y.(\d+).Z.(\d+)', re.I)
axis_regex = re.compile('([+-])([xyz])', re.I)

def normalise_signals(data_window, signal_delta_time_s):

    # to np arrays
    for k, vs in data_window.items():
        data_window[k] = acceleration_conversion_map(np.array(vs))

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

def sine (freq, time, amp, phase, vertical_disp):    
    return amp * np.sin(freq * 2 * np.pi * time + phase) + vertical_disp

def process_curve_fit(data_window):
    
    # this function is to be executed asynchronously
    print("Child Process #%d" % os.getpid())

    # normalise raw signals
    normalised_data_window = normalise_signals(data_window, delta_time_s)
    
    # inferred_freq is also the rotations per second
    inferred_freq = freq_from_autocorr(normalised_data_window['east'], sampling_rate)

    # fix the sine function with the inferred frequency (scipy doesn't like partial functions)
    sine_with_freq = lambda t, a, b, c: sine(inferred_freq, t, a, b, c)

    # fit the sine curve with a fixed frequency to the time values and the signal
    popt, pcov = curve_fit(sine_with_freq, normalised_data_window['time'], normalised_data_window['east'])

    return (popt, pcov, inferred_freq, normalised_data_window)


plt.ion()
axes = plt.gca()
axes.set_xlabel('Time (s)')
axes.set_ylabel('Accleration (m/s^2)')
plt.ylim(-(ACCELERATION_MAX / 2), ACCELERATION_MAX / 2)
plt_zero_line, = plt.plot([], [], 'c-')
plot_east_data, = plt.plot([], [], 'r.')
plot_east_curve, = plt.plot([], [], 'r-')
# plot_north_data, = plt.plot([], [], 'g.')
# plot_north_curve, = plt.plot([], [], 'g-')
# plot_up_data, = plt.plot([], [], 'b.')
# plot_up_curve, = plt.plot([], [], 'b-')

def display(display_data):

    # potential race condition here.. we need to lock access to the GUI, so the display updates are queued up or dropped

    (popt, pcov, frequency, normalised_data_window) = display_data

    plt.xlim(normalised_data_window['time'][0], normalised_data_window['time'][-1])

    plt_zero_line.set_xdata(normalised_data_window['time'])
    plt_zero_line.set_ydata(normalised_data_window['time'] * 0)

    plot_east_data.set_xdata(normalised_data_window['time'])
    plot_east_data.set_ydata(normalised_data_window['east'])

    plot_east_curve.set_xdata(normalised_data_window['time'])
    plot_east_curve.set_ydata( 
        sine(
            frequency, 
            normalised_data_window['time'], 
            popt[0], 
            popt[1], 
            popt[2]
        )
    )

    plt.draw()

    print("RPS: " + str(frequency))

sensor = serial.Serial(device_path, baud_rate)
sensor.reset_input_buffer()
sensor.reset_output_buffer()

print("Waiting for device to be ready...")
sensor.timeout = None    
if sensor.readline() != b"Ready!\n":
    print("Device was not ready! Exiting!")
    exit(1)
sensor.timeout = 1
print("Device is ready!")

# starting 1 child process
pool = Pool(processes=1)

print("Starting Analysis!")
sensor.write(b'1')

data_window_start_ms = None
data_window = {
    't': [],
    'x': [],
    'y': [],
    'z': []
}
while(True):

    # if the starting_byte is not S, discard it until we reach an S
    starting_byte = sensor.read(1)

    if starting_byte != b"S":
        continue

    # read a byte until we reach an E
    intermediate_byte = sensor.read(1)
    message_buffer = b"" 
    while (intermediate_byte != b"E"):
        message_buffer += intermediate_byte
        intermediate_byte = sensor.read(1)

    # now we have the message buffer
    # start from Time 'T'
    message_buffer = message_buffer.decode("utf-8")

    coordinates = re.match(message_regex, message_buffer)

    if coordinates is None:
        continue

    reading_time_ms = int(coordinates.group(1))
    reading_x_accel = int(coordinates.group(2)) 
    reading_y_accel = int(coordinates.group(3))
    reading_z_accel = int(coordinates.group(4))

    if (data_window_start_ms is not None and (data_window_start_ms + time_window_ms >= reading_time_ms)):

        data_window['t'].append(reading_time_ms)
        data_window['x'].append(reading_x_accel)
        data_window['y'].append(reading_y_accel)
        data_window['z'].append(reading_z_accel)

    else:

        # if we have started a data window
        # then this means this is the end of a data window
        # we must asynchronously process the data window
        if (data_window_start_ms is not None):
            print("Processing Data Window at Time: %d" % data_window_start_ms)
            pool.apply_async(process_curve_fit, args=(deepcopy(data_window),), callback=display)
        
        # start a new window
        data_window_start_ms = reading_time_ms
        data_window['t'] = [reading_time_ms]
        data_window['x'] = [reading_x_accel]
        data_window['y'] = [reading_y_accel]
        data_window['z'] = [reading_z_accel]
