#!/usr/bin/env python3

import os
import re
import csv 
import sys
import serial
import threading
import socketserver
import signal as unix_signals
import numpy as np
import matplotlib.pyplot as plt 
from copy import deepcopy
from matplotlib.mlab import find as find_index_by_true
from scipy.optimize import curve_fit
from scipy.signal import fftconvolve
from scipy.stats import mode
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
host = sys.argv[8]
port = int(sys.argv[9])

delta_time_s = delta_time_ms / 1000
sampling_rate = 1000 / delta_time_ms

message_regex = re.compile('^Time.(\d+).X.(\d+).Y.(\d+).Z.(\d+)', re.I)
axis_regex = re.compile('([+-])([xyz])', re.I)

output_direction = 0
output_rps = 0.0

# This is mapping from the sign of the acceleration vector deltas to rotational tangent direction.
# The keys are in the form of (East Axis Delta Sign, Up Axis Delta Sign).
#
# +,+ => NE
# +,- => SE
# -,- => SW
# -,+ => NW
# 0,+ => N
# 0,- => S
# +,0 => E
# -,0 => W
# 0,0 => ?
acceleration_vector_delta_direction_mapping = {
    (1 ,  1): 'NE',
    (1 , -1): 'SE',
    (-1, -1): 'SW',
    (-1,  1): 'NW',
    (0 ,  1): 'N',
    (0 , -1): 'S',
    (1 ,  0): 'E',
    (-1,  0): 'W',
    (0 ,  0): '?'
}

# This is mapping from the sign of the acceleration vector to rotational position.
# The keys are in the form of (East Axis Sign, Up Axis Sign).
# 
# +,+ => Left Bottom Quadrant
# +,- => Left Top Quadrant
# -,- => Right Top Quadrant
# -,+ => Right Bottom Quadrant
# 0,+ => Bottom Semicircle
# 0,- => Top Semicircle
# +,0 => Left Semicircle
# -,0 => Right Semicircle
# 0,0 => ?
acceleration_vector_position_mapping = {
    (1 ,  1): 'LB',
    (1 , -1): 'LT',
    (-1, -1): 'RT',
    (-1,  1): 'RB',
    (0 ,  1): 'B',
    (0 , -1): 'T',
    (1 ,  0): 'L',
    (-1,  0): 'R',
    (0 ,  0): '?'
}

# This is a mapping from:
#   1. acceleration vector delta direction
#   2. acceleration vector position 
# to clockwise or anti-clockwise.
# 1 represents clockwise.
# -1 represents anticlockwise.
# The opposite of the acceleration vector delta direction is the tangential rotational direction.
# 
# NE - LT => anticlockwise
# NE - RB => clockwise
# NE - L  => anticlockwise
# NE - B  => clockwise
# NE - *  => ?
#  
# SE - LB => clockwise
# SE - RT => anticlockwise
# SE - L  => clockwise
# SE - T  => anticlockwise
# SE - *  => ?
# 
# SW - LT => clockwise
# SW - RB => anticlockwise
# SW - R  => anticlockwise
# SW - T  => clockwise
# SW - *  => ?
# 
# NW - RT => clockwise
# NW - LB => anticlockwise
# NW - R  => clockwise
# NW - B  => anticlockwise
# NW - *  => ?
# 
# (all of these below is rare or impossible because it requires T1 and T2 to be at the same position)
# 
# N - L => anticlockwise
# N - R => clockwise
# N - * => ?
# 
# S - L => clockwise
# S - R => anticlockwise
# S - * => ?
# 
# E - T => anticlockwise
# E - B => clockwise
# E - * => ?
# 
# W - T => clockwise
# W - B => anticlockwise
# W - * => ?
acceleration_vector_direction_and_position_mapping = {
    ('NE', 'LT'): -1,
    ('NE', 'RB'):  1,
    ('NE', 'L' ): -1,
    ('NE', 'B' ):  1,
    ('SE', 'LB'):  1,
    ('SE', 'RT'): -1,
    ('SE', 'L' ):  1,
    ('SE', 'T' ): -1,
    ('SW', 'LT'):  1,
    ('SW', 'RB'): -1,
    ('SW', 'R' ): -1,
    ('SW', 'T' ):  1,
    ('NW', 'RT'):  1,
    ('NW', 'LB'): -1,
    ('NW', 'R' ):  1,
    ('NW', 'B' ): -1,
    ('N' , 'L' ): -1,
    ('N' , 'R' ):  1,
    ('S' , 'L' ):  1,
    ('S' , 'R' ): -1,
    ('E' , 'T' ): -1,
    ('E' , 'B' ):  1,
    ('W' , 'T' ):  1,
    ('W' , 'B' ): -1
}

