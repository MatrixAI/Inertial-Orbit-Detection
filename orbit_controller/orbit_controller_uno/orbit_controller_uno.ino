#define MESSAGE_DELAY 30
#define READY_DELAY 1000

bool running;
int x_axis = A0;
int y_axis = A1;
int z_axis = A2;

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
    Serial.flush();

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
 * Write the message frame and flush.
 */
void write_message (unsigned long current_time) {

    write_frame_start();
    write_accelerometer_values(current_time);
    write_frame_end();
    Serial.flush();

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
 * Setup will set the baud rate and let the host know its ready
 */
void setup () {

    Serial.begin(9600);
    running = false;

}

/**
 * This is an event loop.
 * The event loop pattern needs to call all designated event handlers.
 * The serial port is where all events are emitted.
 * The event loop must not be blocked.
 * Loop will write the message frames.
 */
void loop () {

    unsigned long current_time = millis();

    // allow running to be switched while running
    switch_running();
    if (running) {
        write_message_periodic(MESSAGE_DELAY, current_time, true);
    } else {
        write_ready_message_periodic(READY_DELAY, current_time, true);
    }

}