import processing.net.*;

String serverAddress;
int    serverPort;

int gameWidth;
int gameHeight;
int gameCenterX;
int gameCenterY;

Client client;
int    pingPongTime;

FSM   game;
State gameStart   = new State(this, "enterStart",   "runStart",   "exitStart");
State gamePlaying = new State(this, "enterPlaying", "runPlaying", "exitPlaying");
State gameOver    = new State(this, "enterOver",    "runOver",    "exitOver");

float rotationRps;
int   rotationDirection;
int   score;
int   balloonX, balloonY;

ArrayList<int[]> walls = new ArrayList<int[]>(); 


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

    this.gameWidth = 500;
    this.gameHeight = 500;
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
    }

    this.client = this.clientEstablish(this.serverAddress, this.serverPort);
    if (this.client == null) {
        println("Game Client Couldn't Connect");
        exit();
    }
    
    this.pingPongTime = millis() / 1000;

    this.game = new FSM(this.gameStart);

}

/**
 * Override the exit handler, so we close the client connection if its available.
 */
void exit() {

    this.clientShutdown(client);
    super.exit();

}

/**
 * Event loop
 */
void draw() {

    boolean clientStatus = this.clientLiveCheck(
        this.client, 
        this.pingPongTimeout, 
        this.pingPongTime
    );

    if (!clientStatus) {

        println("Game Client Lost Connection, Restarting Connection");
        this.clientShutdown(client);
        this.client = this.clientEstablish(this.serverAddress, this.serverPort);
        if (this.client == null) {
            println("Game Client Couldn't Reconnect");
            exit();
        }

    }

    // put this on a delay (in the setup, rather than in the event loop)
    this.clientPing(client);

    game.update();

}

/**
 * Client Event Handler
 */
void clientEvent() {

    ClientUpdate clientUpdate = this.clientRead(this.client, this.pingPongTime);
    if (clientUpdate != null) {
        this.rotationRps = clientUpdate.rps;
        this.rotationDirection = clientUpdate.direction; 
        this.pingPongTime = clientUpdate.pingPongTime;
    }

}

/**
 * Key Event Handler
 */
void keyPressed() { 

    switch (this.game.getCurrentState()) {
        case this.gameStart:
            this.game.transitionTo(this.gamePlaying);
        break;
        case this.gameOver:
            this.game.transitionTo(this.gameStart);
        break; 
    }

}

void enterStart() {
    
    background(251, 185, 1);
    textAlign(CENTER);
    text("Press any key to start", height/2, width/2);

}

void runStart() {
    // nothing to do here
}

void exitStart() {
    // nothing to do here
}

void enterPlaying() {

    this.balloonX = this.gameCenterX;
    this.balloonY = this.gameCenterY;

}

void runPlaying() {

}

void exitPlaying() {

}

void enterOver() {

    background(251, 185, 1);
    textAlign(CENTER);
    fill(255);
    
    textSize(12);
    text("Your Score", this.gameCenterX, this.gameCenterY - 120);
    
    textSize(130);
    text(score, this.gameCenterX, this.gameCenterY);
    
    textSize(15);
    text("Press any key to restart", this.gameCenterX, this.gameHeight-30);

}

void runOver() {

}

void exitOver() {

    score = 0;
    lastAddTime = 0;
    walls.clear();
    balloonVertVelocity = 0;
    balloonHoriVelocity = 0;

}