# Here is our assumptions:
# There are 4 quadrants to a circular motion
# The 4 quadrants can be grouped into 4 semicircles.
# the bottom semicircle
# the top semicircle
# the left semicircle
# the right semicircle
# projecting a circular motion onto the horizontal axis
# we see that the change between left to right semicircle 
# will register a change in acceleration direction on the horizontal axis
# projecting a circular motion onto the vertical axis
# we see that the change between bottom to top semicircle 
# will register a change in acceleration direction on the vertical axis
# for the horizontal axis:
# 
#              RtL
#              -|-  
#             / | \ 
#  ----->>   |  |  |   <<------
#             \ | / 
#              -|-  
#              LtR
#  
#  * ->
#    * --> 
#      * --->
#        * ---->
#          * --->
#            * -->
#              * ->
#             <- *
#          <-- *
#       <--- *
#    <---- *
#   <--- *
#  <-- *
# <- *
#  * ->
#    * --> 
#      * --->
#        * ---->
#          * --->
#            * -->
#              * ->
#              
# Where the arrows `->>` represent acceleration direction.
# And the `->` represents velocity direction, while arrow length represents magnitude.
# 
# on the vertical axis, a similar graph will appear
# 
# we will see that: 
# left semicircle = right acceleration, right semicircle = left acceleration
# top semicircle = bottom acceleration, bottom semicircle = top acceleration
# 
# the displacement, velocity and acceleration will all be a sine wave when graphed onto a time axis
# 
# so we can now know whether a motion is clockwise or anticlockwise
# but we still need 1 more piece of knowledge
# that is the change in acceleration vector
# 
# we can find the change acceleration vector for any given time interval
# by looking at the X & Z acceleration values for T1 and comparing with X & Z acceleration values at T2
# for now we do not care about Y acceleration values, because we only care about a 2D circular motion and not a 3D orbit
# also because a user can reverse their direction of rotation in between a data window
# we should be doing a majority vote between all time interval calculations in order to tell us
# what the majority rotation direction is for the given data window

def normalise_signals(data_window, signal_delta_time_s):

    # to np arrays
    for k, vs in data_window.items():
        if k.lower() == 'x' or k.lower() == 'y' or k.lower() == 'z':
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

# this returns a np.array
def sine (freq, time, amp, phase, vertical_disp):    
    return amp * np.sin(freq * 2 * np.pi * time + phase) + vertical_disp

def process_curve_fit(data_window):

    # ignore SIGINT in the child process to allow the parent process to cleanup
    unix_signals.signal(unix_signals.SIGINT, unix_signals.SIG_IGN)
    
    # this function is to be executed asynchronously
    print("Child Process #%d" % os.getpid())
    
    # normalise raw signals
    normalised_data_window = normalise_signals(data_window, delta_time_s)
    
    # inferred_freq is also the rotations per second
    inferred_freq_east = freq_from_autocorr(normalised_data_window['east'], sampling_rate)
    inferred_freq_up = freq_from_autocorr(normalised_data_window['up'], sampling_rate)

    # fix the sine function with the inferred frequency (scipy doesn't like partial functions)
    sine_with_freq_east = lambda t, a, b, c: sine(inferred_freq_east, t, a, b, c)
    sine_with_freq_up = lambda t, a, b, c: sine(inferred_freq_up, t, a, b, c)

    # fit the sine curve with a fixed frequency to the time values and the signal
    popt_east, pcov_east = curve_fit(sine_with_freq_east, normalised_data_window['time'], normalised_data_window['east'])
    popt_up, pcov_up = curve_fit(sine_with_freq_up, normalised_data_window['time'], normalised_data_window['up'])


    # to find the rotational direction: clockwise or anticlockwise
    # we need to use the fitted functions to get the approximated acceleration vector values
    fitted_east_sine = lambda ts: sine(inferred_freq_east, ts, popt_east[0], popt_east[1], popt_east[2])    
    fitted_north_sine = lambda ts: sine(inferred_freq_up, ts, popt_up[0], popt_up[1], popt_up[2])
    
    # zip up the east and up accelerations into vectors for every time instant from the fitted sine function
    # creates an array of [[East Accel, Up Accel], [East Accel, Up Accel], ...]
    acceleration_vectors = list(zip(fitted_east_sine(normalised_data_window['time']), fitted_north_sine(normalised_data_window['time'])))

    # acquire the change in acceleration vector for each time interval
    # relies on element-wise subtraction of left shifted and right shifted acceleration_vectors
    acceleration_vector_deltas = np.subtract(acceleration_vectors[1:], acceleration_vectors[:-1])

    # map the acceleration_vector_deltas to directions
    acceleration_vector_delta_directions = []
    for signs in np.sign(acceleration_vector_deltas):
        acceleration_vector_delta_directions.append(acceleration_vector_delta_direction_mapping[tuple(signs)])

    # map the acceleration_vectors to positions
    acceleration_vector_positions = []
    for signs in np.sign(acceleration_vectors):
        acceleration_vector_positions.append(acceleration_vector_position_mapping[tuple(signs)])

    # zip up the directions with the positions
    # for example: [ ['NE', 'LB'], [ 'SW', 'RT'], ... ]
    # then produce a list of inferred rotational directions
    # for example: [ 1, 1, 1, 0, -1, -1, 1] where 1: C, -1: AC and 0: ?
    rotational_directions = []
    for dir_and_pos in zip(acceleration_vector_delta_directions, acceleration_vector_positions):
        rotational_directions.append(acceleration_vector_direction_and_position_mapping.get(dir_and_pos, 0))

    # most common direction (vote on the majority inferred rotational direction)
    rotational_direction = mode(rotational_directions)[0][0]

    return (
        (popt_east, pcov_east), 
        (popt_up, pcov_up), 
        inferred_freq_east, 
        inferred_freq_up, 
        rotational_direction, 
        normalised_data_window
    )


