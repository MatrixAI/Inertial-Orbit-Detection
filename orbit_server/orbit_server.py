import re
import sys
import argparse
import accelerometers
import signal as unix_signal
import server_loop
import analysis_loop
import multiprocessing
import collections
import graphing
import logging

axis_regex = re.compile('([+-])([xyz])', re.I)

def cleanup_and_exit(pool, device, server, code):
    print("Closing Orbit Detection Process Pool and TCP Server!")
    if pool:
        pool.close()
    if device and device.is_open:
        device.write_timeout = 0
        device.write(b"0")
        device.close()
    if server:
        server.shutdown()
        server.server_close()
    sys.exit(code)

def main():

    command_line_parser = argparse.ArgumentParser()
    command_line_parser.add_argument("device", type=str, help="Path to Orbit Controller Serial Device")
    command_line_parser.add_argument("baud", type=int, help="Baud Rate")
    command_line_parser.add_argument("host", type=str, help="IP Address for the Orbit Detection Server")
    command_line_parser.add_argument("port", type=int, help="Port for the Orbit Detection Server")
    command_line_parser.add_argument(
        "-s", 
        "--sensor-type",
        type=str,
        choices=[k for k in accelerometers.accel_sensors],
        help="Accelerometer Sensor Type",
        default="am3x-1.5g"
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
        help="Rolling Time Window Size in Milliseconds (default is 3000ms)",
        default=4000
    )
    command_line_parser.add_argument(
        "-ti", 
        "--time-interval", 
        type=int, 
        help="Rolling Time Window Interval in Milliseconds (default is 150ms)",
        default=150
    )
    command_line_parser.add_argument(
        "-td", 
        "--time-delta", 
        type=int, 
        help="Sampling Period in Milliseconds (default is 30ms)",
        default=40
    )
    command_line_parser.add_argument(
        "-g",
        "--graph",
        help="Plot Acceleration Graph",
        action="store_true"
    )
    command_line_parser.add_argument(
        "-v",
        "--verbose",
        help="Log Verbose Messages",
        action="store_const",
        dest="loglevel",
        const=logging.INFO
    )
    command_line_parser.add_argument(
        "-d",
        "--debug",
        help="Log Debug Messages",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG
    )
    command_line_args = command_line_parser.parse_args()

    # process the command line parameters

    # set the log level
    logging.basicConfig(level=command_line_args.loglevel)

    # acquire the axes that will be used for ENU orientation
    east_axis_match = re.match(axis_regex, command_line_args.east_axis)
    north_axis_match = re.match(axis_regex, command_line_args.north_axis)
    up_axis_match = re.match(axis_regex, command_line_args.up_axis)
    orientation = {
        "east": {
            "sign": east_axis_match.group(1),
            "axis": east_axis_match.group(2).lower()
        },
        "north": {
            "sign": north_axis_match.group(1), 
            "axis": north_axis_match.group(2).lower()
        },
        "up": {
            "sign": up_axis_match.group(1), 
            "axis": up_axis_match.group(2).lower()
        }
    }

    # initialise the external resources for this server
    process_pool = None
    controller = None
    server = None
    # queue size of 1
    analysis_server_chan = collections.deque(maxlen=1)

    # if we need to graph, we'll setup the graph
    if command_line_args.graph:
        graph = graphing.setup(
            -(accelerometers.accel_sensors[command_line_args.sensor_type]["accel_max"] / 2),
            accelerometers.accel_sensors[command_line_args.sensor_type]["accel_max"] / 2
        )
    else:
        graph = None

    # prevent the process_window child-process from inheriting the common exit signals
    exit_handler = lambda signum, frame: cleanup_and_exit(process_pool, controller, server, 0)
    unix_signal.signal(unix_signal.SIGINT, unix_signal.SIG_IGN)
    unix_signal.signal(unix_signal.SIGTERM, unix_signal.SIG_IGN)
    unix_signal.signal(unix_signal.SIGQUIT, unix_signal.SIG_IGN)
    unix_signal.signal(unix_signal.SIGHUP, unix_signal.SIG_IGN)
    process_pool = multiprocessing.Pool(processes=1)
    unix_signal.signal(unix_signal.SIGINT, exit_handler)
    unix_signal.signal(unix_signal.SIGTERM, exit_handler)
    unix_signal.signal(unix_signal.SIGQUIT, exit_handler)
    unix_signal.signal(unix_signal.SIGHUP, exit_handler)

    try: 

        logging.info("Establishing TCP server at %s:%d", command_line_args.host, command_line_args.port)
        server = server_loop.start(command_line_args.host, command_line_args.port, analysis_server_chan)

        logging.info("Establishing connection to controller: %s", command_line_args.device)
        controller = analysis_loop.connect(command_line_args.device, command_line_args.baud)

        # starts the main loop (pass in the process_pool)
        analysis_loop.run(
            controller=controller, 
            time_window_ms=command_line_args.time_window, 
            time_interval_ms=command_line_args.time_interval, 
            time_delta_ms=command_line_args.time_delta, 
            sensor_type=command_line_args.sensor_type, 
            orientation=orientation, 
            process_pool=process_pool, 
            channel=analysis_server_chan, 
            graph=graph
        )

    finally: 

        cleanup_and_exit(process_pool, controller, server, 0)

if __name__ == "__main__": 

    main()
