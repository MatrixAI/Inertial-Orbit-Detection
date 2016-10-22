#define READY_DELAY 1000
#define MESSAGE_DELAY 30

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

    while (Serial.available()) Serial.read();

}

/**
 * The ready message is sent to the host every time the serial port is opened.
 */
void write_ready_message () {

    Serial.print("1");

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
        Serial.flush();

        last_ready_time = current_time;

    }

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
 * Write the accelerometer values.
 */
void write_accelerometer_values (unsigned long current_time) {

    Serial.print("Time=");
    Serial.print(current_time);
    Serial.print(",X=");
    Serial.print(analogRead(x_axis));
    Serial.print(",Y=");
    Serial.print(analogRead(y_axis));
    Serial.print(",Z=");
    Serial.print(analogRead(z_axis));
    
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
        Serial.flush();

        last_message_time = current_time;

    }

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
 * Then it writes the ready message.
 */
void running_setup () {

    // block until serial port is ready
    // Serial is actually always ready due to being a HardwareSerial
    while (!Serial);

    // let the host know the device is ready immediately 
    // without waiting on the delayed ready messages
    write_ready_message();

}

/**
 * Setup will set the baud rate and let the host know its ready
 */
void setup () {

    Serial.begin(9600);
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

    // allow running to be switched while running
    switch_running();
    current_time = millis();
    if (running) {
        write_periodic_message(current_time);
    } else {
        write_delayed_ready_message(current_time);
    }

}