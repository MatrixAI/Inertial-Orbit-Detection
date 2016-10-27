import java.util.Iterator;

float hotBalloonVertVelocity;
int hotBalloonX, hotBalloonY;
int score;

PGraphics startScreen;
PGraphics playBackground;
PGraphics hotBalloon;

int wallInterval;
int wallUnpassedIndex;
ArrayList<Wall> walls = new ArrayList<Wall>(); 

class Wall {

    PGraphics layer;
    int position;
    int width;
    int gapPosition;
    int gapHeight;

    Wall(PGraphics layer, int position, int width, int gapPosition, int gapHeight) {
        this.layer = layer;
        this.position = position;
        this.width = width;
        this.gapPosition = gapPosition;
        this.gapHeight = gapHeight;
    }

}

/**
 * Key Event Handler.
 * This is only applied at the start and over states.
 */
void keyPressed() { 

    State currentState = this.game.getCurrentState();

    if (currentState == this.gameStart) {
        this.game.transitionTo(this.gamePlaying);
    } else if (currentState == this.gameOver) {
        this.game.transitionTo(this.gameStart);
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
    this.wallUnpassedIndex = 0;
    this.wallInterval = 0;
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
        this.hotBalloonVertVelocity,
        this.rotationRps,
        this.rotationDirection, 
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
    // the horizontal movement is actually applied to the walls
    // since the balloon stays in the center of the screen horizontally
    int horiDistance = this.moveHotBalloon(
        this.hotBalloonHoriVelocity, 
        this.hotBalloonHoriVelocity, 
        timeIntervalFor1Frame 
    );

    // update the walls (add new ones and delete out of screen ones)
    this.wallsUpdate(this.walls, horiDistance);

    // repaint each wall
    for (Wall wall : this.walls) {
        imageMode(CORNER);
        image(wall.layer, wall.position, 0);
    }

    // repaint the balloon
    imageMode(CENTER);
    image(this.hotBalloon, this.hotBalloonX, this.hotBalloonY);

    // if 2, we hit a wall, if 1 we passed a wall, if 0 nothing happened
    int wallStatus = this.meetTheWalls(
        this.walls, 
        this.hotBalloonX, 
        this.hotBalloonY, 
        this.hotBalloon 
    );
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
    image(overScreen, 0, 0);

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
    float vertVelocity, 
    float rps, 
    int rpsDirection, 
    float time
) {

    // if rpsDirection is 0, then this results in 0 acceleration
    float liftForce = this.rotationRPSToForceFactor * (rpsDirection * rps);

    // via F = M * A
    float liftAcceleration = liftForce / this.hotBalloonWeight;

    // resolve against gravity
    float resultantAcceleration = this.gravity + liftAcceleration;

    // vf = vi + a * t
    float finalVelocity = vertVelocity + resultantAcceleration * time;

    return finalVelocity;

}

int moveHotBalloon(float initialVelocity, float finalVelocity, float time) {

    // d = ((vi + vf) / 2) * t
    int distance = round((initialVelocity + finalVelocity / 2.0) * time);
    return distance;

}

int boundByCeilingAndFloor(int objectY, int objectHeight, int boundingHeight) {

    int boundedY;
    int objectRadius = round(objectHeight / 2.0);
    
    // ceiling bound
    boundedY = max(objectY - objectRadius, 0) + objectRadius;
    // floor bound
    boundedY = min(objectY + objectRadius, boundingHeight) - objectRadius;

    return boundedY;

}

///////////
// Walls //
///////////

void wallsUpdate(ArrayList<Wall> walls, int distanceMoved) {

    if (walls.isEmpty()) {

        this.wallAdd(walls, this.gameWidth);
    
    } else {
        
        // iterate over all walls
        // delete the ones that are out of the window 
        // and shift the ones that are still in the window
        for (Iterator<Wall> iter = walls.iterator(); iter.hasNext();) {
            
            Wall wall = iter.next();
            int wallRightSide = wall.position + wall.width;
            
            if (wallRightSide - distanceMoved <= 0) {
                iter.remove();
                this.wallUnpassedIndex--;
            } else {
                wall.position = wall.position - distanceMoved;
            }

        }

        // add a new wall if the wall interval is satisfied by the shift of distanceMoved
        Wall lastWall = walls.get(walls.size() - 1);
        int lastWallRightSide = lastWall.position + lastWall.width;
        if (lastWallRightSide > this.wallInterval) {

            this.wallAdd(walls, lastWallRightSide + this.wallInterval);
            
            // generate a new wall interval
            this.wallInterval = round(random(
                this.wallMinIntervalFactor * this.gameWidth,
                this.wallMaxIntervalFactor * this.gameWidth
            ));

        }

    }

}

void wallAdd(ArrayList<Wall> walls, int newWallPosition) {

    int[] newWallParams = this.generateWallParameters();
    PGraphics newWallLayer = this.createWall(newWallParams[0], this.gameHeight, newWallParams[1], newWallParams[2]);
    
    walls.add(new Wall(
        newWallLayer, 
        newWallPosition, 
        newWallParams[0], // width
        newWallParams[1], // gap position
        newWallParams[2]  // gap height
    ));

}

int[] generateWallParameters() {

    int wallWidth = round(random(
        this.wallMinWidthFactor * this.gameWidth,
        this.wallMaxWidthFactor * this.gameWidth
    ));

    int gapHeight = round(random(
        this.wallMinGapFactor * this.gameHeight,
        this.wallMaxGapFactor * this.gameHeight
    ));

    // this position is the Y coordinate from where the gapStarts
    int gapPosition = round(random(0, this.gameHeight - gapHeight));

    return new int[] { wallWidth, gapPosition, gapHeight };

}

int meetTheWalls (ArrayList<Wall> walls, int hotBalloonX, int hotBalloonY, PGraphics hotBalloon) {

    // return 0, 1 or 2
    // if 2, we hit a wall, if 1 we passed a wall, if 0 nothing happened

    if (walls.isEmpty()) {
        return 0;
    }

    Wall wall = walls.get(this.wallUnpassedIndex);

    // there are 3 objects we care about when detecting collision here
    // the first object is the hotBalloon
    // the second object is the top half of wall
    // the third object is the bottom half of the wall
    // all 3 objects can be considered as rectangles
    // so we shall use the axis-aligned bounding box algorithm twice for each half of the wall
    
    // however note that this does not detect if 
    // the travel path of the hotBalloon intersects the travel path of the walls
    // this is because it's only detecting if there's an overlap in the bounding boxes of the objects
    // to detect intersection along a path, we would require a more sophisticated collision detection algorithm
    // http://gamedev.stackexchange.com/a/55991

    // find out the rounding mode of center-aligned odd widths in Processing Java
    int hotBalloonCornerX = hotBalloonX - round(hotBalloon.width / 2.0);
    int hotBalloonCenterY = hotBalloonY - round(hotBalloon.height / 2.0);
    int hotBalloonWidth = hotBalloon.width;
    int hotBalloonHeight = hotBalloon.height;

    int wallTopHalfX = wall.position;
    int wallTopHalfY = 0;
    int wallTopHalfWidth = wall.width;
    int wallTopHalfHeight = wall.gapPosition;

    int wallBottomHalfX = wall.position;
    int wallBottomHalfY = wall.gapPosition + wall.gapHeight;
    int wallBottomHalfWidth = wall.width;
    int wallBottomHalfHeight = wall.layer.height - wallBottomHalfY;

    if (
        hotBalloonCornerX < wallTopHalfX + wallTopHalfWidth &&  // the first left side has to be less than the second right side
        hotBalloonCornerX + hotBalloonWidth > wallTopHalfX &&   // the first right side has to be greater than the second left side
        hotBalloonCenterY > wallTopHalfY + wallTopHalfHeight && // the first top side has to be greater than the second bottom side
        hotBalloonCenterY + hotBalloonHeight < wallTopHalfY     // the first bottom side has to be less than the second top side
    ) {
    
        // collidied with top half
        this.wallUnpassedIndex++;
        return 2;

    }

    if (
        hotBalloonCornerX < wallBottomHalfX + wallBottomHalfWidth &&  // the first left side has to be less than the second right side
        hotBalloonCornerX + hotBalloonWidth > wallBottomHalfX &&      // the first right side has to be greater than the second left side
        hotBalloonCenterY > wallBottomHalfY + wallBottomHalfHeight && // the first top side has to be greater than the second bottom side
        hotBalloonCenterY + hotBalloonHeight < wallBottomHalfY        // the first bottom side has to be less than the second top side
    ) {
    
        // collided with bottom half
        this.wallUnpassedIndex++;
        return 2;

    }

    // if we didn't collide with the wall, did the pass the wall yet?
    // passing the wall simply means the hotBalloon left side is greater than the wall's right side
    if (
        hotBalloonCornerX > wall.position + wall.width
    ) {

        this.wallUnpassedIndex++;
        return 1;

    } else {

        // no passing, so nothing happens
        return 0;

    }

}