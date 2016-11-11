import processing.net.Client;

String serverAddress;
int    serverPort;

Client client;

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

    this.serverAddress = this.defaultServerAddress;
    this.serverPort = this.defaultServerPort;
    this.gameWidth = this.defaultGameWidth;
    this.gameHeight = this.defaultGameHeight;
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

    this.game = new FSM(this.gameStart);

}

/**
 * Event loop
 */
void draw() {
    
    // we need to try restarting the connection once if the connection drops for some reason
    if (this.client == null || !this.client.active()) {
        println("Game Client Lost Connection, Attempting to Restablish Connection");
        this.client = this.clientEstablish(this.serverAddress, this.serverPort);
        if (this.client == null) {
            println("Game Client Couldn't Reconnect");
            exit();
            return;
        }
    }

    ClientData clientData = this.clientRead(this.client, this.messageProtocol, this.rpsAndDirTokenRegex);

    if (clientData != null) {
        this.rotationRps         = clientData.rps;
        this.rotationDirection   = clientData.direction;
    }

    this.game.update();

    this.rotationRps = 0.0;
    this.rotationDirection = 0;

}