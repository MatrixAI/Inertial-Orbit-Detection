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
 * Then it blocks until we get a true running.
 * If we don't get a true running, then block until there's available input.
 * Then parse the available input for a running control signal.
 */
void running_setup () {

    // block until serial port is ready
    while (!Serial);

    // let the server know the device is ready
    write_ready_message();

    // block until running is true
    while (!running) {
        // block until we get some input
        while (!Serial.available());
        switch_running();
    }

}

/**
 * The ready message is sent to the server every time the serial port is opened.
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
 * Setup will let the server know its ready, and it will block until running is true.
 */
void setup () {

    Serial.begin(9600);
    running_setup();

}

/**
 * Loop will write the message frames, while delaying by 30ms.
 * On each iteration, it will check if the server is telling the device to stop running.
 */
void loop () {

    // if serial port gets closed, this device may not be reset, 
    // if so, we perform the setup again
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
