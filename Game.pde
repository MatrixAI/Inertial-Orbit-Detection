// VARIABLES

// client network
import processing.net.*;
Client c; 
int orbitDirection;
float orbitRPS;
float orbitRPSScalingFactor = 0.6;

// There are three game screens
// 0: Initial Screen
// 1: Game Screen
// 2: Game-over Screen

int gameScreen = 0; 

// the hot air balloon
int balloonX, balloonY; 
int balloonSize = 25;
int basketSize = 25;

// gravity
float gravity = 1; 
float balloonVertVelocity = 0; 

// horizontal movement
float balloonHoriVelocity = 1; 
float airfriction = 0.0001;

// walls
int wallSpeed = 3; 
int wallInterval = 1600;
float lastAddTime = 0;
int minGapHeight = 250;
int maxGapHeight = 300;
int wallWidth = 80;
color wallColors = color(240, 248, 255);
// This arraylist stores data of the gaps between the walls
// Actual walls are drawn accordingly
// [gapWallX, gapWallY, gapWallWidth, gapWallHeight]
ArrayList<int[]> walls = new ArrayList<int[]>(); 

// score
int score = 0;

// SETUP BLOCK

void setup() { 
    // This sets up the game screen
    size(500, 500); 
    balloonX = width/4;
    balloonY = height/5;
    // Connect to the server's IP address and port
    // server IP is 127.0.0.1 and port is 8888
    c = new Client(this, "127.0.0.1", 8888); 
} 

// DRAW BLOCK

// This is the draw loop
void draw() { 
    // Display the contents of the current screen
    if (gameScreen == 0) {
        drawInitScreen(); 
    } else if (gameScreen == 1) { 
        drawGameScreen(); 
    } else if (gameScreen == 2) { 
        drawGameOverScreen();
    } 
} 

// SCREEN CONTENTS

void drawInitScreen() { 
    background(251, 185, 1); 
    textAlign(CENTER); 
    text("Press any key to start", height/2, width/2);
}

void drawGameScreen() { 
    readFromOrbitDetectionServer();
    liftBalloon();
    drawBackground();
    drawballoon();
    applyGravity();
    applyHorizontalSpeed(); 
    wallAdder(); 
    wallHandler(); 
}  

void drawGameOverScreen() { 
    background(251, 185, 1);
    textAlign(CENTER);
    fill(255);
    textSize(12);
    text("Your Score", width/2, height/2 - 120);
    textSize(130);
    text(score, width/2, height/2);
    textSize(15);
    text("Press any key to restart", width/2, height-30);
}

// INPUTS

void keyPressed() { 
    // if we are on the initial screen when clicked, start the game
    if (gameScreen == 0) { 
        gameScreen = 1;
    } else if (gameScreen == 1) { 
        // liftBalloon();
    } else if (gameScreen == 2) { 
        restart();
    }
}

// OTHER FUNCTIONS

void applyGravity() { 
    // balloonVertVelocity += gravity; 
    // balloonY += balloonVertVelocity; 
    balloonY += gravity;
}

void drawBackground() {
  background(187, 255, 255);
  fill(255);
  noStroke();
  ellipse(width/2, height-150, width+150, 100);
  fill(162, 205, 90);
  noStroke();
  rectMode(CORNER);
  rect(0, height-130, width, height);
  noStroke(); 
  fill(162, 205, 90);
}

void drawballoon() {
    // ropes
    strokeWeight(1);
    stroke(94, 38, 18);
    line(balloonX-12,balloonY,balloonX+1,balloonY+20);
    line(balloonX+10,balloonY,balloonX-2,balloonY+20);
    // balloon
    fill(255, 48, 48);
    noStroke();
    ellipseMode(CENTER);
    ellipse(balloonX, balloonY, balloonSize, balloonSize);
    fill(255, 255, 255);
    ellipseMode(CENTER);
    ellipse(balloonX, balloonY, balloonSize-5, balloonSize);
    fill(255, 48, 48);
    ellipseMode(CENTER);
    ellipse(balloonX, balloonY, balloonSize-10, balloonSize);
    // basket
    fill(139, 125, 107);
    rectMode(CENTER);
    rect(balloonX, balloonY+20, basketSize-15, basketSize-15);
    fill(139, 69, 19);
    rectMode(CENTER);
    rect(balloonX, balloonY+20, basketSize-17, basketSize-15);
    fill(139, 125, 107);
    rectMode(CENTER);
    rect(balloonX, balloonY+20, basketSize-19, basketSize-15);
}

