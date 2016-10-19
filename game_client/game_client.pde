import processing.net.*;

String serverAddress;
int serverPort;
int gameWidth;
int gameHeight;

Client client;

FSM game;
State gameStart = new State(this, "enterStart", "runStart", "exitStart");
State gamePlaying = new State(this, "enterPlaying", "runPlaying", "exitPlaying");
State gameOver = new State(this, "enterOver", "runOver", "exitOver");

int score;
int balloonX, balloonY;
RPSAndDir rpsAndDir;
ArrayList<int[]> walls = new ArrayList<int[]>(); 
ArrayList<int[]> clouds = new ArrayList<int[]>(); 

long pingPongTime;


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

    gameWidth = 500;
    gameHeight = 500;
    boolean displayFullScreen = false;

    // args may be null
    // the first parameter other than the program name is placed at 0 index
    if (args != null) {

        if (args.length >= 1) {
            serverAddress = args[0];
        }

        if (args.length >= 2) {
            serverPort = int(args[1]);
        }

        if (args.length >= 3) {
            gameWidth = int(args[2]);
        }

        if (args.length >= 4) {
            gameHeight = int(args[3]);
        }

        if (
            args[args.length - 1] == "-f"
            || args[args.length - 1] == "--fullscreen"
        ) {
            gameWidth = displayWidth;
            gameHeight = displayHeight;
            displayFullScreen = true;
        }

    }

    if (!displayFullScreen) {
        size(gameWidth, gameHeight);
    } else {
        fullScreen();
    }

}

/**
 * Sets up the game.
 */
void setup() { 

    // ints cannot be null, so 0 is the sentinel value of serverPort
    if (
        serverAddress == null 
        || serverPort == 0 
    ) {
        // overrided exit is only available at setup and beyond
        println("Server Address and Server Port is Needed");
        exit();
    }

    // Client does not throw exceptions
    client = new Client(this, serverAddress, serverPort); 
    if (!client.active()) {
        println("Game Client Couldn't Connect to Server");
        exit();
    }
    client.clear();
    pingPongTime = System.currentTimeMillis() / 1000L;

    // transition to the initial game state
    game = new FSM(gameStart);

}

/**
 * Override the exit handler, so we close the client connection if its available.
 */
void exit() {

    if (client != null) {
        client.clear();
        client.stop();
    }
    super.exit();

}

/**
 * Event loop
 */
void draw() {

    game.update();
    clientPingPongCheck();

}

/**
 * Client Event Handler
 */
void clientEvent() {

    // only update the current rps and dir, if its a new frame from the orbit server
    RPSAndDir newRpsAndDir = clientReadOrbitServer(client, pingPongTime);
    if (newRpsAndDir != null) {
        rpsAndDir = newRpsAndDir;
    }

}

/**
 * Key Event Handler
 */
void keyPressed() { 

    switch (game.getCurrentState()) {
        case gameStart:
            game.transitionTo(gamePlaying);
        break;
        case gameOver:
            game.transitionTo(gameStart);
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

    balloonX = displayWidth / 2;
    balloonY = displayHeight / 2;

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
    text("Your Score", gameWidth / 2, gameHeight / 2 - 120);
    
    textSize(130);
    text(score, gameWidth / 2, gameHeight / 2);
    
    textSize(15);
    text("Press any key to restart", gameWidth / 2, gameHeight-30);

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

