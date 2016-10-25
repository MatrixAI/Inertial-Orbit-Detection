/**
 * Create Start State Screen
 */
PGraphics createStartScreen(int width, int height) {

    int centerX = round(width / 2.0);
    int centerY = round(height / 2.0);
    PGraphics screen = createGraphics(width, height);
    screen.beginDraw();
    screen.background(251, 185, 1);
    screen.textAlign(CENTER);
    screen.text("Press any key to start", centerX, centerY);
    screen.endDraw();
    return screen;

}

/**
 * Create Play State Background
 */
PGraphics createPlayBackground(int width, int height) {

    int hillCenterX = round(width / 2.0);
    int hillCenterY = round(0.7 * height);
    int hillWidth = round(1.3 * width);
    int hillHeight = round(0.2 * height);

    int groundWidth = width;
    int groundHeight = round(0.26 * height);

    PGraphics background = createGraphics(width, height);

    background.beginDraw();

    // sky
    background.background(198, 226, 255);

    // hill
    background.fill(0, 139, 69);
    background.noStroke();
    background.ellipseMode(CENTER);
    background.ellipse(hillCenterX, hillCenterY, hillWidth, hillHeight);
    
    // ground
    background.fill(162, 205, 90);
    background.noStroke();
    background.rectMode(CORNER);    
    background.rect(0, background.height - groundHeight, groundWidth, groundHeight);
    
    background.endDraw();
    
    return background;

}


/**
 * Draw a hot balloon in to a PGraphics frame buffer layer.
 * The size parameter is the diameter of the balloon part of the hot air balloon.
 * All other dimensions will be sized proportionally to the size parameter.
 */
PGraphics createHotBalloon(int size) {

    int layerSize = 2 * size;
    int layerCenterX = round(layerSize / 2.0);
    int layerCenterY = round(layerSize / 2.0);

    int balloonSize = size;
    int balloonMarker1Width = round(0.8 * balloonSize);
    int balloonMarker1Height = balloonSize;
    int balloonMarker2Width = round(0.6 * balloonSize);
    int balloonMarker2Height = balloonSize;

    int rope1StartXOffset = -round(0.48 * balloonSize);
    int rope1StartYOffset = 0;
    int rope1EndXOffset = round(0.04 * balloonSize);
    int rope1EndYOffset = round(0.8 * balloonSize);
    
    int rope2StartXOffset = round(0.4 * balloonSize);
    int rope2StartYOffset = 0;
    int rope2EndXOffset = -round(0.08 * balloonSize);
    int rope2EndYOffset = round(0.8 * balloonSize);

    int basketXOffset = 0;
    int basketYOffset = round(0.8 * balloonSize);
    int basketSize = round(0.4 * balloonSize);
    int basketMarker1Width = round(0.32 * balloonSize);
    int basketMarker1Height = basketSize;
    int basketMarker2Width = round(0.24 * balloonSize);
    int basketMarker2Height = basketSize;
    
    PGraphics hotBalloon = createGraphics(layerSize, layerSize);
    
    hotBalloon.beginDraw();
    
    // ropes
    hotBalloon.strokeWeight(1);
    hotBalloon.stroke(94, 38, 18);
    hotBalloon.line(
        layerCenterX + rope1StartXOffset, layerCenterY + rope1StartYOffset, 
        layerCenterX + rope1EndXOffset,   layerCenterY + rope1EndYOffset
    );
    hotBalloon.line(
        layerCenterX + rope2StartXOffset, layerCenterY + rope2StartYOffset, 
        layerCenterX + rope2EndXOffset,   layerCenterY + rope2EndYOffset
    );

    // balloon
    hotBalloon.fill(255, 48, 48);
    hotBalloon.noStroke();
    hotBalloon.ellipseMode(CENTER);
    hotBalloon.ellipse(
        layerCenterX, layerCenterY, 
        balloonSize, balloonSize
    );
    
    hotBalloon.fill(255, 255, 255);
    hotBalloon.ellipseMode(CENTER);
    hotBalloon.ellipse(
        layerCenterX, layerCenterY, 
        balloonMarker1Width, balloonMarker1Height
    );
    
    hotBalloon.fill(255, 48, 48);
    hotBalloon.ellipseMode(CENTER);
    hotBalloon.ellipse(
        layerCenterX, layerCenterY, 
        balloonMarker2Width, balloonMarker2Height
    );

    // basket
    hotBalloon.fill(139, 125, 107);
    hotBalloon.rectMode(CENTER);
    hotBalloon.rect(
        layerCenterX + basketXOffset, layerCenterY + basketYOffset, 
        basketSize, basketSize
    );
    
    hotBalloon.fill(139, 69, 19);
    hotBalloon.rectMode(CENTER);
    hotBalloon.rect(
        layerCenterX + basketXOffset, layerCenterY + basketYOffset, 
        basketMarker1Width, basketMarker1Height
    );
    
    hotBalloon.fill(139, 125, 107);
    hotBalloon.rectMode(CENTER);
    hotBalloon.rect(
        layerCenterX + basketXOffset, layerCenterY + basketYOffset, 
        basketMarker2Width, basketMarker2Height
    );

    hotBalloon.endDraw();

    return hotBalloon;
    
}

/**
 * Draw a single wall. The width and height is the width and height of the entire wall including the gaps.
 * The gap position is the Y-position from the top to the beginningof the gap.
 * The gap height is the size of the gap opening.
 */
PGraphics createWall(int width, int height, int gapPosition, int gapHeight) {

    PGraphics wall = createGraphics(width, height);

    wall.beginDraw();
    wall.rectMode(CORNER);
    wall.strokeCap(ROUND);
    wall.fill(color(240, 248, 255));

    // top-half of the wall
    // includes bottom corner radius
    wall.rect(
        0, 
        0, 
        width, 
        gapPosition, 
        0, 0, 
        50, 50
    ); 

    // bottom-half of the wall
    // includes top corner radius
    wall.rect(
        0, 
        gapPosition + gapHeight, 
        width, 
        height, 
        50, 50, 
        0, 0
    );

    wall.endDraw();
    return wall;

}

/**
 * Create Over State Screen
 */
PGraphics createOverScreen(int width, int height, int score) {

    int centerX = round(width / 2.0);
    int centerY = round(height / 2.0);

    PGraphics screen = createGraphics(width, height);

    screen.beginDraw();

    screen.background(251, 185, 1);
    
    screen.fill(255);

    screen.textSize(12);
    screen.textAlign(CENTER);
    screen.text("Your Score:", centerX, centerY);
    
    screen.textSize(130);
    screen.textAlign(CENTER);
    screen.text(score, centerX, centerY + 120);
    
    screen.textSize(15);
    screen.text("Press any key to restart", centerX, centerY + 140);

    screen.endDraw();
    
    return screen;

}