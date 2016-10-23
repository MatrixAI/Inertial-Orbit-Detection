#define MESSAGE_DELAY 30
#define READY_DELAY 1000

Stream * port;
bool running;
int x_axis = A0;
int y_axis = A1;
int z_axis = A2;

/**
 * Flush the serial input buffer.
 */
void flush_input () {

    while (port->available()) port->read();

}

/**
 * The ready message is sent to the host every time the serial port is opened.
 */
void write_ready_message () {

    port->print("1");
    port->flush();

}

/**
 * Write periodic ready message if the serial port misses the first ready message.
 * Except in the case of the USB CDC serial port, there's no way to know if the 
 * receiver closed the serial port. So periodic ready messages should be sent.
 * This is only needed when `running` is false.
 */
void write_ready_message_periodic (unsigned long delay, unsigned long current_time, bool initial_action) {

    static unsigned long last_time;
    if ((initial_action && last_time == 0) || ((current_time - last_time) >= delay)) {
        write_ready_message();
        last_time = current_time;
    }

}

/**
 * Begin a new message frame.
 */
void write_frame_start () {

    port->print("S");

}

/**
 * End the message frame.
 */
void write_frame_end () {

    port->print("E");

}

/**
 * Write the accelerometer values.
 */
void write_accelerometer_values (unsigned long current_time) {

    port->print("Time=");
    port->print(current_time);
    port->print(",X=");
    port->print(analogRead(x_axis));
    port->print(",Y=");
    port->print(analogRead(y_axis));
    port->print(",Z=");
    port->print(analogRead(z_axis));
    
}

/**
 * Write the message frame and flush.
 */
void write_message (unsigned long current_time) {

    write_frame_start();
    write_accelerometer_values(current_time);
    write_frame_end();
    port->flush();

}

/**
 * Write the message frame periodically.
 * This is designed to be executed inside an event loop.
 */
void write_message_periodic (unsigned long delay, unsigned long current_time, bool initial_action) {

    static unsigned long last_time;
    if ((initial_action && last_time == 0) || ((current_time - last_time) >= delay)) {
        write_message(current_time);
        last_time = current_time;
    }

}

/**
 * Switches the running flag.
 * The input control signal is just an ascii 1 or 0.
 */
void switch_running () {

    while (port->available() > 0) {
        int control = port->parseInt();
        if (control == 0) {
            running = false;
        } else if (control == 1) {
            running = true;
        }
    }

}

/**
 * Check which port to use, and prefer Serial over Serial1.
 */
void switch_ports () {

    // Serial1 as HardwareSerial will always report true
    // as there is no way to know if there is a listener 
    // without a keepalive or ping-pong protocol. So 
    // there's no poing checking it.
    // So we first just check for opened Serial in order 
    // to prefer Serial over Serial1.
    if (Serial) {
        port = &Serial;
    } else {
        port = &Serial1;
    }

}

/**
 * Setup will set the baud rate and let the host know its ready
 */
void setup () {

    // Serial is the USB CDC, the type is `Serial_ : public Stream`.
    // Serial1 is the RX and TX pins, the type is `HardwareSerial : public Stream`.
    // Both inherit from the Stream type.
    // The Serial1 is usually connected to a Bluetooth module.
    // We are going to open both serial ports. 
    // If Serial ever becomes available, switch from Serial 1 to Serial for emitting data.
    // As long as Serial is not opened, then we will just emit data over Serial1.
    Serial.begin(9600);
    Serial1.begin(9600);
    running = false;
    switch_ports();

}

/**
 * This is an event loop.
 * The event loop pattern needs to call all designated event handlers.
 * The serial port is where all events are emitted.
 * The event loop must not be blocked.
 * Loop will write the message frames.
 */
void loop () {

    // this is the system clock milliseconds from when controller is started
    // and resets every 50 days
    unsigned long current_time = millis();

    // switch to Serial if becomes open and we're not already using Serial
    // switch to Serial1 if Serial closes and we're currently using Serial
    // because we can detect when Serial is closed, we can stop data emission
    if (Serial && port != &Serial) {
        running = false;
        switch_ports();
    } else if (!Serial && port == &Serial) {
        running = false;
        switch_ports();
    }

    // allow running to be switched while running
    switch_running();
    if (running) {
        write_message_periodic(MESSAGE_DELAY, current_time, true);
    } else {
        write_ready_message_periodic(READY_DELAY, current_time, true);
    }

}