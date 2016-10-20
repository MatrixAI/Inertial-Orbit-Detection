float balloonVertVelocity;
int   balloonX, balloonY;
int   score;

////////////////////////////////
// Game Start State Functions //
////////////////////////////////

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

//////////////////////////////////
// Game Playing State Functions //
//////////////////////////////////

void enterPlaying() {

    this.balloonX = this.gameCenterX;
    this.balloonY = this.gameCenterY;
    this.balloonVertVelocity = 0;

}

void runPlaying() {

}

void exitPlaying() {

}

///////////////////////////////
// Game Over State Functions //
///////////////////////////////

void enterOver() {

    background(251, 185, 1);
    textAlign(CENTER);
    fill(255);
    
    textSize(12);
    text("Your Score", this.gameCenterX, this.gameCenterY - 120);
    
    textSize(130);
    text(score, this.gameCenterX, this.gameCenterY);
    
    textSize(15);
    text("Press any key to restart", this.gameCenterX, this.gameHeight - 30);

}

void runOver() {

}

void exitOver() {

    this.walls.clear();
    this.score = 0;
    this.balloonVertVelocity = 0;

}