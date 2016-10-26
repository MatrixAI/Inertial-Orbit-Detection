from copy import deepcopy
import serial
import window_processing
import time
import logging
import re

controller_message_regex = re.compile('^Time.(\d+).X.(\d+).Y.(\d+).Z.(\d+)', re.I)

def read_from_controller(controller, frame_start_byte, frame_end_byte):

    # block until we get a proper message from the controller
    while True:
        # discard bytes until we find the frame start byte
        starting_byte = sensor.read(1)
        if starting_byte != frame_start_byte:
            continue

        # read bytes until we get the frame end byte
        intermediate_byte = sensor.read(1)
        message_buffer = bytearray()
        while (intermediate_byte != frame_end_byte):
            message_buffer += intermediate_byte
            intermediate_byte = sensor.read(1)

        # decode bytes into a string
        message_buffer = message_buffer.decode("ascii")

        # match the sample
        sample = re.match(controller_message_regex, message_buffer)

        if sample is not None:
            break

    sample_time_ms = int(sample.group(1))
    sample_x_accel = int(sample.group(2)) 
    sample_y_accel = int(sample.group(3))
    sample_z_accel = int(sample.group(4))

    return (sample_time_ms, sample_x_accel, sample_y_accel, sample_z_accel)

def roll_the_window(rolling_window, rolling_window_interval, rolling_time, shift_or_increment=True):
    """Rolls the data window. Make sure the new window is the same type as the existing window.

    Because the our rolling increment is based on time, this means the resulting window 
    size can change. If the existing window is empty, then the new window becomes the existing 
    window.
    """

    # if the existing window is empty, then the new window becomes the existing window
    if rolling_window and rolling_window['t']:
        
        # rolling the window can involve a same-size shift (truncate and append), or just an increment
        # rolling windows generally need a same-size shift, however to reach the full size we need to 
        # first act like recursive windows!
        if shift_or_increment:

            starting_time = rolling_window['t'][0]
            cutoff_time = starting_time + rolling_time
            cutoff_index = None

            # find the first time sample that is greater to the cutoff time
            # the index of that becomes the length that we perform a cutoff
            for i,t in enumerate(rolling_window['t']):
                if t > cutoff_time:
                    cutoff_index = i
                    break

        else:

            cutoff_index = 0

        # for example, if the index is 7, it will remove sample 0 to sample 6
        for k in rolling_window:
            rolling_window[k] = rolling_window[k][cutoff_index:]
            rolling_window[k] = rolling_window[k] + rolling_window_interval[k]
            
    else:

        rolling_window = rolling_window_interval

    return rolling_window

def connect(device_path, baud_rate):
    """Connects to the game controller serial device with a given baud rate.

    This orbit server should be started after the game controller is already connected.
    It will block until for the controller device sends a `Ready!\n` message. If the 
    controller sends something other than message, it will raise an IOError exception.
    """

    controller = serial.Serial(device_path, baud_rate)

    # clear the buffers first
    controller.reset_input_buffer()
    controller.reset_output_buffer()

    logging.info("Waiting for device to be ready...")

    # having no time out means the main thread event loop will block on controller events
    # this does not affect the write timeout, only the read timeout
    controller.timeout = None

    # wait until the device is ready (equivalent to a peek function on the serial device)
    # having any data incoming from the controller signals readiness
    while (controller.in_waiting < 1):
        pass

    logging.info("Device is ready!")

    return controller

def run(
    controller, 
    time_window_ms, 
    time_interval_ms, 
    time_delta_ms, 
    sensor_type, 
    orientation, 
    process_pool, 
    channel, 
    graph 
):

    logging.info("Running Analysis Loop")

    # the time window size determines the number of values that will be inside a data window
    # however the actual size of a data window is not deterministic, as the real time delta between 
    # each acceleration sample may be slightly different because arduino is a soft realtime system
    
    rolling_window = {"t": [], "x": [], "y": [], "z": []}
    rolling_window_start = None
    rolling_window_end = None
    rolling_window_interval = deepcopy(rolling_window)
    rolling_window_interval_start = None
    rolling_window_interval_end = None
    filled_rolling_window = False

    # tell the controller to start sending data
    controller.write(b'1')

    # this is the initial loop setup
    # it will setup the first rolling interval
    (
        sample_time_ms, 
        sample_x_accel, 
        sample_y_accel, 
        sample_z_accel
    ) = read_from_controller(controller, b"S", b"E")

    rolling_window_interval_start = sample_time_ms
    rolling_window_interval['t'] = [sample_time_ms]
    rolling_window_interval['x'] = [sample_x_accel]
    rolling_window_interval['y'] = [sample_y_accel]
    rolling_window_interval['z'] = [sample_z_accel]

    # the analysis loop is the main thread event loop
    # it needs to accumulate samples into a rolling interval
    # then roll the rolling window data with the rolling interval
    # then execute the analysis on the data asynchronously
    while True:

        # block until we get proper cooordinates
        (
            sample_time_ms, 
            sample_x_accel, 
            sample_y_accel, 
            sample_z_accel
        ) = read_from_controller(controller, b"S", b"E")

        # if we are continuing the accumulation the rolling interval
        if (rolling_window_interval_start is not None and (rolling_window_interval_start + time_interval_ms >= sample_time_ms)):

            rolling_window_interval['t'].append(sample_time_ms)
            rolling_window_interval['x'].append(sample_x_accel)
            rolling_window_interval['y'].append(sample_y_accel)
            rolling_window_interval['z'].append(sample_z_accel)

        # else if we have finished accumulating a rolling interval
        elif(rolling_window_interval_start is not None):

            rolling_window_interval_end = rolling_window_interval["t"][-1]

            logging.info(
                "Rolling the Data Window with Interval at: {0} - {1}", 
                rolling_window_interval_start, 
                rolling_window_interval_end
            )

            # the `filled_rolling_window` starts out as False
            # only at the completion of the initial window do we change to True
            # once it is True, it stays True, for the rest of this event loop
            if (
                not filled_rolling_window 
                and rolling_window_start is not None 
                and (rolling_window_start + time_window_ms < sample_time_ms)
            ): 
                filled_rolling_window = True 

            # roll the window with the new interval
            # this will allow us to acquire the start and end of this window
            rolling_window = roll_the_window(
                rolling_window, 
                rolling_window_interval, 
                time_interval_ms, 
                filled_rolling_window
            )
            rolling_window_start = rolling_window["t"][0]
            rolling_window_end = rolling_window["t"][-1]

            # we only want to process filled rolling windows, not the initial partially filled window
            if filled_rolling_window:

                logging.info("Processing Data Window at: {0} - {1}", rolling_window_start, rolling_window_end)
                
                # the analysis will be executed in a child-process
                # the callback will be executed in another thread of this main-process
                # therefore, it won't be blocked this event loop
                process_pool.apply_async(
                    window_processing.create_analyse_rotation_process(time_delta_ms, orientation, sensor_type), 
                    args=(deepcopy(rolling_window),), 
                    callback=window_processing.create_analyse_rotation_process_callback(channel, graph)
                )

            # start a new rolling_window_interval
            rolling_window_interval_start = sample_time_ms
            rolling_window_interval['t'] = [sample_time_ms]
            rolling_window_interval['x'] = [sample_x_accel]
            rolling_window_interval['y'] = [sample_y_accel]
            rolling_window_interval['z'] = [sample_z_accel]

        # yield to other threads
        time.sleep(0)