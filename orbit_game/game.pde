float hotBalloonVertVelocity;
int hotBalloonX, hotBalloonY;
int score;

PGraphics startScreen;
PGraphics playBackground;
PGraphics hotBalloon;

ArrayList<int[]> walls = new ArrayList<int[]>(); 

/**
 * Key Event Handler.
 * This is only applied at the start and over states.
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

////////////////////////////////
// Game Start State Functions //
////////////////////////////////

void enterStart() {

    background(0);
    if (this.startScreen == null) {
        this.startScreen = this.createStartScreen(this.gameWidth, this.gameHeight);
    }
    imageMode(CORNER);
    image(this.startScreen, 0, 0);

}

void runStart() {
    // nothing to do here
}

void exitStart() {
    // nothing to do here
}

//////////////////////////////////
// Game Playing State Functions //
//////////////////////////////////

void enterPlaying() {

    // reset the balloon to the center with no initial velocity
    this.hotBalloonX = this.gameCenterX;
    this.hotBalloonY = this.gameCenterY;
    this.hotBalloonVertVelocity = 0;
    // reset the walls
    this.walls.clear();
    // reset the score
    this.score = 0;

    // create the layer assets required by the game
    if (this.playBackground == null) {
        this.playBackground = this.createPlayBackground(this.gameWidth, this.gameHeight);
    }

    if (this.hotBalloon == null) {
        this.hotBalloon = this.createHotBalloon(this.hotBalloonSize);
    }

}

void runPlaying() {

    // reset the entire scene frame buffer
    // this is the common way in graphics programming
    background(0);

    imageMode(CORNER);
    image(this.playBackground, 0, 0);

    // the duration of 1 frame is roughly 1/60th of a second
    float timeIntervalFor1Frame = 1.0 / this.frameRate;

    // get the final velocity after acceleration
    float hotBalloonVertVelocityFinal = this.accelerateHotBalloonVert(
        this.hotBalloonWeight, 
        this.gravity, 
        this.hotBalloonVertVelocity,
        this.rotationalRps,
        this.rotationalDirection, 
        this.rotationRPSToForceFactor, 
        timeIntervalFor1Frame 
    );

    // decide whether the balloon is moving up or down
    // need to reverse the distance because origin is top-left in processing
    this.hotBalloonY = this.hotBalloonY - this.moveHotBalloon(
        this.hotBalloonVertVelocity, 
        hotBalloonVertVelocityFinal, 
        timeIntervalFor1Frame
    );

    // the final velocity becomes the initial velocity for the next frame
    this.hotBalloonVertVelocity = hotBalloonVertVelocityFinal;

    // bound the balloon by the ceiling and the floor
    this.hotBalloonY = this.boundByCeilingAndFloor(this.hotBalloonY, this.hotBalloon.height, this.gameHeight);

    // constant horizontal motion
    // the horizontal movement is done by the background, not the balloon
    int horiDistance = this.moveHotBalloon(
        this.hotBalloonHoriVelocity, 
        this.hotBalloonHoriVelocity, 
        timeIntervalFor1Frame 
    );

    // update the wall movement
    this.walls = this.wallsUpdate(this.walls, horiDistance);

    // repaint the balloon
    imageMode(CENTER);
    image(this.hotBalloon, this.hotBalloonX, this.hotBalloonY);

    // if 2, we hit a wall, if 1 we passed a wall, if 0 nothing happened
    int wallStatus = this.meetTheWalls(this.walls, this.hotBalloonX, this.hotBalloonY);
    if (wallStatus == 2) {
        this.game.transitionTo(this.gameOver);
    } else if (wallStatus == 1) {
        // increment score when we passed a wall
        this.score++;
    }

}

void exitPlaying() {
    // nothing to do here
}

///////////////////////////////
// Game Over State Functions //
///////////////////////////////

void enterOver() {

    background(0);
    // this screen changes each time, so its not kept statically
    PGraphics overScreen = this.createOverScreen(this.gameWidth, this.gameHeight, this.score);
    imageMode(CORNER);
    image(this.overScreen, 0, 0);

}

void runOver() {
    // nothing to do
}

void exitOver() {
    // nothing to do
}

//////////////////////
// Moving Functions //
//////////////////////

float accelerateHotBalloonVert(
    float weight, 
    float gravity, 
    float vertVelocity, 
    float rps, 
    int rpsDirection, 
    float rpsFactor
    float time
) {

    // if rpsDirection is 0, then this results in 0 acceleration
    float liftForce = rpsFactor * (rpsDirection * rps);

    // via F = M * A
    float liftAcceleration = liftForce / weight;

    // resolve against gravity
    float resultantAcceleration = gravity + liftAcceleration;

    // vf = vi + a * t
    float finalVelocity = vertVelocity + resultantAcceleration * time;

    return finalVelocity;

}

int moveHotBalloon(float initialVelocity, float finalVelocity, float time) {

    // d = ((vi + vf) / 2) * t
    int distance = round((initialVelocity + finalVelocity / 2.0) * time);
    return distance;

}

int boundByCeilingAndFloor(int objectPosition, int objectHeight, int boundingHeight) {

    float objectRadius = objectHeight / 2.0;
    position = round(min(objectPosition - objectRadius, 0.0) + objectRadius)
    position = round(max(objectPosition + objectRadius, boundingHeight) - objectRadius)
    return position;

}

///////////
// Walls //
///////////

ArrayList<int[]> wallsUpdate (ArrayList<int[]> walls, int distance) {

    // decide how to add new walls based on the distance

}

int meetTheWalls (ArrayList<int[]> walls, int positionX, int positionY) {

    // return 0, 1 or 2

}