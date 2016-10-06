// this was produced with the help of: http://eli.thegreenplace.net/2009/08/12/framing-in-serial-communications
// in the future, just use: https://github.com/firmata/protocol

int x_axis = A0;
int y_axis = A1;
int z_axis = A2;
int axis_value = 0;
boolean running = false;

/**
 * Flush the serial input buffer.
 */
void flush_input () {

    while (Serial.available() ) Serial.read();

}

/**
 * Switches the running flag.
 * The input control signal is just an ascii 1 or 0.
 */
void switch_running () {

    while (Serial.available() > 0) {
        int control = Serial.parseInt();
        if (control == 0) {
            running = false;
        } else if (control == 1) {
            running = true;
        }
    }

}

/**
 * This is the real setup.
 * First it blocks until the serial is ready.
 * Then it writes the ready message.
 */
void running_setup () {

    // block until serial port is ready
    while (!Serial);

    // let the host know the device is ready
    write_ready_message();

    // the only thing we can block on is the serial port readiness
    // we cannot block on receiving a running control signal
    // that can lead to the race condition of where the device doesn't reset 
    // the communication protocol if the host terminates the port

}

/**
 * The ready message is sent to the host every time the serial port is opened.
 */
void write_ready_message () {

    Serial.print("Ready!\n");

}

/**
 * Begin a new message frame.
 */
void write_frame_start () {

    Serial.print("S");

}

/**
 * End the message frame.
 */
void write_frame_end () {

    Serial.print("E");

}

/**
 * Write the message frame.
 */
void write_accelerometer_values () {

    Serial.print("Time=");
    Serial.print(millis());
    Serial.print(",X=");
    axis_value = analogRead(x_axis);
    Serial.print(axis_value);
    Serial.print(",Y=");
    axis_value = analogRead(y_axis);
    Serial.print(axis_value);
    Serial.print(",Z=");
    axis_value = analogRead(z_axis);
    Serial.print(axis_value);
    
}

/**
 * Setup will set the baud rate and let the host know its ready
 */
void setup () {

    Serial.begin(9600);
    running_setup();

}

/**
 * This is an event loop.
 * The event loop pattern needs to call all designated event handlers.
 * The serial port is where all events are emitted.
 * The event loop must not be blocked. Or else there can be a race condition between the host and device.
 * Loop will write the message frames, while delaying by 30ms.
 */
void loop () {

    // if serial port gets closed, this device must be reset
    // so that way the communication protocol starts from the beginning
    if (!Serial) {
        running = false;
        running_setup();
    }

    // allow running to be switched while running
    switch_running();
    if (running) {
        write_frame_start();
        write_accelerometer_values();
        write_frame_end();
        delay(30);
        Serial.flush();
    }
    // if not running, the loop is a no-op

}