void liftBalloon() { 
    float lift = orbitDirection * (orbitRPS * orbitRPSScalingFactor);
    // balloonVertVelocity -= lift; 
    // balloonY += balloonVertVelocity;
    balloonY -= lift;
}

void readFromOrbitDetectionServer() { 
  byte newline = 10;
  if (c.available() > 0) { 
    String directionAndRPS = c.readStringUntil(newline);
    // split values into an array
    String[] splittedDirectionAndRPS = split(directionAndRPS, ':'); 
    orbitDirection = int(splittedDirectionAndRPS[0]);
    orbitRPS = float(splittedDirectionAndRPS[1]);
    c = new Client(this, "127.0.0.1", 8888);
  }
}

void applyHorizontalSpeed() { 
    balloonX += balloonHoriVelocity;
    balloonHoriVelocity -= (balloonHoriVelocity * airfriction);
}

void wallAdder() { 
    if (millis() - lastAddTime > wallInterval) { 
        int randHeight = round(random(minGapHeight, maxGapHeight)); 
        int randY = round(random(0, height - randHeight));
        // {gapWallX, gapWallY, gapWallWidth, gapWallHeight, scoreCheck}
        int[] randWall = {width, randY, wallWidth, randHeight, 0};
        walls.add(randWall); 
        lastAddTime = millis();
    }
}

void wallHandler() { 
    for (int i = 0; i < walls.size(); i++) { 
        wallRemover(i); 
        wallMover(i);
        wallDrawer(i); 
        watchWallCollision(i);
    }
}

void wallDrawer(int index) { 
    int[] wall = walls.get(index); 
    // get gap wall settings
    int gapWallX = wall[0];
    int gapWallY = wall[1]; 
    int gapWallWidth = wall[2]; 
    int gapWallHeight = wall[3];
    // draw actual walls
    rectMode(CORNER);
    strokeCap(ROUND);
    fill(wallColors);
    rect(gapWallX, 0, gapWallWidth, gapWallY, 0, 0, 50, 50); 
    rect(gapWallX, gapWallY+gapWallHeight, gapWallWidth, height-(gapWallY + gapWallHeight), 50, 50, 0, 0);
}

void wallMover(int index) {
    int[] wall = walls.get(index); 
    wall[0] -= wallSpeed; 
}

void wallRemover(int index) { 
    int[] wall = walls.get(index); 
    if (wall[0] + wall[2] <= 0) { 
        walls.remove(index);
    }
}

void watchWallCollision(int index) { 
    int[] wall = walls.get(index); 
    // get gap wall settings
    int gapWallX = wall[0];
    int gapWallY = wall[1];
    int gapWallWidth = wall[2];
    int gapWallHeight = wall[3];
    int wallScored = wall[4];
    int wallTopX = gapWallX;
    int wallTopY = 0;
    int wallTopWidth = gapWallWidth;
    int wallTopHeight = gapWallY;
    int wallBottomX = gapWallX; 
    int wallBottomY = gapWallY + gapWallHeight; 
    int wallBottomWidth = gapWallWidth;
    int wallBottomHeight = height - (gapWallY + gapWallHeight);

    if (
        (balloonX + (balloonSize/2) > wallTopX) &&
        (balloonX - (balloonSize/2) < wallTopX + wallTopWidth) &&
        (balloonY + (balloonSize/2) > wallTopY) && 
        (balloonY - (balloonSize/2) < wallTopY + wallTopHeight) 
    ) { 
        gameScreen = 2;
    }

    if (
        (balloonX + (balloonSize/2) > wallBottomX) &&
        (balloonX - (balloonSize/2) < wallBottomX + wallBottomWidth) && 
        (balloonY + (balloonSize/2) > wallBottomY) && 
        (balloonY - (balloonSize/2) < wallBottomY + wallBottomHeight)
        ) { 
            gameScreen = 2;
    }

    if (balloonY < 0) { 
        gameScreen = 2;
    }

    if (balloonY > height) { 
        gameScreen = 2;
    }

    if (balloonX > gapWallX + (gapWallWidth/2) && wallScored==0) { 
        wallScored = 1;
        wall[4] = 1;
        score();
    }
} 

void score() { 
    score++;
}

void restart() { 
    score = 0;
    balloonX = width/4;
    balloonY = height/5;
    lastAddTime = 0; 
    walls.clear();
    gameScreen = 0;
    balloonVertVelocity = 0;
    balloonHoriVelocity = 0;
}