# import os
# import re
# import csv 
# import sys
# import serial
# import threading
# import socketserver
# import signal as unix_signals
# import numpy as np
# import matplotlib.pyplot as plt 
# from copy import deepcopy
# from matplotlib.mlab import find as find_index_by_true
# from scipy.optimize import curve_fit
# from scipy.signal import fftconvolve
# from scipy.stats import mode
# from multiprocessing import Pool 


# to get accelerometer information

import argparse
import re
import accelerometers
import analysis_loop
import signal as unix_signals
from multiprocessing import Pool

axis_regex = re.compile('([+-])([xyz])', re.I)

def cleanup_and_exit(pool, device, server, code):
    print("Closing Orbit Detection Process Pool and TCP Server!")
    if pool:
        pool.close()
    if device:
        device.write_timeout = 0
        device.write(b"0")
        device.close()
    if server:
        server.shutdown()
        server.server_close()
    sys.exit(code)

if __name__ == "__main__": 

    command_line_parser = argparse.ArgumentParser()
    command_line_parser.add_argument("device", type=str, help="Path to Orbit Controller Serial Device")
    command_line_parser.add_argument("baud", type=int, help="Baud Rate")
    command_line_parser.add_argument("host", type=str, help="IP Address for the Orbit Detection Server")
    command_line_parser.add_argument("port", type=int, help="Port for the Orbit Detection Server")
    command_line_parser.add_argument(
        "-s", 
        "--sensor-type",
        type=str,
        choices=[k for k in accelerometers.accel_sensors]
        help="Accelerometer Sensor Type",
        default="am3x-1g"
    )
    command_line_parser.add_argument(
        "-ea", 
        "--east-axis", 
        type=str, 
        choices=["+x", "+y", "+z", "-x", "-y", "-z"], 
        help="East Axis and Sign from Orbit Controller",
        default="+x"
    )
    command_line_parser.add_argument(
        "-na", 
        "--north-axis", 
        type=str, 
        choices=["+x", "+y", "+z", "-x", "-y", "-z"], 
        help="North Axis and Sign from Orbit Controller",
        default="+y"
    )
    command_line_parser.add_argument(
        "-ua", 
        "--up-axis", 
        type=str, 
        choices=["+x", "+y", "+z", "-x", "-y", "-z"], 
        help="Up Axis and Sign from Orbit Controller",
        default="+z"
    )
    command_line_parser.add_argument(
        "-tw", 
        "--time-window", 
        type=int, 
        help="Rolling Time Window Size in Milliseconds",
        default=3000
    )
    command_line_parser.add_argument(
        "-tr", 
        "--time-rolling", 
        type=int, 
        help="Rolling Time Window Increment in Milliseconds",
        default=150
    )
    command_line_parser.add_argument(
        "-td", 
        "--time-delta", 
        type=int, 
        help="Sampling Period in Milliseconds",
        default=30
    )
    command_line_args = command_line_parser.parse_args()

    # process the command line parameters

    # acquire the acceleration parameters for the controller acceleration sensor
    accel_params = accelerometers.accel_sensors[command_line_args.sensor_type]

    # acquire the axes that will be used for ENU orientation
    east_axis_match = re.match(axis_regex, command_line_args.east_axis)
    north_axis_match = re.match(axis_regex, command_line_args.north_axis)
    up_axis_match = re.match(axis_regex, command_line_args.up_axis)
    east_sign = east_axis_match.group(1)
    east_axis = east_axis_match.group(2)
    north_sign = north_axis_match.group(1)
    north_axis = north_axis_match.group(2)
    up_sign = up_axis_match.group(1)
    up_axis = up_axis_match.group(2)

    # these will be used for sampling interpolation, frequency estimation, and sine wave regression
    delta_time_s = command_line_args.time_delta / 1000
    sampling_rate = 1000 / command_line_args.time_delta

    # initialise the external resources for this server
    process_pool = None
    controller = None
    server = None

    # prevent the process_window child-process from inheriting the exit handler
    exit_handler = lambda signum, frame: cleanup_and_exit(process_pool, controller, server, 0)
    unix_signal.signal(unix_signal.SIGINT, unix_signal.SIG_IGN)
    unix_signal.signal(unix_signal.SIGTERM, unix_signal.SIG_IGN)
    unix_signal.signal(unix_signal.SIGQUIT, unix_signal.SIG_IGN)
    unix_signal.signal(unix_signal.SIGHUP, unix_signal.SIG_IGN)
    process_pool = Pool(processes=1)
    unix_signal.signal(unix_signal.SIGINT, exit_handler)
    unix_signal.signal(unix_signal.SIGTERM, exit_handler)
    unix_signal.signal(unix_signal.SIGQUIT, exit_handler)
    unix_signal.signal(unix_signal.SIGHUP, exit_handler)

    # start the TCP server
    server = ThreadedTCPServer((command_line_args.host, command_line_args.port), ThreadedTCPRequestHandler)
    
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