plt.ion()
axes = plt.gca()
axes.set_xlabel('Time (s)')
axes.set_ylabel('Accleration (m/s^2)')
plt.ylim(-(ACCELERATION_MAX / 2), ACCELERATION_MAX / 2)
plot_zero_line, = plt.plot([], [], 'c-')
plot_east_data, = plt.plot([], [], 'r.')
plot_east_curve, = plt.plot([], [], 'r-')
# plot_north_data, = plt.plot([], [], 'g.')
# plot_north_curve, = plt.plot([], [], 'g-')
plot_up_data, = plt.plot([], [], 'b.')
plot_up_curve, = plt.plot([], [], 'b-')

def display(display_data):
    
    # potential race condition here.. we need to lock access to the GUI, so the display updates are queued up or dropped

    (
        (popt_east, pcov_east), 
        (popt_up, pcov_up), 
        inferred_freq_east, 
        inferred_freq_up, 
        rotational_direction, 
        normalised_data_window
    ) = display_data

    plt.xlim(normalised_data_window['time'][0], normalised_data_window['time'][-1])

    plot_zero_line.set_xdata(normalised_data_window['time'])
    plot_zero_line.set_ydata(normalised_data_window['time'] * 0)

    plot_east_data.set_xdata(normalised_data_window['time'])
    plot_east_data.set_ydata(normalised_data_window['east'])

    plot_up_data.set_xdata(normalised_data_window['time'])
    plot_up_data.set_ydata(normalised_data_window['up'])

    plot_east_curve.set_xdata(normalised_data_window['time'])
    plot_east_curve.set_ydata( 
        sine(
            inferred_freq_east, 
            normalised_data_window['time'], 
            popt_east[0], 
            popt_east[1], 
            popt_east[2]
        )
    )

    plot_up_curve.set_xdata(normalised_data_window['time'])
    plot_up_curve.set_ydata( 
        sine(
            inferred_freq_up, 
            normalised_data_window['time'], 
            popt_up[0], 
            popt_up[1], 
            popt_up[2]
        )
    )

    plt.draw()

    global output_direction
    global output_rps

    if rotational_direction == 1:
        print("Clockwise")
        output_direction = 1
    elif rotational_direction == -1:
        print("Anticlockwise")
        output_direction = -1
    else:
        print("Unknown Direction")
        output_direction = 0

    # output rps will be the average of the east frequency and up frequency
    output_rps = (inferred_freq_east + inferred_freq_up) / 2

    print("RPS East: " + str(inferred_freq_east) + "\n" + "RPS Up: " + str(inferred_freq_up))

def cleanup_and_exit(pool, sensor, server, code):
    
    print("Closing Orbit Detection Process Pool, Orbit Sensor and TCP Server!")
    pool.close()
    sensor.write_timeout = 0
    sensor.write(b'0')
    sensor.close()
    server.shutdown()
    server.server_close()
    sys.exit(code)

# TCP server will be in its own thread
class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

# TCP request handling will be in its own thread
class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        print("Responding to new client: {}".format(self.request.getpeername()))
        self.request.settimeout(5)
        try:
            while True:
                # wait on client to ask for data first (it can be anything)
                if not (self.request.recv(1024)): break
                # send `output_direction:output_rps`
                self.request.sendall(bytes("{0}:{1}\n".format(output_direction, output_rps), 'ascii'))
            print("Client: {} closed connection.".format(self.request.getpeername()))
        except:
            print("Timed out waiting for client, closing connection to client: {}".format(self.request.getpeername()))

# starting 1 child process
pool = Pool(processes=1)

# start the TCP server
server = ThreadedTCPServer((host, port), ThreadedTCPRequestHandler)
server_thread = threading.Thread(target=server.serve_forever)
server_thread.daemon = True
server_thread.start()
print("Starting server at {0}:{1}".format(host, port))

# start the sensor readings
sensor = serial.Serial(device_path, baud_rate)
sensor.reset_input_buffer()
sensor.reset_output_buffer()
print("Waiting for device to be ready...")
sensor.timeout = None    
if sensor.readline() != b"Ready!\n":
    print("Device was not ready! Exiting!")
    cleanup_and_exit(pool, sensor, server, 1)
sensor.timeout = 1
print("Device is ready!")

print("Starting Analysis!")
sensor.write(b'1')

data_window_start_ms = None
data_window = {
    't': [],
    'x': [],
    'y': [],
    'z': []
}

try:

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

except KeyboardInterrupt:

    cleanup_and_exit(pool, sensor, server, 0)
