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

    int balloonSize = size;
    int balloonYOffset = round(balloonSize / 2.0);
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
    
    int layerWidth = balloonSize;
    int layerHeight = round(1.45 * balloonSize);

    int layerCenterX = round(layerWidth / 2.0);
    int layerCenterY = round(layerHeight / 2.0);

    PGraphics hotBalloon = createGraphics(layerWidth, layerHeight);
    
    hotBalloon.beginDraw();
    
    // ropes
    hotBalloon.strokeWeight(1);
    hotBalloon.stroke(94, 38, 18);
    hotBalloon.line(
        layerCenterX + rope1StartXOffset, balloonYOffset + rope1StartYOffset, 
        layerCenterX + rope1EndXOffset,   balloonYOffset + rope1EndYOffset
    );
    hotBalloon.line(
        layerCenterX + rope2StartXOffset, balloonYOffset + rope2StartYOffset, 
        layerCenterX + rope2EndXOffset,   balloonYOffset + rope2EndYOffset
    );

    // balloon
    hotBalloon.fill(255, 48, 48);
    hotBalloon.noStroke();
    hotBalloon.ellipseMode(CENTER);
    hotBalloon.ellipse(
        layerCenterX, balloonYOffset, 
        balloonSize, balloonSize
    );
    
    hotBalloon.fill(255, 255, 255);
    hotBalloon.ellipseMode(CENTER);
    hotBalloon.ellipse(
        layerCenterX, balloonYOffset, 
        balloonMarker1Width, balloonMarker1Height
    );
    
    hotBalloon.fill(255, 48, 48);
    hotBalloon.ellipseMode(CENTER);
    hotBalloon.ellipse(
        layerCenterX, balloonYOffset, 
        balloonMarker2Width, balloonMarker2Height
    );

    // basket
    hotBalloon.fill(139, 125, 107);
    hotBalloon.rectMode(CENTER);
    hotBalloon.rect(
        layerCenterX + basketXOffset, balloonYOffset + basketYOffset, 
        basketSize, basketSize
    );
    
    hotBalloon.fill(139, 69, 19);
    hotBalloon.rectMode(CENTER);
    hotBalloon.rect(
        layerCenterX + basketXOffset, balloonYOffset + basketYOffset, 
        basketMarker1Width, basketMarker1Height
    );
    
    hotBalloon.fill(139, 125, 107);
    hotBalloon.rectMode(CENTER);
    hotBalloon.rect(
        layerCenterX + basketXOffset, balloonYOffset + basketYOffset, 
        basketMarker2Width, basketMarker2Height
    );

    hotBalloon.endDraw();

    return hotBalloon;
    
}

/**
 * Draw a single wall. The width and height is the width and height of the entire wall including the gaps.
 * The gap position is the Y-position from the top to the beginning of the gap.
 * The gap height is the size of the gap opening.
 */
PGraphics createWall(int width, int height, int gapPosition, int gapHeight) {

    int strokeWidth = 1;

    PGraphics wall = createGraphics(width + 2 * strokeWidth, height);

    wall.beginDraw();
    wall.rectMode(CORNER);

    wall.stroke(95, 95, 95, 80);
    wall.strokeWeight(strokeWidth);
    wall.fill(color(236, 236, 236));

    // top-half of the wall
    // includes bottom corner radius
    // we don't want to show the top stroke
    wall.rect(
        0, 
        0 - strokeWidth, 
        width, 
        gapPosition, 
        0, 0, 
        0.2 * width, 0.2 * width
    ); 

    // bottom-half of the wall
    // includes top corner radius
    // we don't want to show the bottom stroke
    wall.rect(
        0, 
        gapPosition + gapHeight + strokeWidth, 
        width, 
        height - (gapPosition + gapHeight), 
        0.2 * width, 0.2 * width, 
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
    screen.text("Your Score:", centerX, centerY - 30);
    
    screen.textSize(50);
    screen.textAlign(CENTER);
    screen.text(score, centerX, centerY + 20);
    
    screen.textSize(15);
    screen.text("Press any key to restart", centerX, centerY + 50);

    screen.endDraw();
    
    return screen;

}