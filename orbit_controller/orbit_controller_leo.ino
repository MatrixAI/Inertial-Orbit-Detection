#define READY_DELAY 1000
#define MESSAGE_DELAY 30

Stream * port;
boolean running = false;
int x_axis = A0;
int y_axis = A1;
int z_axis = A2;
unsigned long current_time;
unsigned long last_ready_time;
unsigned long last_message_time;

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

}

/**
 * Write periodic ready message if the serial port misses the first ready message.
 * Except in the case of the USB CDC serial port, there's no way to know if the 
 * receiver closed the serial port. So periodic ready messages should be sent.
 * This is only needed when `running` is false.
 * Note that we do not need to check last_ready_time == 0, because a readiness 
 * message will always be sent at startup by `running_setup`.
 */
void write_delayed_ready_message (unsigned long current_time) {

    if (current_time >= (last_ready_time + READY_DELAY)) {

        write_ready_message();
        port->flush();

        last_ready_time = current_time;

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
 * Write the message frame.
 * It will write when the last message time was 0, indicating this is the first time writing.
 * It will also write when the current time passes through the delay interval.
 */
void write_periodic_message (unsigned long current_time) {

    if ((last_message_time == 0) || (current_time >= (last_message_time + MESSAGE_DELAY))) {

        write_frame_start();
        write_accelerometer_values(current_time);
        write_frame_end();
        port->flush();

        last_message_time = current_time;

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
 * This is the real setup.
 * First it blocks until the serial is ready.
 * Then it writes the ready message.
 */
void running_setup () {

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

    // let the host know the device is ready immediately 
    // without waiting on the delayed ready messages
    write_ready_message();

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
    running_setup();
    last_ready_time = 0;
    last_message_time = 0;

}

/**
 * This is an event loop.
 * The event loop pattern needs to call all designated event handlers.
 * The serial port is where all events are emitted.
 * The event loop must not be blocked.
 * Loop will write the message frames.
 */
void loop () {

    // switch to Serial if becomes open and we're not already using Serial
    // switch to Serial1 if Serial closes and we're currently using Serial
    // because we can detect when Serial is closed, we can stop data emission
    if (Serial && port != &Serial) {
        running = false;
        running_setup();
    } else if (!Serial && port == &Serial) {
        running = false;
        running_setup();
    }

    // allow running to be switched while running
    switch_running();
    if (running) {
        current_time = millis();
        write_periodic_message(current_time);
    } else {
        current_time = millis();
        write_delayed_ready_message(current_time);
    }

}