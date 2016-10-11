import serial
import rotation_mapping
import logging
import timer
import process_window
from copy import deepcopy

message_regex = re.compile('^Time.(\d+).X.(\d+).Y.(\d+).Z.(\d+)', re.I)

def connect(device_path, baud_rate):

    controller = serial.Serial(device_path, baud_rate)

    # clear the buffers first
    controller.reset_input_buffer()
    controller.reset_output_buffer()

    logging.info("Waiting for device to be ready...")
    controller.timeout = None
    if controller.readline() != b"Ready!\n":
        logging.info("Device was not ready! Exiting!")
        raise IOError("Orbit Controller did not send `Ready!\\n`")
    controller.timeout = 1

    logging.info("Device is ready!")

    return controller

def run(controller, channel):

    logging.info("Running Analysis Loop")

    # tell the controller to start sending data
    controller.write(b'1')

    data_window_start_ms = None
    data_window = {
        't': [],
        'x': [],
        'y': [],
        'z': []
    }

    while True:

        # ok here we need to implement the double input buffer method
        # we read with no timeout
        # that means its a polling asynchronous IO style
        # when we read nothing, we just continue on
        # if we do read something
        # on the other hand, would it be good idea
        # actually it would be better to use something like select/poll
        # for proper sleeping in case there's no events
        # rather than continuously busy looping
        # how can we do that with pyserial?
        # serial.in_waiting (returns numbers of bytes that is waiting, non-blocking)
        # 
        # also another event could be closing, that is checking is_open?
        # wait timeout=0 means read will always block
        # that could mean block until the necessary number of bytes is read
        # this can just block and do nothing until those bytes are ready
        # when its blocked, the thread will context switch, and the other thread will run
        # there's no other events for this to process!
        # also the analysis loop needs to orchestrate the queue from process_window to 
        # server_loop
        # so ultimately we need a queue passed in that can communicate between analysis loop to server loop

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

        # yield to other threads
        timer.sleep(0)
