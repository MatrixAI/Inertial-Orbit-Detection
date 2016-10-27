import processing.net.Client;

String serverAddress;
int    serverPort;

Client client;
int    pingPongReceiveTime;
int    pingPongSendTime;

int gameWidth;
int gameHeight;
int gameCenterX;
int gameCenterY;

FSM   game;
State gameStart   = new State(this, "enterStart",   "runStart",   "exitStart");
State gamePlaying = new State(this, "enterPlaying", "runPlaying", "exitPlaying");
State gameOver    = new State(this, "enterOver",    "runOver",    "exitOver");

float rotationRps;
int   rotationDirection;

/**
 * Settings is the hook designed for setting the window size based on variables.
 * Here we interrogate the command line parameters, and set the server address, 
 * server port, game width and game height. There's also a `-f` flag representing 
 * full screen. While the server address and port are required parameters, the 
 * game width and game height are not.
 *
 * Note that at settings time, very little of Processing functionality is 
 * available.
 */
void settings() {

    this.gameWidth = defaultGameWidth;
    this.gameHeight = defaultGameHeight;
    boolean displayFullScreen = false;

    // args may be null
    if (this.args != null) {

        if (this.args.length >= 1) {
            this.serverAddress = this.args[0];
        }

        if (this.args.length >= 2) {
            this.serverPort = int(this.args[1]);
        }

        if (this.args.length >= 3) {
            this.gameWidth = int(this.args[2]);
        }

        if (args.length >= 4) {
            this.gameHeight = int(this.args[3]);
        }

        if (
            this.args[this.args.length - 1] == "-f"
            || this.args[this.args.length - 1] == "--fullscreen"
        ) {
            this.gameWidth = this.displayWidth;
            this.gameHeight = this.displayHeight;
            displayFullScreen = true;
        }

    }

    if (!displayFullScreen) {
        size(this.gameWidth, this.gameHeight);
    } else {
        fullScreen();
    }

    this.gameCenterX = this.gameWidth / 2;
    this.gameCenterY = this.gameHeight / 2;

}

/**
 * Override the exit handler, so we close the client connection if its available.
 */
void exit() {

    this.clientShutdown(this.client);
    super.exit();

}

/**
 * Sets up the game.
 */
void setup() { 

    // ints cannot be null, so 0 is the sentinel value of serverPort
    if (
        this.serverAddress == null 
        || this.serverPort == 0 
    ) {
        // overrided exit is only available at setup and beyond
        println("Server Address and Server Port is Needed");
        exit();
        // exit doesn't return immediately, but by returning here, it will return immediately
        return;
    }

    this.client = this.clientEstablish(this.serverAddress, this.serverPort);
    if (this.client == null) {
        println("Game Client Couldn't Connect");
        exit();
        return;
    }

    // initialise both ping pong send and receive time to the current time
    int currentTime = this.getCurrentTime();
    this.pingPongSendTime = currentTime;
    this.pingPongReceiveTime = currentTime;

    this.game = new FSM(this.gameStart);

}

/**
 * Event loop
 */
void draw() {

    int currentTime = this.getCurrentTime();

    boolean pongStatus = this.clientPongCheck(
        this.client, 
        this.pingPongTimeout, 
        this.pingPongReceiveTime, 
        currentTime
    );

    if (!pongStatus) {
        println("Game Client Lost Connection, Restarting Connection");
        this.clientShutdown(client);
        this.client = this.clientEstablish(this.serverAddress, this.serverPort);
        if (this.client == null) {
            println("Game Client Couldn't Reconnect");
            exit();
        }
    }

    boolean pingStatus = this.clientPingCheck(
        this.client, 
        this.pingPongInterval,
        this.pingPongSendTime,
        currentTime
    );

    if (pingStatus) {
        this.pingPongSendTime = currentTime;
    }

    ClientData clientData = this.clientRead(this.client, this.messageProtocol, this.rpsAndDirTokenRegex);

    if (clientData != null) {
        if (clientData.rps != null && clientData.direction != null) {
            this.rotationRps         = clientData.rps;
            this.rotationDirection   = clientData.direction; 
        }
        this.pingPongReceiveTime = currentTime;
    }

    this.game.update();

}

/**
 * Get the current time since this program started in seconds.
 */
int getCurrentTime() {

    return millis() / 1000;

}